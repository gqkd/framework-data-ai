# Release sets and independently witnessed delivery

Read this when preparing or assessing a multi-repository release, or deciding whether an
included CHG can progress to implemented/verified. This extends the release skill's frozen
EVP/metric/slice checks; it does not replace them or grant merge/deployment authority.

## One immutable candidate, three separate facts

| State being assessed | Evidence required by strict-release |
|---|---|
| `prepared` | Coherent RLM/REL/EVR, exact frozen EVP, authenticated pre-release and integration receipts |
| `implemented` | Prepared evidence plus every candidate/dependency code commit present in its authenticated default-branch history |
| `verified` | Implemented evidence plus an authenticated observation of the whole deployed set in the intended environment, with a passed smoke run |

A new manifest is a prepared description, never a deployment observation. No command in
this guide merges, deploys, updates a CHG or regenerates a historical immutable artifact.
The default branch comes from the hosting controller: do not assume its name is `main`.
There is no atomicity claim across repositories, builds, merges, environments or deploys.

## Additive RLM and EVR fields

New RLMs can replace the old single `code`/`build` pair with optional `release_set`:

```yaml
release_set:
  version: 1
  repositories:
    repository:product:sample:api:
      commit: FULL_COMMIT
      build_digest: sha256:BUILD_DIGEST
    repository:platform:identity:
      commit: FULL_COMMIT
      build_digest: sha256:BUILD_DIGEST
  dependencies: []
```

These are shape placeholders, not executable proof. Copy actual values from authenticated
build provenance. The build digest identifies the shipped artifact (an image, package or
source archive), not a mutable tag. Declare repositories once in product.yaml/PLATFORM;
RLM names their logical IDs, including shared entries applicable through `used_by`.
Every release-relevant repository must be included; a subset cannot read as the whole set.
Do not retain a populated legacy `code.commit`/`build.image_digest` alongside `release_set`.

The canonical candidate payload contains the versioned repositories/dependencies plus the
existing RLM `config`, `infrastructure`, `ai` and `data` objects (absent objects normalize to
`{}`). These authored facts keep their existing home. Dependencies are sorted by manifest
path. `sha256(canonical_JSON(payload))` is its derived identity; an EVR records this in the
optional `release_set_hash` alongside its existing `verified_code`. The verifier compares
both: matching code with another build, prompt, configuration, dataset or target is not
matching evidence. Canonical JSON uses the existing memory serialization contract.
When authorized inputs and the manifest are readable, strict-release returns the computed
`release_set_hash` even if the EVR mismatches. This helps prepare or diagnose the candidate;
the failed gate remains failed and the digest alone is not an evaluation receipt.

The legacy reader normalizes a single code/build pair only if exactly one eligible code
repository is declared. It never broadcasts one commit to multiple repositories or invents
a missing build digest. Ordinary legacy validation remains unchanged. A legacy EVR without
an exact candidate identity is readable historical evidence, not a strict-release pass;
do not backfill or rewrite it. New observations require new evidence.

## Shared releases and compatibility

Each dependency names a manifest path in the same approved documentary repository, its
`release_set_hash`, and `compatibility: {path, sha256, section}`. `section` is an existing
framework section marker in the authoritative source (for example a DEC's `decision`).
The verifier checks source bytes, the marker, exact dependency identities, missing/conflicting
code and bounded acyclic traversal. It does not execute or infer compatibility conditions.
The integration witness must establish those conditions against the full transitive set.
Cross-documentary-repository dependency collection is not provided: unavailable references
block rather than fetching another repository or substituting its latest main.

## Trusted input and receipts

```bash
python3 -I -B /path/to/framework/skills/audit/scripts/validate.py \
  --profile strict-release --trust-input /trusted/release/input.json --json
```

`schemas/memory/release-input.v1.json` specifies the caller API. Trusted CI supplies the
clean framework pin; documentary identity/root/selected commit/approved tip; manifest path;
requested state; authorized classifications/exclusions; repository identity/root and
authenticated default-branch name/tip for the entire transitive code set; receipt witnesses.
Generated RLMs without a classification are readable in this explicitly selected scope;
classified sources outside the filter are not promoted into release evidence.

The tool reads bounded Git objects and regular receipt files, never worktree proposals,
network endpoints, source executables or hooks. Missing/shallow history, dirty runtime,
ambiguous namespaces and unavailable sources fail closed. The documentary selection must
remain consistent with the approved tip. Existing implemented/verified CHG claims raise
the required evidence level even when a caller requests only `prepared`.

Receipts conform to `schemas/memory/release-receipt.v1.json`. Each carries producer/run,
stage, exact documentary revision, RLM/EVR paths, candidate identity and execution result.
The controller independently authenticates the bytes, producer, run and stage and supplies
their witness. A hash copied from a PR or an EVR saying `go` is not authentication.

- `pre-release`: verify artifact-to-code build provenance, actual evaluated artifacts,
  the frozen EVP hash/version, all required metrics/slices and blocking thresholds. The
  framework checks the linkage/hash, not arbitrary numerical tables in prose.
- `integration`: run the required integration tests and compatibility checks for the
  entire candidate and dependencies. It does not imply commits were merged atomically.
- `deployment`: independently observe the entire runtime set (dependencies included),
  record its `observed_set_hash`, actual environment and timezone-qualified `observed_at`,
  then attest the smoke result. Expected manifest values are not observed values.

Do not reuse a green receipt after changing a commit, build, configuration, dependency,
documentary revision or evaluation. The controller must select the relevant current run,
including failed or rolled-back observations; never search history for any old green run.
Deploy test code only in a separate authorized workflow; do not expose deployment secrets
to PR code or execute receipt commands. The framework is not that workflow or collector.

## Interpretation and boundaries

The command emits JSON (exit 0 passed bounded gate, 1 failed, 2 unavailable/invalid
invocation). `supported_state` states what the supplied authenticated observations support;
`status_changed` and `deployment_executed` stay false. `review_required` stays true.
An observation is evidence as of its recorded run, not continuous monitoring or a promise
that an environment has not changed since. Default-branch ancestry proves inclusion, not
semantic preservation after later changes; exact runtime artifacts remain independently
bound by the deployment receipt.

Ordinary `validate.py` adds RLS001/RLS002 only when an RLM declares the new `release_set`.
They are documentary warnings, not authenticated release approval. Strict-release makes
its gates errors and cannot be weakened through project severity overrides. Keep the
ordinary full documentary audit and the project's human approval process.

After genuine delivery, propose the normal lifecycle and observation-window updates.
Do not move a CHG to verified merely because RLM/REL exist, and do not modify the body
of an immutable CHG/RLM/EVR. A changed candidate is a new immutable manifest/evaluation.
