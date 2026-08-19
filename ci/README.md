# CI assets

Two files a project copies into its own repository. Neither is an artifact: nothing here
carries front matter, nothing here is validated, and this directory exists so that
`templates/` keeps meaning "one file per artifact type" and nothing else.

| File | Copy to | What it does |
|---|---|---|
| `PULL_REQUEST_TEMPLATE.md` | `.github/PULL_REQUEST_TEMPLATE.md` | asks for the `CHG` the change set implements |
| `pull-request.yml` | `.github/workflows/pull-request.yml` | runs the validator with the pull request context, which is what `PR001`–`PR004` need |

The checks themselves live in `skills/audit/checks.yaml` like every other one, and a
project turns one down or off in its own `framework.yaml` the same way:

```yaml
checks:
  PR004: off        # we have no data contracts yet
```

What they cannot check is in the template on purpose: whether the change set stayed inside
what the contract said must not change. That is the review, and it is the reason field 2 of
a `CHG` exists.
