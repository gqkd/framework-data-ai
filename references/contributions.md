# Contributions: approved base, bounded scope and execution evidence

Use this for external contributions and multi-repository PR assessment, and for the
exchange where sessions hand each other material (the last section). It extends, not
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

## The exchange between sessions

A project where one documentation session and several code sessions work in parallel hands
material between them: a brief going out, a verification, the text and the link of a merge
request, evidence and a contribution policy coming back. Every rule above says where that
material ends up. None said where it waits, or when it goes, and after six weeks of parallel
sessions the folder holding the repositories was full of worktrees already merged, deliveries
already integrated and copies of credentials nobody removed. This section is the rule for
when. It is optional: a project that declares no exchange works as before.

### The place

`.framework/sessions.yaml` declares it, relative to the root of the documentation
repository, outside it:

```yaml
exchange: ../_scambio
```

Not in `framework.yaml`, for the reason the annotations are not there either: a key that file
does not know stops every validator released before it, the one `migrate.py` rebuilds and
the one a CI job pins alike. A hidden path is invisible to all of them, so the file can be
written the day the project adopts this version, or any day after. The day it is written,
`migrate.py --root <documentation> --adopt` puts the section on the exchange into
`AGENTS.md`: nothing runs it by itself, and until it runs the report lists the section.

The value is committed and read on every machine with a clone, so an absolute path, one
starting with `~`, or one that falls inside the documentation repository stops the validator
with the repair. Code sessions must be able to write there. In the working folder the plugin's
write guard lets a session write, outside its repository and that repository's worktrees, only
`_scambio` beside it, what Claude Code keeps for the session and the folders of the plugin
option `allowed_dirs`; the documentation repository also the place it declares, once
committed, when that is a folder beside it that is not a repository
(`references/workstation.md`). A project that declares another place names it `_scambio`, or
has every person add it to `allowed_dirs`. The guard only stops: Claude Code still asks before
a write outside the session's folder, and how a project lets its sessions write in the
exchange without asking (a permission, an added directory) is the project's. The framework
never relies on material copied by hand out of a session's scratchpad. On a machine where the
place does not exist, a CI runner being the ordinary case, nothing about it is checked and
the report says so in a line; an annotation in `.framework/expected-findings.yaml` about the
exchange is not reported as obsolete there, since nothing looked.

### One folder per element, with fixed names

```
_scambio/
  in-arrivo/CHG-021/      until the documentation session has integrated it
    brief.md              written by `cycle` (step 6): the mandate, for the code session
    verifica.md           the verification, for the change's §Verification
    mr.md  mr-link.txt    the text and the link of the merge request
    evidenze/             evidence: logs, outputs, screenshots
    contribution-policy.json
    risorse.md            what the work created outside the repositories
    sessioni/2026-10-14-ab12cd34.md   a closing declaration per session
  integrati/CHG-021/      the same folder, moved, with INTEGRATO
  sessioni/               declarations of sessions that worked on no single element
```

The folder is named by the element's identifier: a change, or the entry a report is about
when it is not a mandate's (measurements on an open decision go in `in-arrivo/OD-128/`). The
names inside are fixed, so that nothing has to carry the identifier in its own name, and a
file named with the prefix, the shape this replaces, is a finding. Inside `evidenze/` the
names are free. Material that fits none of the fixed names goes in `evidenze/`.

### From in-arrivo to integrati

When the documentation session has integrated a delivery, it moves the folder to
`integrati/` and writes `INTEGRATO` there:

```yaml
commit: 4f1c2a9e7b30          # the commit of the documentation that integrated it
date: 2026-10-14
parts:                        # every delivered name in the folder, and where it went
  verifica.md: CHG-021 §Verification
  evidenze/: CHG-021 §Verification, cited
  mr-link.txt: CHG-021 §Verification
  contribution-policy.json: .framework/contribution-policy.json
```

`brief.md`, `risorse.md` and `sessioni/` are not parts: they were written about the work, not
delivered as its result, and a folder with nothing delivered moves with `parts: {}`. The
commit is the one on the branch the documentation is read from: after a squash or a rebase,
write the new one. A second delivery for an element already integrated, or a new brief for
it, waits in `in-arrivo/` like the first, so the same identifier can be in both stages;
integrated, its files join the folder in `integrati/` and `INTEGRATO` becomes a list with one
block per integration. A file it replaces was integrated by the earlier block's commit,
which still holds what mattered of it.

A delivery is a proposal, never an input of the strict profile: a `contribution-policy.json`
in the exchange governs nothing until the documentation session has reviewed it and
committed it at `.framework/contribution-policy.json`, before the implementation it governs.

