No. Alpha’s ARC does not attest the current local code snapshot.

- `products/alpha/product.yaml` identifies `code/alpha-api` as alpha’s API repository ([product.yaml, `code.api`](/tmp/framework-memory-phase9-batch-20260910/trials/attested-snapshot-is-not-head/project/products/alpha/product.yaml:16)).
- The ARC records `product.api` commit `08bb1e25cf063dce6d6ecd56afcd689137a60ab7` ([ARC.md, `verified_code`](/tmp/framework-memory-phase9-batch-20260910/trials/attested-snapshot-is-not-head/project/products/alpha/ARC.md:14)).
- The local repository’s current `HEAD` is `6a1c6ef23a481569d4020647ba2d09c78823b925`.
- Git history shows `6a1c6ef…` is one commit after `08bb1e25…`, with the subject “Add a synthetic health endpoint.” The ARC commit is its direct parent.
- The checkout had no reported tracked, staged, or ordinary untracked changes, so the inspected working snapshot corresponds to `HEAD`.
- The intervening commit adds `health() -> True` to [service.py](/tmp/framework-memory-phase9-batch-20260910/trials/attested-snapshot-is-not-head/project/code/alpha-api/service.py:6). No other tracked file differs between the two commits.

This interpretation is also explicit in the ARC’s `Current` section: `verified_code` identifies an exact snapshot and is “not a claim about every later commit” ([ARC.md, `Current`](/tmp/framework-memory-phase9-batch-20260910/trials/attested-snapshot-is-not-head/project/products/alpha/ARC.md:33)). Therefore, the ARC attests the older baseline, not current `HEAD`, even though the recorded commit is an ancestor and the existing normalization code remains present.

I also read the named authorities: [DC-001, `Schema`/`Guarantees`](/tmp/framework-memory-phase9-batch-20260910/trials/attested-snapshot-is-not-head/project/products/alpha/contracts/DC-001-response.md:21) and [DEC-001, `Decision`](/tmp/framework-memory-phase9-batch-20260910/trials/attested-snapshot-is-not-head/project/decisions/DEC-001-shared-rule.md:22), plus the current service, test, and schema. They establish the normalization constraints but do not extend the ARC attestation to the later commit.

Uncertainty: this was a read-only commit/tree comparison. I did not execute tests or measure runtime behavior, and Git’s ordinary status does not report ignored files.