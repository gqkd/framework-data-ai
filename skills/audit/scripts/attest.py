#!/usr/bin/env python3
"""Attest a reading of a living document, as a person.

    python3 attest.py --root path/to/project products/atlas/PBR.md --scope "the whole file"
    python3 attest.py --root . OPEN.md --scope "the two entries of §3 changed today; not §1, §2 or §4"
    python3 attest.py --root . --commit

THE PROCEDURE IT BELONGS TO, IN THREE STEPS. Commit the content. Run this, once per document
you have reread, with one sentence per document saying what the reading covered. Commit the
attestations on their own: a commit that changes only `last_review` and `review_scope` is a
reading and not a change, and `LC006` steps over it. Several documents attested in one commit
are fine; what separates them is the sentence, not the minute.

`--commit` IS THE THIRD STEP, since 4.12.0. Alone, it commits the files whose only change from
`HEAD` is their attestation block, and nothing else -- a file that changes more is left out and
named, what is staged of other files stays staged --, with a message made of their paths and
their sentences, so that nobody writes it by hand. With a document and `--scope`, it attests
that one first. It writes no stamp of its own, and it checks nothing of who wrote the ones it
commits: that they are a person's holds because it is run once the person has attested.

WHAT IT WRITES, AND WHY THE INSTANT IS THE CLOCK'S. `last_review` becomes the moment this
runs, at the minute, with its offset (`2026-09-25 10:15 +02:00`): an instant and not a wall
clock reading, so that the validator compares instants wherever the tree is validated from.
It is not chosen and it is not the content commit's date. The link to the text that was read
is not in the value: it is the commit that will carry this attestation, whose parent is the
text as it stood, and `git blame` on the line finds both. The content commit is printed here so
that whoever commits knows what they are attesting, and it is not written into the document.
`review_scope` becomes the sentence given, as a plain scalar when it is short and safe and as a
folded block otherwise. Nothing else in the front matter moves: comments, order and spacing
stay where they were, because this edits lines and does not reserialise YAML.

WHAT IT REFUSES, WITH EXIT 2. A root outside any git repository, or a shallow one: the instant
written here is bound to the commit that will carry it, and there has to be a history for that
commit to enter. A document that is not `living`, or not tracked. An empty `--scope`, or the
sentence already in `review_scope`, which `LC008` would report as copied forward. And the one
that matters most: attested text in the working tree or in the index that differs from `HEAD`.
Attesting uncommitted content would bind the reading to a text that no commit holds yet, and
the commit that follows would carry both the change and the stamp, which `LC006` correctly
counts as a change. Commit the content first.

AN AGENT DOES NOT RUN THIS. The rule in `references/preamble.md` is that an agent proposes
`last_review` and never writes it, and this command is the way a person writes it. The
instant it produces is "already in the repository" only in the sense that a clock is: the
fact it records is that a named person finished reading, which no run can supply. A run that
has read a document lists it, offers the sentence for `review_scope`, and stops. `--commit`
alone is the exception, and the reason it exists: it writes no stamp, so the session that used
to write that commit by hand runs it, once the person has attested -- the script does not tell
their stamp from anybody else's.

Requires the same environment as `validate.py`, whose helpers it uses.
"""

from __future__ import annotations

import argparse
import difflib
import re
import sys
import textwrap
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate as v  # noqa: E402  (the validator's helpers, not its main)


PLAIN_SCALAR = re.compile(r"[A-Za-zÀ-ɏ][^:#]*")
# Words YAML reads as something other than a string, and would hand `LC008` as a boolean or
# a null: `review_scope: no` is an empty note to the validator. Written as a block instead.
YAML_WORDS = {"yes", "no", "true", "false", "on", "off", "null", "y", "n", "~"}
INLINE_COMMENT = re.compile(r"\s+#.*$")


def scope_lines(scope: str) -> list[str]:
    """`review_scope` as YAML lines: a plain scalar when that is safe, a folded block otherwise.

    A plain scalar cannot carry `: ` or ` #`, should not start with an indicator or a digit,
    and must not be a word YAML reads as a boolean or a null, so anything longer than a line,
    containing either, or spelled like one of those goes into `>-`, which folds the wrapped
    lines back into one sentence when read.
    """
    if (len(scope) <= 80 and PLAIN_SCALAR.fullmatch(scope)
            and scope.casefold() not in YAML_WORDS):
        return [f"review_scope: {scope}"]
    return ["review_scope: >-"] + ["  " + line for line in textwrap.wrap(scope, 88)]


