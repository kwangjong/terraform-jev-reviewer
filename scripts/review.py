#!/usr/bin/env python3
"""Review a Terraform plan with deterministic policy checks and Jev routing.

This program never runs `terraform apply`.  It emits a JSON report and returns
non-zero only when the resulting policy decision is `block`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

MODEL = os.getenv("JEV_MODEL", "jev-latest")
ENDPOINT = os.getenv("JEV_ENDPOINT", "https://api.typesafe.ai/v1/systemone")
MIN_CONFIDENCE = float(os.getenv("JEV_MIN_CONFIDENCE", "0.85"))

DESTRUCTIVE_ACTIONS = {"delete", "replace"}
SENSITIVE_TYPES = {
    "aws_iam_policy", "aws_iam_role", "aws_iam_role_policy",
    "aws_iam_role_policy_attachment", "aws_security_group",
    "aws_security_group_rule", "aws_kms_key", "aws_db_instance",
    "aws_s3_bucket_policy", "google_project_iam_member",
    "azurerm_role_assignment",
}


def load_plan(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Cannot read Terraform JSON plan: {exc}") from exc
    if not isinstance(data.get("resource_changes"), list):
        raise SystemExit("Expected output from: terraform show -json tfplan")
    return data


def summarize(plan: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    resources: list[dict[str, Any]] = []
    flags: list[str] = []
    action_counts: Counter[str] = Counter()
    type_counts: Counter[str] = Counter()
    for change in plan["resource_changes"]:
        actions = change.get("change", {}).get("actions", [])
        if actions == ["no-op"]:
            continue
        action = "replace" if set(actions) == {"create", "delete"} else "+".join(actions)
        resource_type = change.get("type", "unknown")
        action_counts[action] += 1
        type_counts[resource_type] += 1
        record = {"address": change.get("address"), "type": resource_type, "action": action}
        resources.append(record)
        if action in DESTRUCTIVE_ACTIONS:
            flags.append(f"destructive change: {record['address']} ({action})")
        if resource_type in SENSITIVE_TYPES:
            flags.append(f"sensitive resource: {record['address']} ({resource_type})")
    return {
        "terraform_version": plan.get("terraform_version"),
        "change_count": len(resources),
        "actions": dict(sorted(action_counts.items())),
        "resource_types": dict(sorted(type_counts.items())),
        # Keep request payload bounded and do not send planned attribute values,
        # which may contain secrets.
        "resources": resources[:200],
    }, flags


def jev_request(state: dict[str, Any], api_key: str) -> dict[str, Any]:
    payload = {
        "model": MODEL,
        "state": state,
        "questions": {
            "review_route": {
                "type": "choice",
                "instructions": "Choose the required review route for this Terraform plan. "
                                "Prefer human review whenever the change could affect production availability, "
                                "data durability, network exposure, or access control.",
                "criteria": {
                    "auto_approve": "Small, reversible, non-production change with no security or data impact.",
                    "platform_review": "Needs platform/SRE review before merge or apply.",
                    "security_review": "Changes access control, secrets, encryption, or network exposure.",
                    "block": "Unsafe change or insufficient context; do not merge or apply."
                },
            },
            "human_review_required": {
                "type": "noul",
                "instructions": "Does this Terraform plan require a human reviewer before it can be merged?"
            },
        },
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Jev request failed: {exc}") from exc


def answer(response: dict[str, Any], question: str) -> dict[str, Any]:
    # Public examples show both a top-level question map and an `answers` map.
    return response.get("answers", response).get(question, {})


def decide(environment: str, flags: list[str], jev: dict[str, Any] | None) -> tuple[str, list[str]]:
    reasons = list(flags)
    destructive = any(item.startswith("destructive") for item in flags)
    sensitive = any(item.startswith("sensitive") for item in flags)
    if environment == "production" and destructive:
        return "block", reasons + ["policy: destructive production change is blocked"]
    if jev is None:
        return "require_review", reasons + ["Jev unavailable: fail closed to human review"]
    route = answer(jev, "review_route")
    selected = route.get("choice")
    confidence = route.get("confidence", 0)
    human_probability = answer(jev, "human_review_required").get("noul", 1)
    if selected == "block":
        return "block", reasons + ["Jev recommends block"]
    if sensitive or confidence < MIN_CONFIDENCE or human_probability >= 0.5:
        return "require_review", reasons + ["policy: sensitive or uncertain decision requires review"]
    if selected == "auto_approve":
        return "pass", reasons + ["Jev classifies plan as low risk"]
    return "require_review", reasons + [f"Jev route: {selected or 'unknown'}"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path, help="terraform show -json output")
    parser.add_argument("--environment", default=os.getenv("TF_ENVIRONMENT", "unknown"))
    parser.add_argument("--offline", action="store_true", help="Skip Jev; useful for tests and local inspection")
    args = parser.parse_args()
    summary, flags = summarize(load_plan(args.plan))
    state = {"environment": args.environment, "plan": summary, "deterministic_flags": flags}
    jev = None
    error = None
    if not args.offline:
        api_key = os.getenv("JEV_API_KEY")
        if not api_key:
            error = "JEV_API_KEY is not set"
        else:
            try:
                jev = jev_request(state, api_key)
            except RuntimeError as exc:
                error = str(exc)
    decision, reasons = decide(args.environment, flags, jev)
    report = {"decision": decision, "reasons": reasons, "summary": summary, "jev": jev, "jev_error": error}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if decision == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())
