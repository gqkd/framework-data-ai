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
section markers. The status and the closure metadata of a `CHG` -- `verified_by`,
`withdrawn_by` -- and its forecast, `affects`, can change without rewriting the mandate: the
forecast authorizes nothing, paths and obligations being the policy's, so since 4.10.0 an
approved mandate no longer freezes it. Status regression, rollback, withdrawal or revoked
current approval cannot authorize work.
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

A hotfix nobody who decides could authorize in time goes with `no-chg: hotfix <reference>`,
from 4.12.0 pinned or no version that reads; afterwards -- in the additive mode at the first
join -- whoever decides writes the `SIG`, the `ICG` and a `CHG` with `hotfix: true` that says
it was authorized after (`cycle`, *A hotfix*; `contribute`, *The hotfix*). Where the policy of
the code has no `exception_reviewers`, `no-chg` never passes (`AUT006`): the hotfix is approved
before its code goes, as any change -- in the additive mode through a lightning join, the join
open abandoned first, or on that join once its whole review is done, closed at once. Either
way its code follows the project's road to production, pre-production included.

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
when. Every project has the place: `_scambio` beside the repositories, which the guard lets
every session write in and the template's section on review of `AGENTS.md` names. Declaring
it is what turns on the rest -- the rule below with its fixed names, `risorse.md` and the
closing declaration, the brief `cycle` writes there and the delivery `contribute` takes from
there, the section of `AGENTS.md` that says the rule, `exchange.py` and the checks of the
validator: a project that declares no exchange has the place and none of its discipline, but
for the rule on copies of credentials where it pins 4.12.0 or later, or no version that reads
(*Copies of credentials*, below). Below 4.13.0 pinned declaring it is optional. Where the
project pins 4.13.0 or later, or no version that reads, it is a requirement to implement, with
the command line of Claude Code, `claude`, on the machine of whoever implements: every code
session is launched by a documentation session on its brief in the exchange, and delivers
there (*The code session, launched*, below), so with no exchange declared `exchange.py code`
refuses and no code session starts. In the additive mode the `exchange:` line enters with the
join that brings the project to 4.13.0; outside it the documentation session proposes it, on
the person's yes; `work.py doctor` checks both requirements and says how to meet them.

### The place

A project declares it in `.framework/sessions.yaml`, relative to the root of the
documentation repository, outside it:

```yaml
exchange: ../_scambio
```

Not in `framework.yaml`, for the reason the annotations are not there either: a key that file
does not know stops every validator released before it, the one `migrate.py` rebuilds and
the one a CI job pins alike. A hidden path is invisible to all of them, so the file can be
written the day the project adopts this version, or any day after. The day it is written,
`migrate.py --root <documentation> --adopt` puts the section on the exchange into
`AGENTS.md`: nothing runs it by itself, and until it runs the report lists the section.
Adopting 4.13.0 or a later version where the line is missing, the `audit` skill writes it
before `--adopt`, on the yes of whoever adopts -- in the additive mode an admin, on the branch
of the join that brings the version --, so that `--adopt` writes that section the same day
(`skills/audit/SKILL.md`, *Adopting a new version of the framework*).

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
place does not exist, a CI runner being the ordinary case, nothing about it is checked but its
name (`EXC008`), and the report says so in a line; an annotation in
`.framework/expected-findings.yaml` about the exchange, `EXC008` aside, is not reported as
obsolete there, since nothing looked.

### One folder per element, with fixed names

```
_scambio/
  in-arrivo/CHG-021/      until the documentation session has integrated it
    brief.md              written by `cycle` (step 6): the mandate, for the code session
    verifica.md           the verification, for the change's §Verification
    mr.md  mr-link.txt    the text and the link of the merge request
    evidenze/             evidence: logs, outputs, screenshots
    contribution-policy.json
    documentazione.md     what the documentation should say, which the code session proposes
    domande.md            the code session's questions to its person, one entry each, dated
    sessione-codice.json  the launch file `exchange.py code` writes: the launch, its runs
    risorse.md            what the work created outside the repositories
    sessioni/2026-10-14-ab12cd34.md   a closing declaration per session that writes one
  integrati/CHG-021/      the same folder, moved, with INTEGRATO
  sessioni/               declarations of sessions that worked on no single element
```