def rewrite(text: str, stamp: str, scope: str) -> str:
    """The document with its attestation block replaced, and nothing else moved.

    The block is found with the validator's own `attestation_spans`, so what this replaces is
    exactly what `LC006` will step over. A comment on the `last_review` line itself survives
    on the new line: it is text, and the command does not delete text.
    """
    lines = text.split("\n")
    lo, hi = v._front_matter_lines(text)
    if hi == 0:
        raise ValueError("no front matter")
    spans = v.attestation_spans(lines, lo, hi)
    review_at = next((s for s, e in spans if v.REVIEW_KEY.match(lines[s])), None)
    comment = ""
    if review_at is not None:
        m = INLINE_COMMENT.search(lines[review_at])
        comment = m.group(0) if m else ""
    new_block = [f"last_review: {stamp}{comment}"] + scope_lines(scope)
    if review_at is None:
        # No stamp yet (`LC001`): after `created`, or at the end of the front matter.
        created_at = next((i for i in range(lo, hi) if lines[i].startswith("created:")), None)
        at = created_at + 1 if created_at is not None else hi
        drop = {i for s, e in spans for i in range(s, e)}
        kept = [line for i, line in enumerate(lines) if i not in drop]
        at -= sum(1 for i in drop if i < at)
        kept[at:at] = new_block
        return "\n".join(kept)
    out: list[str] = []
    i = 0
    while i < len(lines):
        span = next(((s, e) for s, e in spans if s == i), None)
        if span is None:
            out.append(lines[i])
            i += 1
            continue
        if span[0] == review_at:
            out.extend(new_block)
        i = span[1]                      # the other key's block goes: it is rewritten here
    return "\n".join(out)


def content_commit(repo: v.Repository, rel: str) -> tuple[str, datetime, str] | None:
    """The newest commit that changed the attested text of `rel`, or brought the file in.

    Found by the walk `LC006` uses, so the commit named here is the one a finding would name.
    """
    change = v.last_text_change(repo, rel)
    if change is None:
        return None
    sha, when, kind = change
    return sha, when, {"born": "brought the file into the history",
                       "merge": "put two versions of it together (a merge)"}.get(
                           kind, "last changed its text")


def refuse_in_a_merge(root: Path) -> None:
    """NOT IN THE MIDDLE OF A MERGE. The stamp would be written into the merge commit, which
    records no reading: `LC006` counts what a merge produced as a change at the merge's own
    instant, so the reading would be reported as not done. Finish the merge, then attest."""
    merging = v._git(["rev-parse", "--verify", "-q", "MERGE_HEAD"], root)
    if merging is not None and merging.returncode == 0:
        v.refuse("a merge is in progress. Commit it first -- `work.py sync --continue`, or "
                 "`git commit` -- then reread and attest: a stamp written into a merge commit "
                 "is not a reading, because a merge records none.")


def attestations_only(root: Path, repo: v.Repository) -> tuple[list[tuple[str, str]], list[str]]:
    """The tracked files whose only change from `HEAD` is the attestation block, each with its
    `review_scope` sentence; and the changed files that change more, which are not committed.

    The working tree is what `git commit --only` takes, so it is what is read: a file whose
    text differs from `HEAD` anywhere outside the block is a change and not a reading, as
    `LC006` would count it, and stays out.

    `--relative`, OR A DOCUMENTATION IN A SUBFOLDER COMMITS NOTHING: git names the changed
    files from the top of the repository, and the paths read here, and given to the commit, are
    the project's, as `Repository.blob` takes them. A file that is not text is a change too."""
    changed = v._git(["diff", "--name-only", "-z", "--relative", "HEAD"], root)
    if changed is None or changed.returncode != 0:
        v.refuse("git could not say which files differ from HEAD. Nothing is committed.")
    readings: list[tuple[str, str]] = []
    others: list[str] = []
    for rel in sorted(r for r in changed.stdout.split("\0") if r):
        path = root / rel
        head = repo.blob("HEAD", rel)
        try:
            text = path.read_text(encoding="utf-8") if path.is_file() else None
        except (OSError, UnicodeDecodeError):
            text = None
        if head is None or text is None:
            others.append(rel)
            continue
        meta, _, err = v.parse_front_matter(text)
        same = v.split_attestation(text)[0] == v.split_attestation(head)[0]
        scope = " ".join(str((meta or {}).get("review_scope") or "").split())
        if err or meta is None or meta.get("lifecycle") != "living" or not same or not scope:
            others.append(rel)
            continue
        readings.append((rel, scope))
    return readings, others


def commit_attestations(root: Path, repo: v.Repository) -> None:
    """Commit the attestations written and not committed, on their own, with a message made of
    their paths and sentences. Exit 2 when there is none: an empty commit records no reading."""
    readings, others = attestations_only(root, repo)
    if not readings:
        v.refuse("no file differs from HEAD only in `last_review` and `review_scope`: there is no "
                 "attestation to commit. Attest first, one document at a time, then `--commit`."
                 + (f" Changed, and more than their attestation: {', '.join(others)}."
                    if others else ""))
    title = (f"Attest the reading of {readings[0][0]}" if len(readings) == 1
             else f"Attest the readings of {len(readings)} documents")
    body = "\n".join(f"- {rel}: {scope}" for rel, scope in readings)
    message = (f"{title}\n\n{body}\n\nOnly `last_review` and `review_scope` change: a reading, "
               "not a change.\n")
    r = v._git(["commit", "-q", "--only", "-m", message, "--", *(rel for rel, _ in readings)],
               root)
    if r is None or r.returncode != 0:
        v.refuse("git refused the commit: "
                 + ((r.stderr or r.stdout).strip() if r is not None else "git did not run")
                 + ". Nothing is committed.")
    sha = v._git(["rev-parse", "--short=12", "HEAD"], root)
    print(f"Committed {sha.stdout.strip() if sha is not None else 'the attestations'}: {title}.")
    for rel, scope in readings:
        print(f"  {rel}: {scope}")
    if others:
        print("Not committed, because they change more than their attestation: "
              + ", ".join(others) + ".")


