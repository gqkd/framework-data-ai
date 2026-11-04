#!/usr/bin/env python3
"""Build a project in the additive mode, where the prompts of `contribute` are measured.

Usage: python additive.py <dest-dir>

`contribute` says it works only where `.framework/work.yaml` on the main line declares
`mode: additive`, and in any other repository it names the skill the request belongs to and
stops. Its prompts measured in `default`, which is not in the mode, would measure a skill asked
to do what it refuses. This is `audit/clean-repo`, the smallest correct project, put in the mode:
the roles, open entries with the anchors the threads are computed from, and the history the
to-do reads the main line from.

A git repository with one commit on main, and beside it, as on a machine, its remote, a bare
repository at `../remote.git`, and the exchange at `../_scambio`: `<dest>/../remote.git` and
`<dest>/../_scambio`, which this generator removes and writes again. On the remote, besides
main, luca's parking branch, pushed with one commit and so ready for a join; in the exchange,
what a code session delivered for the approved CHG-001, `documentazione.md` alone. The
triggering runner copies the repository alone, with what its clone holds of the remote: there
the to-do reads, offline, `origin/main` and the parking branch ready, and advises a join, which
the hook at the start of a session puts in the context of every run where the plugin is
installed as a plugin, and not by the symlink alone -- as it did not while the fixture had no
remote --; `work.py`, which fetches, does not get far. The behaviour runner copies the three,
`beside` in `evals/behaviour/contribute/cases.yaml`, and a run takes threads, pushes and
integrates in its own copy. Its review stamps are audit.py's, which move with the calendar.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = Path(sys.argv[1])

with tempfile.TemporaryDirectory() as tmp:
    r = subprocess.run([sys.executable, str(HERE / "audit.py"), tmp], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"audit.py failed:\n{r.stdout}\n{r.stderr}")
    if D.exists():
        shutil.rmtree(D)
    shutil.copytree(Path(tmp) / "clean-repo", D)

# The register in the shape the threads are computed from: each open entry forecasts what it
# will change. OD-004 and OD-012 are decisions, each a thread for those who decide; KI-003 and
# KI-005 forecast one anchor, so they are one thread of work, which a contributor may take; the
# approved CHG-001 is a thread of its own, as every mandate from 4.11.0. Its stamp is the one
# audit.py gave the register, read rather than restated: those move with the calendar.
register = D / "products" / "atlas" / "OPEN.md"
stamp = re.search(r"^last_review: (.+)$", register.read_text(encoding="utf-8"), re.M).group(1)
register.write_text("""\
---
schema: framework/open-register/v1
artifact_type: open-register
lifecycle: living
status: active
owners: [maria]
products: [atlas]
created: 2026-01-01
last_review: STAMP
entries:
  OD-004:
    status: open
    cost_to_reverse: medium
    default_in_force: BigQuery, the landing zone is already there
    affects: [products/atlas/ARC.md#current]
  OD-012:
    status: open
    cost_to_reverse: low
    default_in_force: weekly
    affects: [products/atlas/PBR.md]
  KI-003:
    status: open
    affects: [products/atlas/ARC.md#delta]
  KI-005:
    status: open
    affects: [products/atlas/ARC.md#delta]
  OD-001:
    status: decided
    cost_to_reverse: medium
    closed_by: DEC-001

review_scope: the whole file
---

# Open decisions and known issues

# §1 · Open decisions

## Cost to reverse MEDIUM: changing it later costs a migration, not a rewrite

### OD-004 · Which warehouse for the gold layer

- **Question:** Snowflake or BigQuery for the gold layer?

## Cost to reverse LOW: a setting

### OD-012 · How often the scores are recomputed

- **Question:** Weekly, or every night?

# §2 · Known issues

### KI-003 · The nightly load has no retry

### KI-005 · A failed load leaves the gold layer half written

# §3 · Parking lot

# §4 · Decided, moved out

- OD-001 -> DEC-001
""".replace("last_review: STAMP\n", f"last_review: {stamp}\n"), encoding="utf-8")
chg = D / "products" / "atlas" / "changes" / "CHG-001-scoring.md"
text = chg.read_text(encoding="utf-8")
if text.count("derives_from: DEC-001\n") != 1:
    sys.exit(f"{chg}: no `derives_from: DEC-001` line to put the forecast after; audit.py moved")
chg.write_text(text.replace("derives_from: DEC-001\n",
                            "derives_from: DEC-001\naffects: [products/atlas/ARC.md#target]\n"),
               encoding="utf-8")
(D / ".framework").mkdir(exist_ok=True)
(D / ".framework" / "work.yaml").write_text(
    "mode: additive\npeople: [maria, luca]\nadmins: [maria]\nrereading: optional\n",
    encoding="utf-8")
(D / ".framework" / "sessions.yaml").write_text("exchange: ../_scambio\n", encoding="utf-8")

# The union of the root register, derived from the registers above.
VALIDATE = HERE.parents[2] / "skills" / "audit" / "scripts" / "validate.py"
r = subprocess.run([sys.executable, str(VALIDATE), "--root", str(D), "--emit-index"],
                   capture_output=True, text=True)
if r.returncode:
    sys.exit(f"--emit-index failed:\n{r.stdout}\n{r.stderr}")

# One commit, an hour after the latest review stamp, read from the files rather than restated:
# a stamp cannot be later than the commit that records it (`LC007`), and audit.py decides how
# many there are.
stamps = [s for p in D.rglob("*") if p.is_file() and ".git" not in p.parts
          for s in re.findall(r"^last_review: (\d{4}-\d\d-\d\d \d\d:\d\d)",
                              p.read_text(encoding="utf-8", errors="replace"), re.M)]
when = (datetime.strptime(max(stamps), "%Y-%m-%d %H:%M") + timedelta(hours=1)).strftime(
    "%Y-%m-%dT%H:%M:00+02:00")
env = {**os.environ, "GIT_AUTHOR_NAME": "maria", "GIT_AUTHOR_EMAIL": "maria@example.com",
       "GIT_COMMITTER_NAME": "maria", "GIT_COMMITTER_EMAIL": "maria@example.com",
       "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when,
       "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
for args in (["init", "-q", "-b", "main"], ["add", "-A"],
             ["commit", "-q", "-m", "the project, in the additive mode"]):
    subprocess.run(["git", "-C", str(D), *args], check=True, env=env)

# Beside the project, as on a machine: its remote, a bare repository at `../remote.git`, and the
# exchange at `../_scambio`, which `.framework/sessions.yaml` declares. Relative paths, which git
# and the exchange resolve from the top of the tree they run in: the same place from the project
# and from every worktree `work.py` makes beside it, and, in a copy of the three, the copy's own.
# Written beside `D` and not inside it, so each is removed here: whoever builds `D` removes `D`.
REMOTE, EXCHANGE = D.parent / "remote.git", D.parent / "_scambio"
for p in (REMOTE, EXCHANGE):
    shutil.rmtree(p, ignore_errors=True)
subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(REMOTE)], check=True, env=env)
for args in (["remote", "add", "origin", "../remote.git"], ["push", "-q", "-u", "origin", "main"]):
    subprocess.run(["git", "-C", str(D), *args], check=True, env=env)

# A parking branch of luca's, pushed with one commit, so ready: the next join lands it whole.
# What `open --branch` makes, a branch named after the parking prefix with no claims, made here
# by git with the dates fixed, since `open` stamps the hour it runs.
later = (datetime.strptime(when[:16], "%Y-%m-%dT%H:%M") + timedelta(hours=1)).strftime(
    "%Y-%m-%dT%H:%M:00+02:00")
luca = {**env, "GIT_AUTHOR_NAME": "luca", "GIT_AUTHOR_EMAIL": "luca@example.com",
        "GIT_COMMITTER_NAME": "luca", "GIT_COMMITTER_EMAIL": "luca@example.com",
        "GIT_AUTHOR_DATE": later, "GIT_COMMITTER_DATE": later}
PARKING = "work/parcheggio-retry-policy"
root_register = D / "OPEN.md"
text = root_register.read_text(encoding="utf-8")
if text.count("# §3 · Parking lot\n\n- Nothing qualified yet.\n") != 1:
    sys.exit(f"{root_register}: no parking lot to add a line to; audit.py moved")
subprocess.run(["git", "-C", str(D), "switch", "-q", "-c", PARKING], check=True, env=luca)
root_register.write_text(text.replace(
    "# §3 · Parking lot\n\n- Nothing qualified yet.\n",
    "# §3 · Parking lot\n\n- Nothing qualified yet.\n"
    "- Should every nightly job retry the same way, or each its own?\n"), encoding="utf-8")
for args in (["commit", "-q", "-am", "a parking line: one retry policy for the nightly jobs?"],
             ["push", "-q", "origin", PARKING], ["switch", "-q", "main"]):
    subprocess.run(["git", "-C", str(D), *args], check=True, env=luca)

# What a code session delivered for the approved CHG-001: `documentazione.md`, what the
# documentation should say, in the folder of the change, waiting for the thread that holds it.
delivery = EXCHANGE / "in-arrivo" / "CHG-001" / "documentazione.md"
delivery.parent.mkdir(parents=True)
delivery.write_text("""\
# CHG-001 · What the documentation should say

The scoring job of atlas now runs in the warehouse, as SQL, and no longer in pandas.

- products/atlas/ARC.md, the target: the scores are a view, `gold.scores`, refreshed at 05:30
  and read by the publication at 06:00, inside the daily SLA.
- products/atlas/ARC.md, the target: the pandas job and its container are gone; nothing else
  reads them.
""", encoding="utf-8")
print(f"fixture written to {D}, with {REMOTE.name} and {EXCHANGE.name} beside it")
