#!/usr/bin/env python3
"""Build `contribute/team` as it stands before its code session: where a launch is measured.

Usage: python additive_launch.py <dest-dir>

From 4.13.0 a change is implemented by a code session that the documentation session launches
on its brief, `exchange.py code`, and launches only on the person's yes. `contribute/team` holds
in its exchange what a code session already delivered for CHG-001, which its cases `todo`,
`delivery` and `join-stops` read: a launch measured there would be the launch of a change whose
code came back. This is the same project, built by `additive.py` into `<dest>`, one step earlier:
nothing in the exchange for CHG-001 -- the brief is written on the thread, once taken --, and
beside the project, as on a machine, the code repository of atlas, `../atlas-backend` -- the name
`product.yaml` gives it --, with its remote, a bare repository at `../atlas-backend.git`, the
default branch set, so that the first call of `code` finds a repository beside the documentation
with an `origin` to fetch and a base to start from. The behaviour runner copies the five,
`beside` on the case `code-launch` in `evals/behaviour/contribute/cases.yaml`.
The code repository and its remote are removed and written again here, as `additive.py` does
with what it writes beside the project.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
D = Path(sys.argv[1])

r = subprocess.run([sys.executable, str(HERE / "additive.py"), str(D)], capture_output=True,
                   text=True)
if r.returncode:
    sys.exit(f"additive.py failed:\n{r.stdout}\n{r.stderr}")

EXCHANGE = D.parent / "_scambio"
CODE, CODE_REMOTE = D.parent / "atlas-backend", D.parent / "atlas-backend.git"

# The exchange one step earlier: nothing for CHG-001. In the additive mode the brief is written on
# the thread, by whoever takes it, naming the change in the thread's worktree, and reviewed there
# before the launch is proposed: a brief written before the thread exists would name the main
# checkout, and the skill would write it again.
shutil.rmtree(EXCHANGE / "in-arrivo" / "CHG-001")

# The code repository of atlas and its remote: the pandas job CHG-001 rewrites, and its test.
for p in (CODE, CODE_REMOTE):
    shutil.rmtree(p, ignore_errors=True)
when = "2026-04-01T09:00:00+02:00"
env = {**os.environ, "GIT_AUTHOR_NAME": "maria", "GIT_AUTHOR_EMAIL": "maria@example.com",
       "GIT_COMMITTER_NAME": "maria", "GIT_COMMITTER_EMAIL": "maria@example.com",
       "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when,
       "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
files = {
    "README.md": "# atlas-backend\n\nThe nightly scoring job of atlas, in pandas.\n",
    "scoring/__init__.py": "",
    "scoring/score.py": '''\
"""The nightly scoring job: reads the features, writes one score per customer.

`run` is the job, in pandas; `score` is the weighting it applies, which the test reads.
"""

WEIGHTS = {"recency": 0.5, "frequency": 0.3, "value": 0.2}


def score(rows):
    """One score per customer: the weighted sum of its features."""
    return {r["customer"]: round(sum(WEIGHTS[k] * r[k] for k in WEIGHTS), 4) for r in rows}


def run(features_path, scores_path):
    """Read the features, score them, write the scores table: once a night, before 06:00."""
    import pandas as pd

    features = pd.read_parquet(features_path)
    scores = score(features.to_dict("records"))
    pd.DataFrame({"customer": list(scores), "score": list(scores.values())}).to_parquet(
        scores_path, index=False)
''',
    "tests/__init__.py": "",
    "tests/test_score.py": '''\
import unittest

from scoring.score import score


class ScoreTest(unittest.TestCase):
    def test_one_score_per_customer(self):
        rows = [{"customer": "a", "recency": 1, "frequency": 0, "value": 0},
                {"customer": "b", "recency": 0, "frequency": 1, "value": 1}]
        self.assertEqual(score(rows), {"a": 0.5, "b": 0.5})
''',
}
for rel, text in files.items():
    (CODE / rel).parent.mkdir(parents=True, exist_ok=True)
    (CODE / rel).write_text(text, encoding="utf-8")
subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(CODE_REMOTE)], check=True,
               env=env)
for args in (["init", "-q", "-b", "main"], ["add", "-A"],
             ["commit", "-q", "-m", "the nightly scoring job, in pandas"],
             ["remote", "add", "origin", "../atlas-backend.git"],
             ["push", "-q", "-u", "origin", "main"],
             ["remote", "set-head", "origin", "main"]):
    subprocess.run(["git", "-C", str(CODE), *args], check=True, env=env)
print(f"fixture written to {D}, with {EXCHANGE.name}, {CODE.name} and {CODE_REMOTE.name} "
      "beside it")