def main() -> int:
    ap = argparse.ArgumentParser(description="Attest a reading of a living document")
    ap.add_argument("--root", default=".", type=Path,
                    help="the project being attested, not the framework")
    ap.add_argument("document", type=Path, nargs="?",
                    help="the living document you have just reread")
    ap.add_argument("--scope",
                    help="one sentence: what the reading covered, and what it did not")
    ap.add_argument("--commit", action="store_true",
                    help="commit, on their own, the attestations written and not committed, "
                         "with a message made of their paths and sentences")
    args = ap.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        v.refuse(f"{root}: no such directory. `--root` is the project being attested.")
    if args.document is None:
        if not args.commit:
            ap.error("a document with --scope, or --commit")
        if args.scope is not None:
            ap.error("--scope goes with the document it attests")
        repo = v.Repository.open(root)       # exits 2 on a shallow or unreadable history
        if repo is None:
            v.refuse(f"{root} is not inside a git repository: there is nothing to commit to.")
        refuse_in_a_merge(root)
        commit_attestations(root, repo)
        repo.close()
        return 0
    if args.scope is None:
        ap.error("--scope is required with a document")
    doc = args.document if args.document.is_absolute() else root / args.document
    doc = doc.resolve()
    try:
        rel = doc.relative_to(root).as_posix()
    except ValueError:
        v.refuse(f"{doc} is not under {root}.")
    if not doc.is_file():
        v.refuse(f"{rel}: no such file under {root}.")
    scope = " ".join(args.scope.split())
    if not scope:
        v.refuse("`--scope` is empty. The sentence is the attestation: what did the reading "
                 "cover, and what did it not? Without it the stamp is a stamp, and `LC008` "
                 "says so.")

    repo = v.Repository.open(root)           # exits 2 on a shallow or unreadable history
    if repo is None:
        v.refuse(f"{root} is not inside a git repository. The instant written here is bound "
                 "to the commit that will carry it, and there is no history for that commit "
                 "to enter.")

    refuse_in_a_merge(root)

    text = doc.read_text(encoding="utf-8")
    meta, _, err = v.parse_front_matter(text)
    if err or meta is None:
        v.refuse(f"{rel}: {err or 'no front matter'}. Only a living document is attested.")
    if meta.get("lifecycle") != "living":
        v.refuse(f"{rel} is `{meta.get('lifecycle')}`, not `living`. An immutable is not "
                 "reviewed, it is superseded; there is nothing to attest.")
    if not repo.is_tracked(rel):
        v.refuse(f"{rel} is not tracked. Commit the content first: the reading is attested "
                 "over the text as committed, and this file has no committed text.")
    head = repo.blob("HEAD", rel)
    if head is None:
        v.refuse(f"{rel} is tracked but has no committed version. Commit the content first.")
    staged = repo.blob("", rel)          # `:path` is the index
    for where, version in (("the working tree", text), ("the index", staged)):
        if version is not None and v.split_attestation(version)[0] != v.split_attestation(head)[0]:
            v.refuse(f"{rel}: the attested text in {where} differs from HEAD. Commit the "
                     "content first, then attest. The instant written here covers the text as "
                     "committed and nothing else; a commit carrying both the change and the "
                     "stamp is counted by `LC006` as a change, correctly.")
    if " ".join(str(meta.get("review_scope") or "").split()).casefold() == scope.casefold():
        v.refuse(f"{rel}: `--scope` is the sentence already there. `LC008` would report the "
                 "note copied forward, because the same sentence describes two readings. A "
                 "reading that covered the same parts still happened at another time, over "
                 "text that had a chance to change: say so in the sentence.")

    attests = content_commit(repo, rel)
    now = datetime.now().astimezone().replace(second=0, microsecond=0)
    stamp = f"{now:%Y-%m-%d %H:%M} {v._offset(now)}"
    new_text = rewrite(text, stamp, scope)
    doc.write_text(new_text, encoding="utf-8")
    repo.close()

    diff = difflib.unified_diff(text.split("\n"), new_text.split("\n"),
                                fromfile=f"a/{rel}", tofile=f"b/{rel}", lineterm="")
    print("\n".join(diff))
    if attests is not None:
        sha, when, what = attests
        print(f"\n{rel}: attests the text as of commit {sha[:12]} "
              f"({when:%Y-%m-%d %H:%M} {v._offset(when)}), which {what}. The commit is not "
              "written into the document: the attestation commit and its parent carry it.")
    if args.commit:
        repo = v.Repository.open(root)
        commit_attestations(root, repo)
        repo.close()
        return 0
    print("Nothing is committed. Commit the attestations on their own -- `--commit` does it, "
          "after the last one: a commit that changes only `last_review` and `review_scope` is a "
          "reading, not a change. No derived view needs regenerating: none of them carries "
          "`last_review`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
