"""What a living fixture document carries beside its stamp, decided once for every generator.

`LC008` asks a living document reread after its creation for a sentence saying what the
reading covered. Outside a git history the validator decides "after its creation" by the day:
a `last_review` on a day other than `created`. The fixtures under `evals/` are written to
files and not committed, so the same rule decides here which of them owe the sentence, and a
generator that plants no defect there writes it, or the finding it exists to produce arrives
inside a list of unrelated ones. One rule in one place: seven copies of it were written into
six generators on the day the check arrived, which is how a rule stays learned in one place.
"""

from __future__ import annotations

NOTE = "the whole file"


def reread(fields: dict) -> dict:
    """The front matter fields, with `review_scope` where a reading is owed and absent.

    A fixture that writes its own sentence keeps it; one that writes a stamp on the day of
    `created` is a day-one document and owes nothing; an immutable never carries the field.
    """
    if (fields.get("lifecycle") == "living" and "last_review" in fields
            and "review_scope" not in fields
            and str(fields.get("created", ""))[:10] != str(fields.get("last_review", ""))[:10]):
        fields = dict(fields)
        fields["review_scope"] = NOTE
    return fields
