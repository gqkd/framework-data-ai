#!/usr/bin/env python3
"""Make `ordering-b` the same register as `ordering-a`, read in a different order.

The stability question is whether the skill ranks the entries or reproduces the sequence it
found them in, and two identical fixtures cannot tell those apart: they were byte identical,
so the test could not have failed however the skill behaved.

Only the order of entries inside a section changes. Nothing else may: the heading an entry
sits under is itself a claim about its cost, and two entries here contradict theirs on
purpose (OD-009 is filed LOW and declares high, OD-001 is filed HIGH and declares medium).
Moving those would delete the trap rather than reorder it.

The permutation is chosen, not random: the entry that should be worked first (OD-002, high
cost with no default in force) stops being the first one read, and OD-001, which belongs
seventh, becomes the first. An agent echoing file order now produces a visibly wrong answer.
"""
import re, shutil, sys
from pathlib import Path

ROOT = Path(sys.argv[1])   # a directory holding ordering-a; see make.py
A, B = ROOT / "ordering-a", ROOT / "ordering-b"

ORDER = {"HIGH":   ["OD-001", "OD-007", "OD-002", "OD-004", "OD-005"],
         "MEDIUM": ["OD-003", "OD-008"],
         "LOW":    ["OD-009", "OD-006"]}

def shuffle(text: str) -> str:
    out, section = [], None
    # Split into: everything up to the first section, then (heading, entries) per section.
    parts = re.split(r"(?m)^(## Cost to reverse (HIGH|MEDIUM|LOW)[^\n]*\n)", text)
    out.append(parts[0])
    for i in range(1, len(parts), 3):
        heading, section, body = parts[i], parts[i + 1], parts[i + 2]
        # Entries run from a `### OD-` heading to the next `###`/`#` or end of section.
        chunks = re.split(r"(?m)(?=^### OD-)", body)
        head, entries = chunks[0], chunks[1:]
        tail = ""
        if entries:
            m = re.search(r"(?m)^#(?!##)", entries[-1])          # `# §2 ...` starts the next part
            if m:
                entries[-1], tail = entries[-1][:m.start()], entries[-1][m.start():]
        by_id = {re.match(r"### (OD-\d+)", e).group(1): e for e in entries}
        want = ORDER[section]
        if set(want) != set(by_id):
            sys.exit(f"{section}: fixture holds {sorted(by_id)}, permutation names {sorted(want)}")
        out += [heading, head] + [by_id[i] for i in want] + [tail]
    return "".join(out)

shutil.rmtree(B, ignore_errors=True)
shutil.copytree(A, B)
src = (A / "OPEN.md").read_text(encoding="utf-8")
dst = shuffle(src)
(B / "OPEN.md").write_text(dst, encoding="utf-8")

a_ids = re.findall(r"^### (OD-\d+)", src, re.M)
b_ids = re.findall(r"^### (OD-\d+)", dst, re.M)
assert sorted(a_ids) == sorted(b_ids), "an entry was lost or duplicated"
assert a_ids != b_ids, "the order did not actually change"
assert len(src) == len(dst), "the shuffle changed the content, not just the order"
print("ordering-a:", " ".join(a_ids))
print("ordering-b:", " ".join(b_ids))
