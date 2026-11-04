# The workstation: what a person needs to work with the framework

What a machine needs before a person writes documentation or code with the framework, the
hooks the plugin brings into every session, and the rules on where an agent may write. Read
it once per machine, and again when the plugin's version changes: the hooks follow the plugin,
and the version a project pins decides whether the hook at the start of a session says the to-do
and, where a version brought a new rule -- the threads of 4.11.0, a code in a heading --, which
one the to-do and the validator apply (`validate.rules_hold`).

## What to install

- **Claude Code**, with the framework installed as a plugin at the version the project pins in
  `framework.yaml` at the root of the documentation or a later one, the latest release best: the
  hook at the start of a session says where it stands. The README says how to install it and how to
  update it. The symlink into `~/.claude/skills/` the README also describes brings the skills and
  not the hooks: no guard. Tested with Claude Code 2.1.310 on Linux, the hook at the start of a
  session with 2.1.317; the earliest version that works is not known.
- **Python 3** with the framework's dependencies, from the framework's directory:
  `python3 -m pip install -r requirements.txt -c constraints.txt`. The write guard runs as
  `python3 -I` and needs nothing else: with no `python3` on the PATH the hook fails, and a
  hook that fails lets every write through, which only the last check below notices. The
  scripts of the skills need PyYAML and the rest.
- **git**, with worktrees: `work.py open` creates one beside the documentation repository
  for every work it opens.
- **`gh`**, where the project's workflows or a skill open pull requests.

## The folders

The documentation repository, the code repositories and the exchange sit side by side in one
parent folder:

```text
<parent>/
  <documentation>/      the repository with .framework/
  <code>/               each code repository of the project
  <documentation>--<slug>/   the worktrees work.py open creates
  _scambio/             the exchange between sessions
```

That parent folder is the **working folder**: the documentation repository and every
repository beside it. The exchange is `_scambio` beside the repositories, so that
`exchange: ../_scambio` in `.framework/sessions.yaml` names the same place from every
repository and every worktree, on every machine; a project that declares another name
leaves code sessions, which read no `sessions.yaml`, without it, unless every person adds it
to `allowed_dirs`.

**One project per parent folder.** A second repository with `.framework/` goes into another
parent folder: two projects would share `_scambio`, where each element has a folder named by
its identifier, and the `CHG-021` of one would land on the `CHG-021` of the other. Every
repository in the parent folder is under the guard, those that have nothing to do with the
project included.

You work under one name: the one `--who` takes, among the `people` of `.framework/work.yaml`.

## The hooks the plugin brings

**The write guard** (`hooks/guard.py`, a `PreToolUse` hook on Write, Edit and NotebookEdit).
In a session started inside the working folder it lets an agent write:

- in the repository the session started in, and in that repository's worktrees, the main
  checkout among them;
- in the exchange: `_scambio` beside the repository, and the place `.framework/sessions.yaml`
  declares, for the repository that declares it, as committed on the branch the session works
  on; each only when it is a folder beside the repository that is not a repository itself,
  links followed;
- in what Claude Code itself keeps for a session: its scratchpad, in the temporary folder;
  and under `~/.claude` or `CLAUDE_CONFIG_DIR`, the memory of its project -- named after the
  main checkout, which the worktrees share -- and the plans, a folder Claude Code shares among
  all projects. A memory moved with `autoMemoryDirectory`, and the memory of subagents
  (`agent-memory`), go into `allowed_dirs`;
- in the folders of the plugin option `allowed_dirs`, absolute or relative to the parent
  folder: Claude Code asks for it when the plugin is enabled, and `/config` changes it. It is
  the way out for a write meant to land elsewhere, a folder of deliverables for instance.

Anything else it stops, and tells the agent to ask the person. It grants nothing: a write it
lets through outside the session's folder, in the exchange for one, still needs Claude
Code's own permission, which `/add-dir` or a permission rule gives. It runs in subagents too, and
before every call whatever the permission mode. Outside the working folder it does nothing at
all, and neither does it in a session started in the parent folder itself, which is no
repository: start sessions in a repository.

It sees Write, Edit and NotebookEdit only: a command run through Bash, or a tool of an MCP
server that writes files, writes wherever the operating system lets it. The limit for Bash
is the rule below, which an agent follows and nothing enforces; the sandbox Claude Code
offers for Bash is what can enforce it.

