# Destructive production database deletion

The GitHub Actions workflow creates a disposable S3 bucket in LocalStack, then
generates an actual Terraform deletion plan by changing `create_bucket` to
`false`. It must be blocked regardless of Jev’s output: this is the deterministic
production safety rule.

```sh
python3 scripts/review.py --plan demo-plans/destructive-production-delete/plan.json --environment production --offline
```

Expected result: `block` with exit status 1. The checked-in `plan.json` is an
illustrative artifact; CI reviews its freshly generated `tfplan.json` instead.
Nothing connects to AWS: the resource exists only inside the ephemeral LocalStack
service container.