The folder is named by the element's identifier: a change, or the entry a report is about
when it is not a mandate's (measurements on an open decision go in `in-arrivo/OD-128/`). The
names inside are fixed, so that nothing has to carry the identifier in its own name, and a
file named with the prefix, the shape this replaces, is a finding. Inside `evidenze/` the
names are free. Material that fits none of the fixed names goes in `evidenze/`.

`documentazione.md` is how a code session, which writes no documentation, says what the
documentation should say after its change. In the additive mode a thread draws its effects from
it (`references/additive.md`, *What a code session delivers*): everything goes through the
threads, the documentation the code changes included. Where the project pins 4.13.0 or later,
or no version that reads, it is delivered outside the mode too, where the documentation session
writes it into the documents when it brings the delivery in, with the rules of the
`requirement` skill; below 4.13.0 pinned it is a delivery of the additive mode alone.
`domande.md` and `sessione-codice.json` are fixed names at every version pinned, as every name
here: one exchange serves a machine whose worktrees may pin different versions.

### From in-arrivo to integrati

When the documentation session has integrated a delivery, and committed it, it moves the
folder to `integrati/` and writes `INTEGRATO` there -- since 4.12.0 `exchange.py integrate <ID>`
does both, with the default place of each part, and leaves to a person what it cannot know:
`mr.md`, what a verification cites for an entry, a policy carried outside the additive mode. A
verification it says placed in the change's §Verification is one that section holds at the
commit: while it is empty, or holds only the template's sentence, `integrate` refuses:

```yaml
commit: 4f1c2a9e7b30          # the commit of the documentation that integrated it
date: 2026-10-14
parts:                        # every delivered name in the folder, and where it went
  verifica.md: CHG-021 §Verification
  evidenze/: CHG-021 §Verification, cited
  mr-link.txt: CHG-021 §Verification
  contribution-policy.json: .framework/contribution-policy.json
```

`brief.md`, `risorse.md`, `domande.md`, `sessione-codice.json` and `sessioni/` are not parts:
they were written about the work, not delivered as its result, and a folder with nothing
delivered moves with `parts: {}`; the launch file moves with the folder, and says the launch
closed. The commit is the one on the branch the documentation is read from -- in the additive
mode, the thread's branch, or the join's for a mandate no thread held, which the clone's work
branches hold until the join and the main line after it: after a squash or a rebase, write the
new one. A second delivery for an element already integrated, or a new brief for it, waits in
`in-arrivo/` like the first, so the same identifier can be in both stages; integrated, its
files join the folder in `integrati/` and `INTEGRATO` becomes a list with one block per
integration. A file it replaces was integrated by the earlier block's commit, which still
holds what mattered of it. Below 4.13.0 pinned `integrate` refuses an element already in
`integrati/`, and the folders are joined by hand. Where the project pins 4.13.0 or later, or no
version that reads, `integrate` joins them itself -- one block more in `INTEGRATO`, a part
delivered again taking the place of the one with its name, `evidenze/` adding up, a file whose
name is taken getting the number of its block --, and a block `parts: {}` beside the others is
a launch closed with nothing delivered; outside the additive mode it says `documentazione.md`
`written into the documents by <commit>`. It refuses an element whose last run of a code
session is running or was never read.