```bash
python3 "${CLAUDE_PLUGIN_ROOT:?}/skills/audit/scripts/exchange.py" --root <documentation>
```

lists, in the order they are worth reading: the elements the documents already call done
whose folder is still in `in-arrivo/`; the deliveries waiting for integration, the oldest
first, with the days since the oldest delivered file; the elements with a brief and nothing
delivered yet; the resources of elements done still there, with their commands; the
declarations in `sessioni/`; and the findings below. It reads modification times off the
disk, so a copy that does not preserve them resets the count. It moves and writes nothing.

### What a mandate creates outside the repositories

`risorse.md`, written by the session that creates a resource, when it creates it:

```
| Tipo | Percorso o nome | Comando che la toglie |
|---|---|---|
| worktree | /home/me/projects/app-chg021 | git -C /home/me/projects/app worktree remove /home/me/projects/app-chg021 |
| ramo locale | chg-021 in /home/me/projects/app | git -C /home/me/projects/app branch -D chg-021 |
| stack isolato | app-chg021 | docker compose -p app-chg021 down |
| copia di credenziali | /tmp/<scratchpad>/.env.misure (DB_URL, DB_PASSWORD) | rm /tmp/<scratchpad>/.env.misure |
```

The types are `worktree`, `ramo locale`, `stack isolato`, `volume`, `immagine`,
`copia di credenziali` and `altro`. Paths are absolute, because the list is read from
whatever directory the next session starts in. The list is what is still there: a resource
removed is a row deleted.

When the element is done, a change at `implemented`, the documentation session lists its
resources with their commands and proposes the removal. It runs a command only on the
person's approval, and deletes the row when it has. A resource still there afterwards is a
warning, never an error. A worktree or a copy of credentials is there when its path exists;
the other kinds are names in tools the validator does not run, and are there while their row
is.

**Copies of credentials.** A copy of a `.env` or of a key lives only in the scratchpad of the
session that needs it, is in the list with its path and the names of the keys it holds,
never their values, and is deleted when the session closes. Never under the folder that
holds the repositories: one `git add -A` in the wrong directory publishes it.

### The closing declaration

Every session, documentation or code, closes with a short declaration, written in
`sessioni/<date>-<session>.md` of the element's folder, or of the exchange when the session
worked on no single element. `<session>` is the session's identifier as its tool names it;
the first eight characters are enough. Three sections, with these headings:

```markdown
## Committato
- `CHG-021` in app: 3 commits on `chg-021`, merged as !42

## Non committato
- `products/p/OPEN.md`: OD-128, the two lines of the default in force

## Fuori dai repository
- see `risorse.md`: the worktree and the copy of the `.env`
```

A section with nothing to say says `niente`. The second is what lets another session, in the
same working tree, commit the work of all of them without guessing whose a line is. A
declaration in the exchange's own `sessioni/` is removed by the session that commits what it
lists as not committed; one in an element's folder travels with the folder.

### What the validator reports on it

Only where the place exists, and reading only names, modification times, `risorse.md`,
`INTEGRATO` and the headings of the declarations: never a verification, an evidence or a
copy of credentials. It does not look for copies nobody listed.

| Check | What it says |
|---|---|
| `EXC001` | a folder names an identifier the documentation does not declare |
| `EXC002` | an element done in the documents still has its folder in `in-arrivo/` |
| `EXC003` | a folder in `integrati/` whose `INTEGRATO` is missing, unreadable, names a commit the documentation's history does not hold, or leaves a delivered name without a destination |
| `EXC004` | a resource still there after its element is done |
| `EXC005` | a copy of credentials under the folder that holds the repositories, or a value in the list |
| `EXC006` | a name the framework does not read: a loose file, a name not fixed, the exchange inside a git repository |
| `EXC007` | a resource row without a known type, an absolute path where one is due, or a command; a copy of credentials without its keys; a declaration misnamed or without one of its sections |

Done, for the exchange, means a change at `implemented`, `verified` or `rolled-back`, or an
`OD` or `KI` entry `decided` or `superseded`: the work is merged, or the question answered.
It is earlier than what the digest counts as closed, a change at `verified`, and on purpose:
what a mandate created outside the repositories serves the work up to the merge. A change
that two documents declare is done only when both say so. All seven are warnings.

The rule has to reach sessions that run no skill, which only the project's `AGENTS.md` does.
The template's section *Sessions and the exchange* says it, and `migrate.py --adopt` writes
it there, with the declared place, once `.framework/sessions.yaml` declares one.
