#!/usr/bin/env python3
"""Adopting a new version of the framework, as a difference rather than as an announcement.

`FW001` tells a repository that the rules moved. It does not tell it *which of the findings
in front of it moved with them*, and that is the whole question: one of them is a migration
and the other is a repair, they want opposite responses, and guessing wrong at it a few
times is how a validator stops being read.

So this runs both validators on the same project -- the one from the version the project
declares, and the one from the version it is moving to -- and splits the findings three
ways:

    already there      reported by both. Documents to repair. Not migration work.
    new                reported only by the new validator. This is the migration.
    gone               reported only by the old one. Cleared by the move.

The old validator is not kept anywhere: it is reconstructed from this repository's git
history, at the commit where `schemas/artifact-types.yaml` last declared the version the
project pinned. That is why no tag is needed and why nothing has to have been released:
the history is the archive.

The migration notes are not restated here either. They live beside the number they explain,
in the registry, and this reads them out of it -- so there is one copy, and it is the one
whoever bumps the version has to write.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("Needs pyyaml:  pip install pyyaml")

FRAMEWORK = Path(__file__).resolve().parents[3]
REGISTRY_REL = "schemas/artifact-types.yaml"
VALIDATE_REL = "skills/audit/scripts/validate.py"

# The two findings `--adopt` clears by writing the number, rather than by anybody editing a
# document. They are not migration work and are not repairs: they are the migration itself,
# stated as a finding.
ADOPT_CLEARS = ("FW001", "FW002")

SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
VERSION_LINE = re.compile(r"^version:\s*['\"]?(\d[\d.]*)", re.M)
# `# 2.0.0 -> 2.1.0.` and the one that opens the history, `# 1 -> 1.1.0.`
NOTE_OPENS = re.compile(r"^#\s*(\d[\d.]*)\s*->\s*(\d+\.\d+\.\d+)\.")


def semver(v):
    m = SEMVER.match(str(v).strip())
    return tuple(int(g) for g in m.groups()) if m else None


def git(args, cwd, **kw):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, **kw)


def declared_version(root: Path):
    """What the project says it was written against, where it says it, and why not.

    The third return value is what this used to lack. A `framework.yaml` that does not parse
    came back out of here as a `yaml` traceback -- the tool died on the one file it exists to
    read, having said nothing about the project -- and a file with no `framework_version` in
    it came back indistinguishable from a file that is not valid YAML at all. They are
    different repairs.
    """
    cfg = root / "framework.yaml"
    if not cfg.exists():
        return None, cfg, None
    try:
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        first = str(e).strip().splitlines()[0]
        return None, cfg, (f"{cfg} does not parse as YAML: {first}. Nothing can be read out "
                           "of it, including which version this repository was written "
                           "against, and the validator will stop on the same line.")
    if not isinstance(data, dict):
        return None, cfg, f"{cfg}: the top level has to be a mapping."
    return data.get("framework_version"), cfg, None


def registry_version(text: str):
    m = VERSION_LINE.search(text)
    return m.group(1) if m else None


def migration_notes(text: str) -> list[tuple[str, str, str]]:
    """Every `X -> Y` note in the registry, as (from, to, prose).

    They are comments, which is the right place for them -- beside the number they explain,
    in the file that defines it -- and the cost is that they have to be read out rather than
    parsed. A note runs from its opening line until the comment block ends or the next note
    opens.
    """
    notes, cur = [], None
    for line in text.splitlines():
        m = NOTE_OPENS.match(line)
        if m:
            if cur:
                notes.append(cur)
            cur = [m.group(1), m.group(2), line.lstrip("# ").rstrip()]
            continue
        if cur is None:
            continue
        if line.startswith("#"):
            cur[2] += "\n" + line.lstrip("#").strip()
        else:
            notes.append(cur)
            cur = None
    if cur:
        notes.append(cur)
    return [tuple(n) for n in notes]


def commit_declaring(version: str, framework: Path):
    """The newest framework commit whose registry declared `version`.

    Newest and not oldest: a version is current from the commit that introduced it until
    the one that replaced it, and the validator a project has been running all along is the
    last one that shipped under that number, not the first.
    """
    # Asked before the log, because git's own answer to "not a repository" is
    # `Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set)`, which
    # names neither the directory nor what is wrong with it. A framework unpacked from an
    # archive rather than cloned is a real way to arrive here, and the whole comparison
    # rests on the history being present.
    if git(["rev-parse", "--git-dir"], framework).returncode != 0:
        return None, (f"{framework} is not a git checkout, so the validator of {version} "
                      "cannot be reconstructed: this tool reads it out of the framework's "
                      "own history. Point --framework at a clone. The migration notes above "
                      "are still the ones for this move.")

    log = git(["log", "--follow", "--format=%H", "--", REGISTRY_REL], framework)
    if log.returncode != 0:
        tail = log.stderr.strip().splitlines()
        return None, f"git could not read the history of {REGISTRY_REL}: " + (
            tail[-1] if tail else "no reason given")
    for sha in log.stdout.split():
        show = git(["show", f"{sha}:{REGISTRY_REL}"], framework)
        if show.returncode == 0 and registry_version(show.stdout) == version:
            return sha, None
    return None, (f"no commit of {REGISTRY_REL} ever declared {version!r}. Either the "
                  "project pins a version this checkout does not contain, or its history "
                  "is shallow: `git fetch --unshallow` and try again")


def export(sha: str, framework: Path, into: Path) -> Path:
    """That commit's whole tree, so the old validator finds its own schemas and catalog."""
    archive = into / "old.tar"
    with archive.open("wb") as fh:
        r = subprocess.run(["git", "archive", sha], cwd=framework, stdout=fh,
                           stderr=subprocess.PIPE, text=False)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode(errors="replace").strip())
    tree = into / "old"
    tree.mkdir()
    with tarfile.open(archive) as tar:
        # `filter="data"` is the default from 3.14 and a DeprecationWarning before it. Named
        # rather than left implicit so this prints nothing on 3.12, which is what CI runs:
        # a migration tool whose first output is a warning about itself gets distrusted
        # before it has said anything.
        tar.extractall(tree, filter="data")
    archive.unlink()
    return tree


