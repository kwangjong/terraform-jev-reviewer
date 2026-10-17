# Safe staging change

Expected reviewer outcome: `pass` or `require_review` if Jev is not configured.

```sh
python3 scripts/review.py --plan demo-plans/safe-staging-change/plan.json --environment staging --offline
```

`main.tf` is provider-free and can regenerate this plan with Terraform 1.4+.
