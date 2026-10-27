#!/usr/bin/env python3
"""Build a project in the additive mode, where the prompts of `contribute` are measured.

Usage: python additive.py <dest-dir>

`contribute` says it works only where `.framework/work.yaml` on the main line declares
`mode: additive`, and in any other repository it names the skill the request belongs to and
stops. Its prompts measured in `default`, which is not in the mode, would measure a skill asked
to do what it refuses. This is `audit/clean-repo`, the smallest correct project, put in the mode:
the roles, open entries with the anchors the threads are computed from, and the history the
to-do reads the main line from.

A git repository with one commit and no remote. The to-do reads the main line and the remote
branches the clone has, without the network, so it computes threads here; `work.py`, which
fetches, does not get far. That is the limit of a fixture for triggering, which asks only which
skill answers: the behaviour of `contribute`, which needs the exchange beside the repository,
has no fixture yet. Its review stamps are audit.py's, which move with the calendar.
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
# approved CHG-001 forecasts another, and is a thread of its own. Its stamp is the one audit.py
# gave the register, read rather than restated: those move with the calendar.
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
print(f"fixture written to {D}")
