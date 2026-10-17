# Destructive production database deletion

This plan artifact represents Terraform detecting that the stateful primary RDS
instance was removed from configuration. It must be blocked regardless of Jev’s
output: this is the deterministic production safety rule.

```sh
python3 scripts/review.py --plan demo-plans/destructive-production-delete/plan.json --environment production --offline
```

Expected result: `block` with exit status 1. `previous-configuration.tf` is
documentation only; its password is deliberately fake and this directory must
never be applied.