def key(f: dict, seen: Counter) -> tuple:
    """What identifies one finding across two versions of the validator.

    (code, path) and not the message: a reworded message is a PATCH by this framework's own
    definition, and a diff that treated it as a new finding would report the whole
    repository as migration work the first time somebody fixed a sentence.

    The ordinal is what stops that from swallowing the interesting case. A check can report
    the same code on the same file many times -- one per entry of a register, one per
    unresolved citation -- and keyed on the pair alone, three findings and five findings are
    the same key: a version that made a check twice as noisy on a file it already reported
    would come out of this tool as "nothing new". Counting them keeps the two extra ones
    visible without making the diff sensitive to wording.
    """
    k = (f["code"], f["path"])
    seen[k] += 1
    return (*k, seen[k])


def findings(validator: Path, root: Path) -> dict:
    """One validator's report on the project, keyed by `key`."""
    r = subprocess.run([sys.executable, str(validator), "--root", str(root), "--json"],
                       capture_output=True, text=True)
    if r.returncode not in (0, 1) or not r.stdout.strip():
        tail = (r.stderr or r.stdout).strip().splitlines()
        raise RuntimeError(tail[-1] if tail else "no output")
    out = json.loads(r.stdout)
    seen: Counter = Counter()
    return {key(f, seen): f for f in out["findings"]}


def adopt(cfg: Path, version: str, commit: str | None) -> None:
    """Write the new number, and the pinned commit beside it when there is one.

    Both or neither, and that is the point of doing it here. A project that pins moves two
    facts at once; a migration that moved one of them would leave the pin naming the version
    it just stopped running, which `FW003` then reports for the rest of the week. The pin is
    only rewritten when the file already carries one: adding it to a project that never asked
    for it would be this tool taking a decision that costs a deliberate bump per fix.

    A rewrite through yaml.safe_dump would drop every comment in a project's own
    configuration, including the ones explaining why a check is switched off -- which is
    the reasoning this framework asks people to write down.
    """
    # Quoted, always. A bare `2.7` is a decimal to YAML and a bare `3` a whole number,
    # and `FW001` reports both as unusable -- which would be this tool writing the
    # finding it exists to clear.
    declared = f'framework_version: "{version}"'
    if not cfg.exists():
        cfg.write_text(declared + "\n", encoding="utf-8")
        return
    text = cfg.read_text(encoding="utf-8")
    line = re.compile(r"^framework_version:.*$", re.M)
    text = (line.sub(declared, text, count=1) if line.search(text)
            else declared + "\n" + text)
    pin = re.compile(r"^framework_commit:.*$", re.M)
    if commit and pin.search(text):
        text = pin.sub(f'framework_commit: "{commit}"', text, count=1)
    cfg.write_text(text, encoding="utf-8")


