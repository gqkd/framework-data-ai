"""What `--adopt` clears by writing a number, and what it refuses to write over.

`migrate.py` refuses to adopt while NEW is non-empty, which is right: the number it
writes is the claim that the migration is done. `FW001`/`FW002`/`FW003` are excluded
because `--adopt` is the only thing that clears them, and their absence from that list
once deadlocked every project that pinned.

The same deadlock returned one level up and nothing here saw it: a repository that asks
for `require_all` gets an `AN003` for each of those warnings, and `AN003` was not on the
list. The adoption that would have removed the subject was refused by the annotation
about it. These are the cases that were missing on 19/09/2026.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "_migrate_under_test", ROOT / "skills/audit/scripts/migrate.py")
migrate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(migrate)


def finding(code: str, message: str = "") -> dict:
    return {"code": code, "path": "framework.yaml", "level": "warn", "message": message}


class AdoptClears(unittest.TestCase):

    def test_the_version_line_itself_is_not_migration_work(self):
        for code in ("FW001", "FW002", "FW003"):
            self.assertTrue(migrate.adopt_clears(finding(code, "declares an older version")))

    def test_an_annotation_about_the_version_line_is_cleared_with_it(self):
        # The regression. Without this the adoption is refused by a finding that exists
        # only because the adoption has not happened, and the two ways out are to annotate
        # something about to vanish -- reported as AN001 next run -- or to stop asking for
        # all annotations. Both punish the project for taking the framework seriously.
        for code in ("FW001", "FW002", "FW003"):
            f = finding("AN003", f"[{code}] carries no annotation, and this repository "
                                 "asked for all of them with `require_all`")
            self.assertTrue(migrate.adopt_clears(f), code)

    def test_an_annotation_about_anything_else_is_still_outstanding_work(self):
        f = finding("AN003", "[REG014] carries no annotation, and this repository "
                             "asked for all of them with `require_all`")
        self.assertFalse(migrate.adopt_clears(f))

    def test_an_ordinary_finding_is_not_cleared_by_writing_a_number(self):
        for code in ("REG014", "REG016", "VER002", "XP003", "AN001"):
            self.assertFalse(migrate.adopt_clears(finding(code, "something to repair")))

    def test_a_message_that_merely_mentions_a_code_is_not_a_subject(self):
        # The subject is named at the head, in brackets. Prose that happens to contain
        # FW003 further along is not an annotation about it.
        f = finding("AN003", "carries no annotation; see FW003 for the pin")
        self.assertFalse(migrate.adopt_clears(f))

    def test_an_empty_or_absent_message_does_not_crash_the_rule(self):
        self.assertFalse(migrate.adopt_clears({"code": "AN003"}))
        self.assertFalse(migrate.adopt_clears(finding("AN003", "")))


if __name__ == "__main__":
    unittest.main()