On the parking branch of a hotfix, in the additive mode and from 4.13.0 pinned or no version
that reads, the whole delivery goes on the branch, in its delivery folder
`_filoni/<slug>/consegne/<CHG>/`: `documentazione.md`, from which the branch's effects are
written, `verifica.md`, `mr-link.txt` with the line of the merge request (*The code session,
launched*, below) and `evidenze/`. It is committed, then `integrate` runs on that branch --
while the change has no verification yet, or is not written, a `no-chg`, it says the
verification, `mr-link.txt` and `evidenze/` placed in that folder --, then the branch is
pushed. At the join that lands the branch, once its code is merged, whoever decides carries
them into the change's §Verification with the texts of the join, which its review reads
(`contribute`, *The hotfix*). The cost is that `evidenze/` enters the history of the
documentation, which `--finish` does not remove: before it comes onto the branch, the
documentation session reads its text files, and a file that carries the value of a credential
is said to the person, who deletes or cleans it in the exchange first -- `evidenze/` with it
where it is left empty: git keeps no empty folder, and `integrate` would find it delivered and
not on the branch. Nothing checks it, and nothing reads an image. Outside the additive mode the
delivery of a `no-chg` waits for its change to be written, then is integrated as always.

A delivery is a proposal, never an input of the strict profile: a `contribution-policy.json`
in the exchange governs nothing until the documentation session has reviewed it and
committed it at `.framework/contribution-policy.json`, before the implementation it governs.

```bash
python3 "${CLAUDE_PLUGIN_ROOT:?}/skills/audit/scripts/exchange.py" --root <documentation>
```

lists, in the order they are worth reading: the elements the documents already call done
whose folder is still in `in-arrivo/`; the deliveries waiting for integration, the oldest
first, with the days since the oldest delivered file; the elements with a brief and nothing
delivered yet; below 4.12.0 pinned, the resources of elements done still there, with their
commands; the declarations in `sessioni/`; and the findings below. It reads modification
times off the disk, so a copy that does not preserve them resets the count. It moves and
writes nothing;
`integrate <ID>` moves one folder and writes its `INTEGRATO`.

### The code session, launched

Where the project pins 4.13.0 or later, or no version that reads, every code session starts
from a documentation session, which launches it on the brief of an approved change, answers
what is its to answer and brings the delivery in: nobody opens Claude in the code repository,
and nothing is carried by hand -- no brief to another machine, no delivery back. Whoever
implements launches from their own documentation session, on their machine, and in the additive
mode holds the thread of the change; there a hotfix launches from the worktree of its parking
branch, `work.py open --branch hotfix-<home>-<change>` -- the name the to-do prints beside it;
for a `no-chg`, `hotfix-` and its reference as a slug, the change's number reserved there when
its brief is written --, which is its claim. Below 4.13.0 pinned the code session is opened by
hand, as before, and `code` refuses. Each call is one command, with the absolute path written
out, as the sandbox lets it out (`references/workstation.md`):

```bash
python3 <framework>/skills/audit/scripts/exchange.py --root <root> code CHG-021 --repo ../app \
    [--base <branch>] [--no-chg "hotfix <reference>"] [--join-base [auto|merge|rebase]]
python3 <framework>/skills/audit/scripts/exchange.py --root <root> code CHG-021 --launch
python3 <framework>/skills/audit/scripts/exchange.py --root <root> code CHG-021 --resume \
    [--allow <file>]... [--reply <file>]
python3 <framework>/skills/audit/scripts/exchange.py --root <root> code CHG-021 --status
```

`<root>` is the thread's worktree in the additive mode, the parking branch's for a hotfix, the
documentation repository outside the mode. What the launch grants and prepares comes from the
brief's `Commands` block, which `cycle` writes and its review reads: `test:` the tests the code
session may run, `prepare:` the preparation of the worktree, `generated: <file>, by <command>`
the files only the documentation session regenerates, `link:` the files git ignores that are
linked from the main checkout.

