# CI assets

Files a project copies into its own repository. None is an artifact: nothing here
carries front matter, nothing here is validated, and this directory exists so that
`templates/` keeps meaning "one file per artifact type" and nothing else.

| File | Copy to | What it does |
|---|---|---|
| `PULL_REQUEST_TEMPLATE.md` | `.github/PULL_REQUEST_TEMPLATE.md` | asks for the `CHG` the change set implements |
| `pull-request.yml` | `.github/workflows/pull-request.yml` | runs the validator with the pull request context, which is what `PR001`–`PR004` need |
| `branches.yml` | `.github/workflows/branches.yml` | instead of `pull-request.yml`, for documentation written on branches (`.framework/work.yaml`): on each pull request `BR001`–`BR003` against the main line, the generated views and the pull request context; on each push to the main line, an issue for a commit that arrived outside a pull request, a merge that produced text neither side had, or a decision closing an entry already closed. It blocks nothing: on a plan without branch protection it makes these visible within minutes |

In `pull-request.yml` and `branches.yml` the project and the framework are checked out side by side, in `docs/` and `framework-data-ai/`, as they sit on a person's machine (`contribution.yml` reads Git objects and keeps its own layout): inside the project the validator would read the framework's own files as the project's, and inside `.framework/` the checkout would empty the project's folder of that name. Every checkout in these workflows fetches the full history, and it is not a preference: the validator reads the commit behind every attested `last_review` and stops, with exit 2, in a clone that lacks it. `tests/selfcheck.py` asserts the setting on every checkout step in this directory.

The checks themselves live in `skills/audit/checks.yaml` like every other one, and a
project turns one down or off in its own `framework.yaml` the same way:

```yaml
checks:
  PR004: off        # we have no data contracts yet
```

What they cannot check is in the template on purpose: whether the change set stayed inside
what the contract said must not change. That is the review, and it is the reason field 2 of
a `CHG` exists.