def verdict(report: dict) -> int:
    """0 when there is nothing left to do, 1 when there is.

    An adopted migration is nothing left to do even though it reported findings a moment
    ago: they were the reason to run it.
    """
    if report.get("adopted") or report["up_to_date"]:
        return 0
    return 1 if report["new"] or report["version_line"] or report["problems"] else 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compare a project against two versions of the framework")
    ap.add_argument("--root", default=".", type=Path, help="the project, not the framework")
    ap.add_argument("--framework", default=FRAMEWORK, type=Path,
                    help="the framework checkout to migrate towards")
    ap.add_argument("--from", dest="from_version",
                    help="override the version in the project's framework.yaml")
    ap.add_argument("--adopt", action="store_true",
                    help="write the new framework_version into the project")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root, framework = args.root.resolve(), args.framework.resolve()
    # Both are checked before anything is read, and they are checked apart: pointed at a
    # project that is not there, this reported "declares no framework_version" about a
    # `framework.yaml` inside a directory that does not exist, which sends somebody to write
    # a line into a file they cannot open.
    if not root.is_dir():
        sys.exit(f"{root}: no such directory. `--root` is the project being migrated.")
    if not (framework / REGISTRY_REL).exists():
        sys.exit(f"{framework}: no {REGISTRY_REL} here, so this is not a checkout of the "
                 "framework. `--framework` is the definition, `--root` is the project.")

    registry = (framework / REGISTRY_REL).read_text(encoding="utf-8")
    current = registry_version(registry)
    declared, cfg, unreadable = declared_version(root)
    declared = args.from_version or declared

    report = {"project": str(root), "declared": declared, "current": current,
              "up_to_date": False, "notes": [], "already_there": [], "new": [], "gone": [],
              "version_line": [], "problems": []}

    if unreadable and not args.from_version:
        report["problems"].append(unreadable)
    elif declared is None:
        report["problems"].append(
            f"{cfg} declares no `framework_version`, so there is no version to migrate "
            "from. That is `FW002`, and the repair is to write the number the project has "
            "actually been validating against -- not today's, unless it really is.")
    elif semver(declared) is None:
        report["problems"].append(
            f"the project declares {declared!r}, which is not three numbers separated by "
            "dots. `2` and `1.1` are a whole number and a decimal to YAML, and neither "
            "compares with a version. Quote it, or complete it.")
    elif semver(declared) == semver(current):
        # Not a problem, and the distinction is the exit code. A repository already on the
        # current version is the state every repository is supposed to end up in, and a tool
        # that returns 1 for it cannot be put in a pipeline: the run that says "nothing to
        # do" and the run that says "the history is shallow and I could not compare" would
        # be indistinguishable to whoever wired it up.
        report["up_to_date"] = True
    elif semver(declared) > semver(current):
        report["problems"].append(
            f"the project declares {declared} and this checkout is {current}: it is ahead "
            "of the framework it is being pointed at, which usually means `--framework` "
            "points at a stale checkout.")

    if declared and semver(declared) and semver(declared) < (semver(current) or (0, 0, 0)):
        lo, hi = semver(declared), semver(current)
        for frm, to, prose in migration_notes(registry):
            if semver(to) and lo < semver(to) <= hi:
                report["notes"].append({"from": frm, "to": to, "note": prose})

        sha, why = commit_declaring(declared, framework)
        if sha is None:
            report["problems"].append(why)
        else:
            with tempfile.TemporaryDirectory() as tmp:
                try:
                    old_tree = export(sha, framework, Path(tmp))
                    old = findings(old_tree / VALIDATE_REL, root)
                    new = findings(framework / VALIDATE_REL, root)
                except (RuntimeError, OSError) as e:
                    report["problems"].append(f"could not run the {declared} validator: {e}")
                else:
                    report["commit"] = sha[:12]
                    for k in sorted(set(old) | set(new)):
                        f = new.get(k) or old[k]
                        # `FW001` and `FW002` are about the number this tool exists to move.
                        # They are new by construction on every migration, and what clears
                        # them is `--adopt` rather than an edit to any document -- so filing
                        # them under "this is the migration work" told the reader to go and
                        # fix something, while `--adopt` was ignoring them. One of the two
                        # was lying, and it was the report.
                        where = ("version_line" if f["code"] in ADOPT_CLEARS
                                 else "already_there" if k in old and k in new
                                 else "new" if k in new else "gone")
                        report[where].append(
                            {"code": f["code"], "path": f["path"], "level": f["level"],
                             "message": f["message"]})
                finally:
                    shutil.rmtree(Path(tmp) / "old", ignore_errors=True)

    if args.adopt:
        if report["new"] or report["problems"]:
            report["problems"].append(
                "not adopted. `--adopt` writes the new number, which is the claim that the "
                "migration is done; do it after the findings under NEW are gone.")
        else:
            head = git(["rev-parse", "HEAD"], framework)
            commit = head.stdout.strip() if head.returncode == 0 else None
            adopt(cfg, current, commit)
            report["adopted"] = current

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return verdict(report)

    print(f"Project:   {root}")
    print(f"Declared:  {declared}")
    print(f"Framework: {current}" + (f"  (old validator from {report['commit']})"
                                     if report.get("commit") else ""))
    if report["up_to_date"]:
        print(f"\nAlready on {current}: nothing to migrate.")
    for p in report["problems"]:
        print(f"\n! {p}")
    if report["notes"]:
        print("\n-- WHAT MOVED " + "-" * 40)
        for n in report["notes"]:
            print(f"\n{n['note']}")
    for key, label, why in (
            ("new", "NEW: reported only by the new validator",
             "this is the migration work"),
            ("version_line", "THE VERSION LINE ITSELF",
             "not a document to repair: `--adopt` writes it, once NEW is empty"),
            ("already_there", "ALREADY THERE: reported by both",
             "documents to repair, unrelated to the version"),
            ("gone", "GONE: reported only by the old one",
             "cleared by the move, nothing to do")):
        group = report[key]
        if not group:
            continue
        print(f"\n-- {label} ({len(group)}) " + "-" * 20)
        print(f"   {why}")
        for f in group:
            print(f"   [{f['code']}] {f['path']}\n       {f['message'].splitlines()[0]}")
    if report.get("adopted"):
        print(f"\nAdopted: {cfg} now declares {report['adopted']}")
    print()
    return verdict(report)


if __name__ == "__main__":
    sys.exit(main())