**The first call**, `--repo`, prepares the worktree, and launches nothing nor runs the
preparation the brief names. It reads the mandate -- the version
pinned, the brief in `in-arrivo/<CHG>/`, the change `approved` at `--root` (with `--no-chg`, a
hotfix whose change is not written yet) and, in the additive mode, the thread of `--root`
holding it --, fetches the code repository, and creates beside it the code session's worktree,
`<repository>-<chg>`, on the branch of the work: in the additive mode the thread's, with the
name it has in the documentation, or the parking branch of a hotfix; `<chg>` outside the mode.
A new branch starts from `--base`, or from the remote's default branch; one an earlier launch
made, from the start that launch recorded. The call links from the main checkout the files git
ignores that the brief names, read and never written, writes the worktree, its branch and the
links in `risorse.md`, writes the launch file, and stops. What comes next it prints, for the
documentation session to run as its own commands, in view, on the person's yes: the push of the
branch, the preparation the brief names, and `--launch`; under the sandbox the push and the
preparation are the person's to run. The code repository is one beside the documentation, in
the folder that holds the exchange, where the write guard holds the code session; a change
changes one repository, and a change in another is a change of its own.

**`--launch`** runs `claude -p` in the worktree, under `dontAsk`, with the plugin the command
runs from, the delivery folder, and what the code session may do without asking: read, write --
the guard is the limit --, the reviser, the git commands that read, `git add`, the validator and
the tests the brief names. Anything else is denied, and is a stop: a commit comes back as a
question to the person -- where the person's own settings do not allow it
(`references/workstation.md`) --, and pushing and opening the merge request are never the code
session's.

**`--resume`** resumes the same session with one of three things: the rule the person approved
now, written whole in a file, for that run only (`--allow`, and only a rule the last stop
proposed); the answer to its question (`--reply`, a file); or neither, after the documentation
session ran `git rebase --continue` or the commit that concludes a merge of the base, or after
a stop with nothing to approve or answer. **`--status`** says whether it runs and where it
stopped. A resume or a new launch is made from any documentation session of the machine.

**The stops.** Each run ends on one, said in a few lines and written in the launch file, exit 0:

- `negata`: each action denied, with the rule that would grant it. A write the framework's
  guard stopped, or a hook of the person's, is said apart and has no rule: the code session
  proposes what the documentation should say in `documentazione.md`, and writes nothing outside
  its places. A push or a merge request is said apart too, and is no question, being never the
  code session's; and so is `git rebase --continue`, or the commit that concludes a merge of the
  base, which the documentation session runs on the person's yes and never grants;
- `account`: a limit or a credential of the account, the five hours or the week of the
  subscription among them;
- `domanda`: the last entry of `domande.md`, said with any stop of its run;
- `consegna`: the fixed names delivered since the launch began, when nothing was denied and
  nothing asked, and never with a rebase or a merge of the base in progress;
- `fine`: none of these, with the code session's answer, and the error of the run if one ended
  it. A step of network the code session's own sandbox stopped -- a test that wants the network
  -- is a command that failed, and ends here: the documentation session gives the person the
  command, without retrying it outside the sandbox.

**What the documentation session answers.** It says each stop to the person in plain words, and
approves nothing by itself: every approval is the person's yes, for the command written whole
and for the next run alone.

- An action denied is the question: the command, why the code session says it needs it,
  approve? On the yes, the resume with its rule; several rules together where the person
  approves them together. For a commit the question shows what would enter it, read by the
  documentation session: `git -C <worktree> status --short` and `git -C <worktree> diff --cached
  --stat`.
- A question of the code session: where the documentation holds the answer, the documentation
  session gives it itself, with the file and the section it comes from, and tells the person
  what was asked and what it answered; where it does not, or the answer is a decision, the
  question goes to the person, and a new decision takes its own road (`requirement`,
  `resolve`). The answer goes back with `--reply`.
- An error of the account is said, and nothing is resumed until the account allows it: it is
  the one limit on what a code session uses.
