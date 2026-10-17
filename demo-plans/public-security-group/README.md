# Public security-group demo

This intentionally exposes HTTPS to the internet. It is a plan-review sample;
never apply it. The reviewer recognizes `aws_security_group` as sensitive, so it
requires a human review even when Jev is confident.

```sh
python3 scripts/review.py --plan demo-plans/public-security-group/plan.json --environment staging --offline
```

The PR workflow starts LocalStack, generates a fresh plan from `main.tf`, and
reviews that output. The literal AWS credentials are inert placeholders for the
local AWS emulator only, and must never be replaced by real credentials in source
control.
