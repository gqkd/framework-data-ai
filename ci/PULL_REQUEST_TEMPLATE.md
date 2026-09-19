<!--
Copy this file to `.github/PULL_REQUEST_TEMPLATE.md` in the project, not in the framework.
The only line the check reads is the one naming the change contract. Everything else here
is for the person reviewing in the legacy profile. The strict-contribution profile reads
mandates from independent CI-selected Git history; PR text cannot supply trusted inputs.
-->

## Change contract

<!-- The identifier, `CHG-NNN`. More than one is fine. -->

CHG-

<!--
No contract for this change set? Then say so, with the reason, on one line, and delete the
field above:

    no-chg: typo in a comment

A reason is required. It is read by whoever reviews this and it stays in the history: that
is what makes it an exception rather than a way around the check.
-->

## What changes

<!-- The observable behaviour after the merge. Not the files: the effect. -->

## What must NOT change

<!--
Copy it from field 2 of the `CHG`, or say "as CHG-NNN §2". This is the field that makes the
contract useful, and it is the one no check can defend: the validator can see that the
contract exists and that it is approved. Whether this change set stayed inside it is what
the review is for.
-->

## Evidence

<!--
Tests, the eval run, the manual check. If the `ICG` classified this as touching data, say
which `DC` moved and to which version, and who was told.
-->

## Documentary base and code set

<!--
When using strict-contribution, cite the documentary repository and full mandate commit,
the proposed documentary commit, and every code repository/commit in the reviewed set.
These are requests/claims for the CI controller to verify, not an approval.
Link the independently collected test runs and their exact code set. A digest copied
from this PR is not an authenticated receipt. Fast-cycle tests do not replace mandatory
tests in the approved policy. A no-chg reason still requires independent review.
See the adopted framework's references/contributions.md.
-->