- The delivery: the documentation session pushes the code session's commits and opens the merge
  request of the code with the text of `mr.md`, on the person's yes -- on GitHub with `gh pr
  create`, and on another forge, which nothing here calls, the person opens it with that text
  and gives the link; that of a `no-chg` says `no-chg: hotfix <reference>` --, and writes its
  link in `mr-link.txt`. Then it brings the delivery in: in the additive mode as the thread does
  (`contribute`, *What a code session delivered*), on the parking branch of a hotfix as above,
  outside the mode into the documents. The change's `## Verification` carries the line of its
  merge request, `Merge request: <link> @ <commit>` -- the link, and the forty characters of the
  code branch's head the delivery was verified at; the last such line where there are several,
  the one a thread's to-do and a join read --, and on a hotfix's parking branch
  `consegne/<CHG>/mr-link.txt` carries it, as its last line. The merge request comes first and
  `integrate` after, which closes the launch: a link written after it would be a second
  delivery.

**A launch closes** when the code session has come back with the delivery and the documentation
session has brought it in, with `integrate`; a `fine` does not close it, and one that never
reaches a delivery is closed by `integrate`, `parts: {}`, when the person says so. A change
asked for after -- the review's remarks on the merge request -- is a new launch on the same
change, worktree and branch: the brief back in `in-arrivo/<CHG>/` with what to change and why
added at its end, which the review reads, and the first call again. Its commits go into the
same merge request, and its delivery joins the first in `integrati/` (above).

**The branch already on the remote.** The first call compares the branch with the remote's, as
its fetch left it, outside the additive mode too:

- level with it, or behind -- commits of the code session not pushed yet --: a new launch on the
  same branch, whose push is a fast-forward;
- ahead, the remote holding the branch: the branch is brought to it, and the launch tells the
  code session which commits are not its own;
- no local branch -- a thread taken again on the branch of whoever held it, a worktree and
  branch the person removed --: the branch is created from the remote, and its commits above
  the start said the same way;
- diverged: the first call shows both sides and prints two commands, which the documentation
  session runs, in view, on the person's choice: **join them**, a rebase of the local commits
  on the remote's, whatever the way of merging, with no merge commit and no forced push; or
  **keep the remote**, `git reset --keep` to it, dropping the local commits the person saw.
  `--launch` refuses while they diverge with nothing chosen.