**The versions, and the to-do, at the start of a session** (`hooks/session_start.py`, a
`SessionStart` hook). In a project of the framework -- a `framework.yaml` with a
`framework_version:` line, or `.framework/work.yaml`, above the folder the session started in; a
`framework.yaml` of another tool, with no such line, leaves it silent -- it puts in the session's
context, from 4.12.0, three versions: the plugin's, from its `plugin.json`; the latest release,
the highest `v<x>.<y>.<z>` tag where the plugin comes from, read with `git ls-remote --tags`, with
no terminal and git's and ssh's prompts turned off -- a credential helper of another system, as
Git Credential Manager from Windows under WSL, may still open a window for a private source --, at
most once a day whether the read succeeds or not, the day and the last answer kept in the plugin's
data folder (`CLAUDE_PLUGIN_DATA`) -- when it cannot be read it says so and uses the last answer
kept --; and the one the project pins. The mode and
the pin are read as the to-do reads them: from the main line's `.framework/work.yaml` and, in the
mode, its `framework.yaml`; from the checkout's where the main line does not read, and the
checkout's pin outside the mode. A plugin older than the latest release is said first, and older
than the pin more strongly, since there the problems are certain: the agent tells the person and
asks them to accept going on with it or to update first, an answer recorded nowhere, which is a
fact of their machine. It asks when the session starts, and on a resumption, a `/clear`, a
compaction or a fork puts the versions back without asking. Where Claude Code says nobody attends
the session -- `CLAUDE_CODE_SESSION_ATTENDED` is `0` under `claude -p`, seen with 2.1.317 and not
in its documentation --, nobody is asked: the agent says it at the top of its final answer. Where
that variable is missing or says anything else, the session counts as attended, and the person is
asked. The evaluations' runners, which run `claude -p`, do not turn it off: where the plugin is
installed as a plugin, and not through the symlink alone, the line of the versions is in their
sessions as in anybody's. The commands it gives, for the person
to run, follow the way the plugin was installed, read from Claude Code's
`known_marketplaces.json` and from where the plugin's files are: from a marketplace added by URL,
`claude plugin marketplace update` and `claude plugin update`; from a local folder that is a git
checkout, read in place, `git pull` there, and from one that is not, as from a URL; with
`--plugin-dir`, none. Then a new session or `/reload-plugins`.

In a project in the additive mode, read as above, whose pin is the version that brought the mode
or a later one -- or none --, it also runs `skills/audit/scripts/todo.py --summary` and puts its
lines in the session's context: the threads open and who has them, the threads to take, whether a
join is needed, the effects waiting by document. In another project of the framework it says the
versions alone, and outside one nothing. The whole to-do is
`python3 <framework>/skills/audit/scripts/todo.py --root <documentation>`; where the hook could
not compute it -- the scripts' dependencies missing, no main line in the clone -- it says so in
one line, with the reason. The summary is computed by the plugin's `todo.py`; a `<framework>`
checkout at another version may compute the whole to-do differently.

**Updating the plugin changes the sessions of the working folder** -- as the README says, then
a new session or `/reload-plugins` -- whatever version a project pins and with no `--adopt`: the
guard follows the plugin. A session started with
`claude --plugin-dir <checkout>` has the hooks of that checkout instead.

## The Bash sandbox, recommended

Recommended in this version and not required. No tool of the framework writes it: each person
puts it in their own settings, `~/.claude/settings.json` -- not the documentation repository's
`.claude/settings.local.json`, which is not committed, and so a thread's worktree, where the
sessions of a thread start, does not have it --, and `work.py doctor` says whether the settings
files declare it. The exchange is the one folder outside the repository it has to open,
written as an absolute path, since a relative one is not documented to resolve against the
project:

```json
{
  "sandbox": {
    "enabled": true,
    "allowUnsandboxedCommands": false,
    "failIfUnavailable": true,
    "filesystem": { "allowWrite": ["/absolute/path/to/<parent>/_scambio"] },
    "excludedCommands": ["python3 *work.py* reserve *", "python3 *work.py* renumber *"]
  },
  "permissions": { "disableBypassPermissionsMode": "disable" }
}
```

`allowUnsandboxedCommands: false` stops a command the sandbox blocked from being retried outside
it; `failIfUnavailable: true` stops a session whose sandbox cannot start from running Bash with
none, which is what happens on Linux and WSL2 without `bubblewrap` and `socat`;
`disableBypassPermissionsMode` takes away the mode that answers every question yes. `/sandbox`
in a session shows whether it is active and what it is missing.

