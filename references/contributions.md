# Contributions: approved base, bounded scope and execution evidence

Use this for external contributions and multi-repository PR assessment. It extends, not
replaces, the operational reading procedure. No branch-local CHG, PR body or uploaded
JSON authenticates its own authority.

## Two explicit profiles

- **legacy** remains the default of `validate.py`: existing checks, severities and
  `no-chg` handling are unchanged. Its output explicitly says authority is not verified.
- **strict-contribution** is opt-in through CLI, never selected by a proposed
  `framework.yaml`. It reads Git objects at full commit IDs, not working-tree files.
  It verifies a separate CI-controlled input; missing history, access, policy or evidence
  fails closed. It does not execute code, install providers, fetch or merge anything.

```bash
python3 -I -B /path/to/framework/skills/audit/scripts/validate.py \
  --profile strict-contribution --trust-input /trusted/run/input.json \
  --pr-text-file /untrusted/pr-body.txt --json
```

Strict mode always emits JSON. Exit 0 is a passed **bounded mechanical gate**, 1 a failed
gate and 2 an invalid invocation/input. It rejects index writes and a caller's changed-file
list: paths are recomputed from Git objects, retaining deletions, mode changes and both
sides of a rename. Links/submodules needing observation fail instead of being followed.
It is not a complete documentary audit: keep the ordinary validator and semantic review.

## The trust boundary belongs to the CI controller

`schemas/memory/contribution-input.v1.json` is the input contract. The controller, not
the contribution, constructs these fields:

| Input | What the controller must establish |
|---|---|
| `framework_commit` | Full pinned commit of a clean, trusted framework runtime; dependencies installed in an isolated environment |
| `author` | Contribution author's authenticated hosting identity; a no-chg reviewer must be a different person |
| `documents.repository/root` | Stable remote identity and the matching authorized local Git object store |
| `documents.approved_tip` | Actual tip of an allowed protected/reviewed branch, read from the hosting service |
| `documents.commit` | Requested mandate commit, available and ancestral to that approved tip |
| `documents.proposed` | Exact documentary revision under review, or the same mandate commit when documents are unchanged |
| `repositories` | Logical repository IDs, independently authenticated remote identities, local stores and exact base/head commits |
| `receipts` | Paths, canonical digests, producer and run IDs after authenticating the producer, run and downloaded artifact |
| `exception_review` | Only after independent review of the exact no-chg request; never copied from a PR |

A file being outside a checkout, a SHA matching a JSON file, or a field saying
`trusted: true` is not authentication. These inputs are a **trusted caller API**, not a
new signing service. The verifier checks consistency against the supplied trust anchors;
it cannot independently establish a hosting identity from a local filesystem path.
An untrusted workflow can forge a whole input: its output must never be a required
authoritative check. Use an approved workflow/pin and protected review rules.

There is no automatic fallback to the documentary repository's latest main. Missing
cross-repository access is an unavailable gate, not a successful partial approval. Never
give fork code documentary credentials, shared privileged caches or a wider documentary
scope than its mandate names.
Classifications/exclusions restrict selected documentary evidence; they are not an ACL.

## The approved policy

Copy/adapt `ci/contribution-policy.example.json` to
`.framework/contribution-policy.json` in the documentary repository, then review and
commit it **before** the implementation it governs. The strict profile reads the policy
from the mandate commit and checks that it still agrees with the approved tip. A policy
introduced or broadened only by a PR cannot authorize that PR.

The policy binds existing CHG paths to machine-readable path prefixes, required repository
sets, specifically affected artifacts and mandatory test IDs. These are operational
selectors that the prose cannot supply deterministically, not copies of What changes,
Preservation or Acceptance. CHG/ICG/DEC remain authoritative for meaning and classification.
The policy cannot create a mandate, approve a draft or remove its three required sections.
Missing bindings require curation; the engine does not invent them from filenames or graphs.

Each binding contains:

- `repositories`: every code repository to include in the assessed/tested set, including
  declared unchanged consumers when the mandate needs them.
- `paths`: exact relative file/directory prefixes per repository ID; `documents` denotes
  the documentary repository. No globs, absolute paths, parent traversal or empty root.
  Files other than Markdown/YAML or the policy JSON need a matching explicit code-repository
  observation of the same base/head; co-located code is not silently treated as documentation.
  This conservative file filter is not semantic classification of YAML or embedded code.