With no conflict the rebase ends by itself, and the code session starts from the rewritten
branch. With conflicts it stops at the first commit that does not apply, and the launch gives
the code session that step first: resolve its conflicts keeping what both sides meant, add the
files by name, try `git rebase --continue`, and stop. The `--continue`, which commits the step,
is denied, and is the question: which step of how many, which local commit it re-applies, and
the files the step left in conflict, with the code session's resolution against the rewritten
branch (`HEAD`, the remote with the steps done) and against the local commit (`REBASE_HEAD`). On
the yes the documentation session runs `git rebase --continue` itself, in view -- under its
sandbox the person runs it --, and resumes the code session with neither `--allow` nor
`--reply`: the resume tells it where the rebase stopped next, or that it is over. The yes is
never a rule of the code session's, so every step in conflict comes back as a question. `git
rebase --abort`, on the person's yes, brings the branch back to its own commits, and the next
first call asks again. While a rebase is in progress no stop is a `consegna`, and the commands
of `risorse.md` do not remove the worktree: conclude it or abort it first. A new launch that
finds it in progress does not apply it again, and gives the code session the stopped step
first.

**The preparation, with a rebase in progress.** The join comes first and the preparation after:
with no conflict on the rewritten branch, as for every launch. With a rebase, or a merge of the
base (below), in progress, and only there, a preparation that fails on the conflict does not
stop the launch. The generated files the brief names beside the preparation -- a lockfile,
with the command that regenerates it -- the code session never writes: at the stop on the
`--continue` of a step that holds one in conflict, or whose commit changes one, the
documentation session regenerates it and adds it, in view, before the question; once the rebase
is over it runs the preparation again on the final tree, before the code session goes on.

**The person's `rerere` off.** The joins `--join-base` makes, and the commands printed for
joining, for each `--continue` and for the commit that concludes a merge of the base, carry
`-c rerere.enabled=false`, for that command only: a resolution recorded in another rebase or
merge does not come back by itself, and every conflict reaches the code session with its
markers. The `--continue` and the commit run with `GIT_EDITOR=true`, since with no terminal the
editor git opens fails.

**A push refused at the delivery.** The fetch and the comparison are the first call's alone, and
the remote can move while the code session works -- a reviewer accepts a suggestion on the
merge request, two machines work on one `<chg>` outside the additive mode. Then the push of the
delivery is refused, not being a fast-forward, and is not forced. The launch stays open: the
documentation session says so and stops there, with no merge request opened and no delivery
brought in. The delivery is made again by a new launch: an addition at the end of the brief
asking to verify again on the updated branch, the first call, which finds the two diverged and
asks to join them or keep the remote, and the verification made again. The earlier delivery
stays in `in-arrivo/<CHG>/` until it is written again, and the stop `consegna` of the new launch
counts only the names written since it began.

**The base, `--join-base`.** The first call also says how far the branch is behind its base:
`--base`, else the start an earlier launch recorded, else the remote's default branch. Where
the forge wants the branch up to date with its base, or its merge request conflicts with it --
`work.py join` says so at its first step --, the documentation session brings it up to date, on
the person's yes: the first call with `--join-base` -- for a launch the integration closed, its
brief back in `in-arrivo/<CHG>/` --, then a new launch that verifies again, and its delivery
integrated again, the line naming the new commit.

- **A merge**, unless the code is merged by a rebase: the base merged into the branch, the
  person's `rerere` off, its commits said to the code session as not its own. A merge stopped
  on conflicts goes to the code session first, which resolves them and stops on the commit that
  concludes the merge: that commit is the documentation session's, on the person's yes, as the
  step of a rebase, the generated files regenerated before the question and the preparation run
  after it. It is pushed at once, before the code session goes on; refused, the remote having
  moved meanwhile, the remote is kept, `git reset --keep origin/<branch>`, and the base joined
  again, the code session resolving its conflicts again. So too where the branch holds a join
  of the base not pushed and the remote has moved: the first call does not propose to join
  them, since a rebase would undo the merge, but to keep the remote and join the base again.
- **A rebase**, where the code is merged by one -- `merge_method: rebase` in the additive mode,
  or `--join-base rebase` --: the branch's commits are re-applied on the base, with the steps of
  a rebase as above, and get new ids, which the code session is told. Its push is forced, with
  lease at the remote's commit the rebase rewrote, on the person's yes: the one forced push, on
  the code branch of the change. Refused, or the remote moved before it, the same: the remote
  kept and the branch re-applied again.

`--join-base` alone, or `auto`, takes the way from `merge_method`; `merge` or `rebase` names it,
against the key too. It refuses with a rebase or a merge in progress, or a branch diverged from
its remote, which come first; a merge in progress that no `--join-base` made is the person's to
conclude or abort before anything is prepared. A forge rule that forbids forced pushes on the
code branch refuses every push of the second way; where the repository does not admit a
rebase, `merge_method: rebase` or not, the way is `--join-base merge`.

**The subscription alone.** The code session runs on the person's subscription, never on an API
key or another provider, and nothing limits what it uses but the subscription. The launch takes
out of its environment `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN`, `ANTHROPIC_BASE_URL` and the
`CLAUDE_CODE_USE_BEDROCK`, `_VERTEX` and `_FOUNDRY` that choose a cloud, and reads its first
event: a credential from anywhere else stops it at its start, on `account`. The same variables
in the `env` block of Claude Code's settings, which no environment reaches, and an
`apiKeyHelper` there, make `--launch` and `--resume` refuse, exit 2, each said with its file,
its line and its name, never its value -- and so does a settings file that opens and does not
read --; the first call says so ahead. A `CLAUDE_CODE_USE_*` set to a value that turns it off is
no provider. The settings read are the organisation's, the person's and the worktree's
(`references/workstation.md`).

**Windows.** On Windows outside WSL `code` refuses: it watches the code session's process with
POSIX calls, and there asking whether a process runs ends it. There `integrate` refuses too an
element whose last run has not ended: `--status`, under WSL, Linux or macOS, says which.

**The launch file**, `sessione-codice.json`, holds the launch and its runs -- the session, the
repository, the worktree, the branch and its start, the rules granted and approved as history,
each run's stop and the code session's answer -- and no value: one beside a name is withheld.
Anybody can write it, the code session too, so each reading takes it whole or not at all: one
not as the command writes it is refused at `--launch`, `--resume` and `--status`, and the first
call writes a new one in its place, without its history, once no code session it names can
still run. The output of a run waits in the person's outputs folder, the person's alone, until
its stop is written. `domande.md` is the code session's, one entry per question with the day,
so that a question is not lost when the documentation session is closed.

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

Removing the resources belongs to whoever created them, on their machine: the session that
created them says in its final answer what is left, with the commands of the list, and the
person removes them when they want, deleting each row, or never. A copy of credentials is the
one exception: the session deletes it when it closes (*Copies of credentials*). The
documentation session does not read `risorse.md`, proposes no removal, asks and waits for
nothing: a change reaches `implemented` at the merge, and `EXC004` is retired. An `EXC005` is
apart, at every version pinned: an exposure on the machine of the person in front of it, which
it tells that person and proposes to delete, running the deletion only on their yes
(`skills/audit/SKILL.md`). A worktree or a copy of credentials is there when its path exists;
the other kinds are names in tools the validator does not run, and are there while their row is.

**A delivery from another machine**, below 4.13.0 pinned. Where the project pins 4.13.0 or
later, or no version that reads, nothing is carried by hand, and this paragraph does not hold:
whoever writes the code launches it from their own documentation session, on their machine --
in the additive mode holding the thread --, and that session brings the delivery in (*The code
session, launched*, above). Below it, the code written by somebody other than who has the
thread is delivered on that person's machine and carried back by hand. The brief travelled the
other way first, carried to that machine with the absolute paths of this one -- the exchange,
the `CHG`, the framework --, which whoever carries it says. The `risorse.md` that comes with it
stays as it came: its resources are that person's, nobody here proposes or runs anything from
it but the deletion an `EXC005` asks for (above), and only `EXC005` and `EXC007` read its rows,
as they read every list. Its rows go in a note only where the last paragraph of this part holds.

**Copies of credentials.** A copy of a `.env` or of a key lives only in the scratchpad of the
session that needs it, is in the list with its path and the names of the keys it holds,
never their values, and is deleted by that session when it closes, which its final answer
says; it is kept only when its person asks, and then that answer says where it is, with the
command that removes it, and its row stays in the list. Not a resource left for the person to
remove when they want: a secret, which nobody should have to remember. Never under the folder
that holds the repositories: one `git add -A` in the wrong directory publishes it. The rule
holds with no exchange too: the template of `AGENTS.md` says it in a section of its own, *Copies
of credentials*, which `--adopt` writes in every project, and every brief among its guardrails.
Nothing looks for copies nobody listed: the machine is the person's.

**Below 4.12.0 pinned** all of this is as it was. When the element is done -- a change at
`implemented`, which does not wait for a cleaning -- the documentation session lists its
resources with their commands, as `exchange.py` does, and proposes the removal, runs a command
only on the person's approval and deletes the row when it has; a resource still there
afterwards is an `EXC004`, a warning, never an error, `require_all` included. The rows of a
delivery from another machine, which nobody here can remove and `EXC004` would count as still
there, leave the table: the session that brings it in writes them in a note above it that says
whose machine they are on, with their commands, and gives the commands to that person. No line
of the note starts with `|`, which the validator reads as a row wherever it stands, indented or
not; and the note, like the table, never carries the value of a credential. The rule on copies
of credentials is said only where an exchange is declared, in its section of `AGENTS.md` and in
the *Delivery* of a brief.

### The closing declaration

A session, documentation or code, closes with a short declaration -- or with none, in the case
the end of this part says --, written in `sessioni/<date>-<session>.md` of the element's
folder, or of the exchange when the session worked on no single element. `<session>` is the
session's identifier as its tool names it; the first eight characters are enough. Three
sections, with these headings:

```markdown
## Committato
- `CHG-021` in app: 3 commits on `chg-021`, merged as !42

