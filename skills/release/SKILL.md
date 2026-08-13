---
name: release
description: >
  Close a development cycle and prepare a release: check the release gate by comparing the
  evaluation report against the frozen evaluation plan, generate the machine-readable
  release manifest and the human release note, and open the first observation window. Use
  when a release candidate is ready or when asked whether it can ship. Triggers on
  "possiamo rilasciare", "prepariamo la release", "siamo pronti per il rilascio", "chiudiamo
  il ciclo", "fai la release", "genera il manifest", "can we release", "prepare the
  release", "are we ready to ship", "cut a release". Use it also when someone asks why a
  release is blocked.
---

# release

Read `references/preamble.md`, which sits at `${CLAUDE_PLUGIN_ROOT}`, first.

This is the skill with the lowest share of judgment and therefore the one that saves the
most time at equal risk. Almost everything here is assembled from documents and from git.
The one thing that is not mechanical is the gate, and the gate is the point.

## Step 1 · The release gate

`RG` is not a lifecycle gate crossed once. It is a pipeline control that fires at every
release candidate, the first one included.

Check, in order:

1. **An `EVR` exists** for this candidate.
2. **It cites the `EVP` in the version frozen at RC time**, through `evp_version` and
   `evp_hash`. The freeze is the whole mechanism: it is what makes it impossible to adjust
   the thresholds after seeing the results.
3. **The cited hash is the hash of the plan you are about to read.** Citing it is not
   checking it. Recompute it and compare:

   ```bash
   sha256sum products/<p>/EVP.md          # or: shasum -a 256
   ```

   If it differs, the `EVP` on disk is not the one this candidate was measured against, and
   the thresholds in front of you are not the ones that count. Do not judge against them.
   Recover the frozen plan from the commit in `frozen_at` and use that:

   ```bash
   git show <frozen_at>:products/<p>/EVP.md
   ```

   A mismatch is not by itself dishonest: a review that only touched `last_review` moves the
   hash too. It is still disqualifying for this candidate, and which of the two it was shows
   in one `git diff`. Say which.
4. **Every metric and every slice is at or better than its threshold**, judged against the
   list in the frozen `EVP`, not the list the report chose to print. *Better* has a
   direction and the `EVP` states it: for a maximum such as latency, cost or hallucination
   rate, better is lower. A report may show metrics the plan never asked for, and they are
   not evidence for this gate no matter how good they look. A metric the plan requires and
   the report omits is a fail, not an absence: you cannot establish something you were not
   shown. Exactly on the threshold passes.
5. **Only the metrics the plan says block, block.** The `EVP` carries that column and it is
   a decision somebody took while the outcome was still unknown, which is the only moment
   it can honestly be taken. A cost ceiling is often deliberately not blocking: worth
   knowing, not worth stopping a release for. Blocking on it anyway is the same failure as
   waving a breach through, in the direction nobody complains about, and it teaches people
   that the gate is noise. Report every breach; block on the ones the plan says to.
6. **Slices matter as much as aggregates.** A model that clears the overall threshold while
   failing on one segment is a model that fails for the people in that segment.
7. **`verified_code`** names the commit of each repository the evaluation ran on, keyed
   the way `code:` is keyed. `frozen_at` is not the same field and does not answer this: it
   is the commit of *this* repository holding the plan, which is what the `git show` above
   needs. They were one field, and the two lines of this document that used it disagreed
   about which it was — which only looked like one question while documents and code shared
   a repository. Every repository marked `release_relevant` has to carry a commit here:
   `VER002` reports the ones that do not, because an attestation covering part of a system
   reads exactly like one covering all of it.

If any of these is missing or below threshold, the outcome is **rework, not rollback**, and
use that word. Nothing has been deployed yet, so there is nothing to roll back. Rollback
only exists after a deployment, when regressions show up in production, and that path
re-enters through `LOG` and change intake.

**Never lower a threshold to clear the gate.** If a threshold turns out to be wrong, that is
a decision with a reason, recorded in a `DEC`, taken *before* the next candidate, never
between seeing the results and shipping. The `EVP` frozen at RC time is the one that counts
for this candidate.

If `evp_hash` cannot be established, say so and stop. Do not compute a hash of the current
`EVP` and present it as the frozen one: that turns the one piece of evidence the gate rests
on into a decoration.

**Read the numbers, not the verdict column.** An `EVR` states its own outcome per metric and
that column is the author's claim, not the check. Compare each result against the frozen
threshold yourself. The failure this catches is not usually a forged `pass`: it is a row
worded so that no word in it is false and no reader stops, `0.812 against a 0.85 threshold`
sitting at the bottom of a table of excellent numbers the plan never asked for.

## Step 2 · The manifest

`RLM-NNN.yaml` is the same release in machine-readable form, and it is the document that
matters at the one moment nobody has time to read prose. Assemble it from git, the build and
the configuration:

commit and digest · model, prompt and dataset versions · the `DC` touched · the `CHG`
included · the `EVR` · the **rollback target** and whether it has been tested.

It carries `generated_by`, not `owners`. Nobody writes this file by hand, and naming a
person to ask about it would be fiction. Filling it in by hand is how it comes out wrong.

Two things the validator will tell you and that are worth getting right rather than
silencing: an empty `rollback.target` makes the manifest useless at the one moment it exists
for, and `rollback.tested: false` means the procedure is an intention rather than a
procedure. If it has not been tested, say so plainly rather than marking it true.

## Step 3 · The release note

`REL-NNN.md`, for a person. Ten lines. Generated from the `CHG` included, **translated into
effects**: not "changed the retrieval index" but what somebody using the product will now
experience. The note and the manifest are the same release for two different readers, and
neither substitutes for the other.

## Step 4 · Close the loop

- Update `product.yaml`.
- Open a `SIG` in `LOG` of type `metric` for the first observation window, so that the
  question "did it behave as expected in production" has somewhere to be answered rather
  than being remembered.
- Move the included `CHG` to `status: verified`.

## What you must not do

**Do not run the deploy.** This skill prepares the evidence. The command is the user's. The
separation is deliberate: the moment a release skill can deploy, the gate becomes something
to get past rather than something to pass.

**Do not write a `REL` without an `RLM`.** The ten line note serves a person and is not
enough for an agent and not enough for a rollback. Producing only the readable half is how a
rollback becomes an archaeology exercise at the worst possible moment.

**Do not treat a failed gate as a formality.** A gate that leaves no written trace is not a
gate, it is a meeting. If the outcome is rework, say what failed, against which threshold,
and what has to change.

## Handing back

Say whether the gate passed, on which evidence, what was generated, and what is left for the
user to run. If the gate did not pass, lead with that and with the specific metric and slice
that failed. Then run the validator.

**Then the two closing blocks the preamble describes, and they go last:** what changed in
plain words, one line per file, and what to do next with what each option buys and costs. Here
the top row is a command that is yours to run and not mine — the deploy — and on a failed gate
it is the rework, with the threshold that was missed written next to it.