`excludedCommands`, from 4.12.0, lets two commands out of the sandbox: the reservation of a
number and the renumbering, which reserves one first, so that writing an identifier needs no
line pasted by the person. By Claude Code's documentation an entry is matched on the text of
the call, with the syntax of a `Bash(...)` rule, where a `*` stands for any text -- the plugin's
path included, whatever it is on the machine --; the call has to be that command alone, since a
`cd`, a redirect or a `$(...)` keeps the whole of it inside, so the agent runs it with the
absolute path written out, not through a shell variable, and nothing around it. A command let
out has the person's whole access, and asks for permission as any other: `reserve` fetches and
pushes one tag, `id/<ID>`; `renumber` does the same, then writes and commits in the worktree it
runs in. The match is on the text alone, so any `python3` call whose text holds `work.py` and
then ` reserve ` or ` renumber ` is let out as well: what guards those calls is that prompt,
which is to be answered on the command it shows. Every other command stays inside, and its
pushes and fetches are the person's. Where the entries are missing, or the sandbox stops a
command anyway, the skill gives the line to paste, as before. `work.py doctor` says whether the
settings files hold both.

What it lets Bash write, by Claude Code's documentation: the folder the session started in and what
is below it, `$TMPDIR`, the directories added with `--add-dir` or
`permissions.additionalDirectories`, those in `allowWrite`, and the shared `.git` of the repository
a worktree belongs to, but for its `hooks/` and `config`: by that, a commit in a thread's worktree
succeeds, where the plan of this version had assumed it would not. What it does not let through,
with this configuration and no network allowed: `work.py open` and `join`, which create a worktree
beside the repository, in the parent folder; a push and a fetch -- `work.py list`, `sync`,
`release`, `delegate`, `revoke` and the steps of `join` that reach the remote --, which need the
network or, for a remote on disk, a folder outside the repository. Those are the person's to run,
and the `contribute` skill says so rather than retrying them; `reserve` and `renumber` are let out,
above. `work.py check` reaches no remote: it writes in the worktree, in `$TMPDIR` and in the shared
`.git`, so by the same documentation it passes, and the agent runs it. `work.py meetings` reaches no
remote either; it writes in `$TMPDIR` while it reads the threads, and its cards in the folder
`--out` names: given one the sandbox lets Bash write -- `$TMPDIR` or a folder below it --, it
passes too. **None of this has been tried yet on a machine with the sandbox active**, the two
commands let out included: it is what the documentation says, and the trial on worktrees, git and
the network comes before the sandbox is required, in a later version.

## Where an agent writes, and why

An agent writes in the repository it was started for, its worktrees included but for one
where another session is working, and asks the person before writing anywhere else. Several
sessions work side by side on one machine, each in its repository or worktree: a file one of
them writes in another's folder is a change the other did not make, did not review and may
commit. The exchange is the one place they share, and what a session leaves outside the
repositories is listed in the exchange and removed when its work is done
(`references/contributions.md`, *The exchange between sessions*).

The guard lets a session into every worktree of its repository: whether another session is
working in one is for the agent to know and for this rule to hold, not for the guard.

- Never write outside through the shell, a copy or a script because the guard stopped a
  write: the stop is the question to ask the person.
- Never start a session with `--dangerously-skip-permissions`. The guard still runs, but
  every other question Claude Code would have asked is answered yes, including those about
  the shell.
- A folder you mean agents to write in goes into `allowed_dirs`, not into a habit of
  approving one write at a time.

## How to check a machine

- `python3 <framework>/skills/audit/scripts/work.py --root <documentation> doctor --who "<name>"`
  reads, offline, what the files of the machine say of everything below but the last point: the
  plugin against the pin and its hooks, the settings, the folders and the exchange, the
  versions of Python, PyYAML, jsonschema and git -- without the first three it stops at once,
  saying which is missing --, the name, and the copies of `ci/branches.yml` and, where this
  checkout shows that the pin ships one, of `ci/refs.yml`: of the second, where the pin's commit
  cannot be read, it says nothing. A `todo` line is what the framework needs, and makes it
  exit 1; a `note` is what it recommends, or only tells. It does not see the settings an
  organisation manages, nor a plugin loaded with `--plugin-dir`.
- `claude plugin details framework-data-ai` shows the version installed and where it is read
  from; it should be the version the project pins or a later one. `doctor`, for the plugin, and
  the hook at the start of a session read the pin as the to-do does: in the additive mode on the
  main line, `origin/main` or `main` where there is none. The copies of the workflows `doctor`
  compares with this checkout's pin, which a join moves with them.
- `python3 -c "import yaml, jsonschema"` from the environment the scripts use.
- `git worktree list` in the documentation repository.
- From a session in the documentation repository, ask the agent to write a file in the
  parent folder: the guard stops it, and its message names what it may write.