- `obligations`: impact plus exact authoritative artifact path. Data impact needs the
  affected DC and an increasing semantic version; an unrelated DC cannot substitute.
  Architecture/risk need their specifically bound ARC/RSK. Consumer notification and
  semantic correctness still need evidence and review.
- `tests`: mandatory test IDs. Command arrays and allowed producer IDs have one home in
  the policy's test catalog. Their commands are **compared**, not executed by the verifier.

Classifications come from the accepted ICG in the trusted base, joined through qualified
candidate identity. Architecture requires a cited accepted DEC there. No AI EVR is demanded
prematurely at the PR that builds the feature: evaluation/release obligations retain their
existing lifecycle. Nothing in this phase certifies deployed versions.

The complete immutable body and normative metadata are compared, including prose outside
section markers. Existing status/CHG closure metadata can change without rewriting the
mandate; status regression, rollback or revoked current approval cannot authorize work.
The policy and rules must remain consistent with the approved tip; linked mandates and
classifications are rechecked there. A superseding document is not an edit of history.

## Receipts and fast-cycle versus mandatory tests

`schemas/memory/execution-receipt.v1.json` carries producer/run/test, command array,
documentary repository+commit, canonical policy hash, **the whole exact code set**, result
and exit code. The controller authenticates its source and supplies a separate witness
digest; `sha256(canonical_JSON)` is integrity, never the signature of a test execution.

Run test code only in a separate unprivileged, disposable job, against the exact declared
checkouts. Verify checkout cleanliness/contents and environment before execution; bind
the producer identity to a trusted orchestration definition, not a PR-defined test wrapper.
Collect the result after execution, including nonzero exit codes. Authenticate artifact
origin and run/head identity before forwarding a witness. Do not execute commands taken
from a downloaded receipt or retrieved document.

A receipt for an earlier commit, a missing consumer, another command, policy or documentary
base cannot attest the new set. Missing, failed, duplicate and unverified receipts block.
`selected_tests` lists optional fast-cycle choices; it cannot subtract from the union of
mandatory tests for all cited mandates. A graph can add suggestions, not cancel acceptance.
No wall-clock age is used as a substitute for version identity or producer authentication.

`no-chg: <reason>` remains possible. In strict mode, the controller supplies an approved
reviewer and `request_hash = sha256(canonical_JSON({document, proposed, code_set, reason}))`
after reviewing exactly that request. Reviewers come from the approved policy.
The reviewer must differ from the authenticated contribution author, case-insensitively.
Changed reason/head/base invalidates the review. Exception tests remain mandatory; a code
exception cannot pass with an empty test binding. Ordinary human merge review is still due.

## GitHub adoption and limits of the supplied assets

`ci/pull-request.yml` remains a low-permission **legacy** asset, now passing base/head
through quoted environment variables as well as PR text. No `pull_request_target` or
privileged execution of proposed code is added.

`ci/contribution.yml` is an optional, manually dispatched **documentary-PR** example,
running from the repository's default branch. Its controller checks the PR's base identity,
default/protected branch and exact commits via GitHub, fetches objects without checking out
the PR, and invokes the clean pinned runtime. It never fabricates receipts: mandates
requiring code repositories/tests remain blocked until a trusted integration supplies them.
It is not an automatic required PR check and does not configure protections.

For multi-repository code CI, reuse the same verifier/input contract with the organization's
authenticated object/receipt collector. This host-specific collector is an adoption
integration, not a generic untrusted-artifact download step. Protect its inputs and source,
require it on the exact head/merge candidate being merged and rerun after any set changes.
The framework cannot configure those remotes or authenticate private CI runs by assumption.

Adopt `ci/CODEOWNERS.example` only after replacing the team. Require code-owner review for
workflow, framework pin, policy and mandate changes; require review of the latest push,
restrict bypass rights and keep test jobs without secrets/write permissions. CODEOWNERS
alone does not enforce review.

GitHub's [secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use)
supports environment-variable handling, least privilege, immutable action pins and
separation from untrusted execution. Its [CODEOWNERS documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
explains how required approval depends on repository protection configuration.
The supplied workflow is locally tested with synthetic API/Git inputs; a live remote run
and protections must be verified when a project adopts it.
