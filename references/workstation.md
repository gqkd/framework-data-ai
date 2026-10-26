# The workstation: what a person needs to work with the framework

What a machine needs before a person writes documentation or code with the framework, the
hooks the plugin brings into every session, and the rules on where an agent may write. Read
it once per machine, and again when the plugin's version changes: the hooks follow the
plugin, not the version a project pins.

## What to install

- **Claude Code**, with the framework installed as a plugin at the version the project pins
  in `.framework/framework.yaml`. The README says how to install it and why a change is
  picked up by reinstalling rather than updating. The symlink into `~/.claude/skills/` the
  README also describes brings the skills and not the hooks: no guard. Tested with Claude
  Code 2.1.310 on Linux; the earliest version that works is not known.
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
offers for Bash is what can enforce it, and its configuration is not in this document yet.

**Updating the plugin changes the sessions of the working folder** -- reinstalling it, as the
README says, and starting the session again -- whatever version a project pins and with no
`--adopt`: the guard follows the plugin. A session started with
`claude --plugin-dir <checkout>` has the hooks of that checkout instead.

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

- `claude plugin details framework-data-ai` shows the version installed and where it is read
  from; it should be the version the project pins.
- `python3 -c "import yaml, jsonschema"` from the environment the scripts use.
- `git worktree list` in the documentation repository.
- From a session in the documentation repository, ask the agent to write a file in the
  parent folder: the guard stops it, and its message names what it may write.