## Non committato
- `products/p/OPEN.md`: OD-128, the two lines of the default in force

## Fuori dai repository
- see `risorse.md`: the worktree and the isolated stack
```

A section with nothing to say says `niente`. The second is what lets another session, in the
same working tree, commit the work of all of them without guessing whose a line is. A
declaration in the exchange's own `sessioni/` is removed by the session that commits what it
lists as not committed; one in an element's folder travels with the folder. Where the project
pins 4.12.0 or later, or no version that reads, a session that committed everything, with no
review that was due left undone, writes none, since a declaration that says `niente` under
*Non committato* is one nobody would ever remove; a review that was due and did not run is
still said in one.

### What the validator reports on it

Only where the place exists, and reading only names, modification times, `risorse.md`,
`INTEGRATO` and the headings of the declarations: never a verification, an evidence or a
copy of credentials. It does not look for copies nobody listed.

| Check | What it says |
|---|---|
| `EXC001` | a folder names an identifier the documentation does not declare |
| `EXC002` | an element done in the documents still has its folder in `in-arrivo/` |
| `EXC003` | a folder in `integrati/` whose `INTEGRATO` is missing, unreadable, names a commit the documentation's history does not hold, or leaves a delivered name without a destination |
| `EXC004` | below 4.12.0 pinned, a resource still there after its element is done; retired from 4.12.0 pinned, or no version that reads |
| `EXC005` | a copy of credentials under the folder that holds the repositories, or a value in the list |
| `EXC006` | a name the framework does not read: a loose file, a name not fixed, the exchange inside a git repository |
| `EXC007` | a resource row without a known type, an absolute path where one is due, or a command; a copy of credentials without its keys; a declaration misnamed or without one of its sections |

Done, for the exchange, means a change at `implemented`, `verified`, `rolled-back` or
`withdrawn`, or an `OD` or `KI` entry `decided` or `superseded`: the work is merged, or the
question answered. A change `withdrawn` integrates nothing, and its folder goes to `integrati/`
all the same: its `INTEGRATO` names, as `commit`, the commit of the documentation that withdrew
it, and says in `parts` of each delivered name that it was dropped, and why -- `parts: {}` when
nothing was delivered.
It is earlier than what the digest counts as closed, a change at `verified`, and on purpose:
what a mandate created outside the repositories serves the work up to the merge. A change
that two documents declare is done only when both say so. All seven are warnings, and five do
not count for `require_all`: `EXC001`-`EXC004` -- `EXC004` where it is not retired -- and
`EXC007` are the upkeep of a folder that differs from one machine to the next. `EXC005` and
`EXC006` do, because each can say that something is exposed: a credential, an exchange inside
a git repository -- and from 4.12.0 pinned, or no version that reads, they are the only
warnings `require_all` counts on a thread's or a parking branch, since the join, run on
another machine, never sees them; there the way out is the repair. Since 4.12.0 `FW001` and
`FW003` do not count either: they say which validator, and which commit of the framework, a
machine runs -- but for the line of a commit that is wrong, which below 4.12.0 pinned is still
an `FW003`, the document's, and counts as it did.

The rule has to reach sessions that run no skill, which only the project's `AGENTS.md` does.
The template's section *Sessions and the exchange* says it, and `migrate.py --adopt` writes
it there, with the declared place, once `.framework/sessions.yaml` declares one. The
template's section on review names the place itself, declared or not, and `--adopt` brings
that text to a copy of the section still in an earlier version's words, where it can read
that version: in the framework's git history, or with `--from-framework`.
