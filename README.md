# Terraform + Jev reviewer

A PR gate that reads `terraform show -json` output, extracts a secret-safe summary,
and asks Jev for a typed review route. Deterministic policy always wins: this tool
never applies Terraform, and a destructive production change is blocked before any
model output is considered.

## Quick start

```sh
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
export JEV_API_KEY='...'
python3 scripts/review.py --plan tfplan.json --environment staging
```

The output is JSON with `pass`, `require_review`, or `block`. A block exits `1`; a
review requirement exits `0` so that GitHub Environment protection or a required
review job can enforce the approval. If your repository wants review to fail CI,
change the last return in `scripts/review.py` to fail on `require_review` too.

For a local policy-only demonstration (no key or network call):

```sh
python3 scripts/review.py --plan tests/fixtures/destructive-prod.json --environment production --offline
```

## GitHub Actions setup

1. Copy `.github/workflows/terraform-review.yml` to the Terraform repository.
2. Copy `scripts/review.py` there too.
3. Add `JEV_API_KEY` as an Actions secret. Do not put it in `.tfvars` or commit it.
4. Set the repository/environment variable `TF_ENVIRONMENT` to `staging` or
   `production`. Protect the production Environment with required reviewers.
5. Tune `SENSITIVE_TYPES`, `JEV_MIN_CONFIDENCE` (default `0.85`), and the
   destructive-production policy to match your change-management rules.

Only resource addresses, types, and actions are sent to Jev—not `before`/`after`
attribute values from the plan, which can contain sensitive data. Jev is used for
routing; OPA/Conftest, Terraform policy sets, IAM rules, protected branches, and
environment approvals should remain authoritative controls.
