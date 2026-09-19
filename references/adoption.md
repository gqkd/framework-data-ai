# Adopting a framework version without migrating product history

Use this guide when evaluating or adopting an increment. Upgrading the framework and
turning on the opt-in verification profiles are **two independent operations**: installing
the new version grants no permission for the second.

```text
trusted previous framework + proposed framework
                    | compare validators, same project, read-only
                    v
              migration report -- approved adoption --> framework.yaml pin/version

separately, and only when the project decides:
approved CHG + committed contribution policy + witnessed receipts --> strict gate
```

## 1. Compare, then adopt only with approval

Keep the previous trusted checkout or export until the comparison has been reviewed. Run
from any directory, with Python dependencies installed from the proposed complete framework:

```bash
python3 /path/to/new-framework/skills/audit/scripts/migrate.py --root /path/to/documents --json
```

When the project's `framework_commit` is available in the framework clone, it is the
baseline. Otherwise an unpinned version resolves via the registry's Git history; that is
not proof of the exact rules previously executed. `--from-commit` selects an explicit
commit, which must declare the requested version; an unavailable pin does not silently
fall back to another commit. `--from` overrides the starting version, and therefore stops
using the project's old pin. The report identifies `previous_source`.

For packages extracted from Git archives, with no Git history:

```bash
python3 /path/to/new-package/skills/audit/scripts/migrate.py \
  --root /path/to/documents --from-framework /path/to/old-package --json
```

Supply **complete, operator-trusted framework trees**, not just the old validator file and
never a framework supplied by an untrusted product PR. The tool executes both validators in
separate Python processes with their own schemas and packages. Export version matching is
checked; its origin is **not authenticated** (`commit_verified: false`). Independently
verify the archive source and digest before executing it. Neither a passing comparison nor
a same-version no-op establishes independent contribution authority.

Review new findings and historical repairs separately; preserve annotations only while
their findings still exist (`AN001`). `FW001`, `FW002` and `FW003` identify version and pin
work. With explicit approval, add `--adopt`: it changes `framework.yaml` and nothing else.
A pinned project needs a clean committed target Git checkout; a Gitless export cannot move
its pin. The strict profiles also require the actual approved Git objects; a package alone
cannot authenticate them.

The normal migration and selfcheck gates still apply. No automated check can approve a new
architectural choice or declare that a human reviewed an annotation.

`test_adoption.py` checks real complete baseline and new archives, foreign import
isolation, wrong or missing sources, dirty and Gitless pinned adoption, and the isolated
approved write.

## 2. Turning on verification is a separate decision

Adopting the version does not enable a gate. To use `--profile strict-contribution` a
project must, in this order:

1. **Write the policy first.** `.framework/contribution-policy.json` binds an approved
   `CHG` to the repositories, paths, documentary obligations and tests it authorizes. The
   strict profile reads it from the mandate commit and checks that it still agrees with the
   approved tip, so it has to be committed **before** the work it governs. A policy written
   after the fact governs nothing.
2. **Decide who produces the receipts.** The gate **compares** the declared test commands,
   it never executes them, and it requires the execution witness to be authenticated by
   whoever controls CI. Without an authenticated producer the gate fails closed, which is
   the intended behaviour and not a misconfiguration.
3. **Decide the reviewers for the `no-chg` exception**, or leave the list empty so that no
   contribution without a mandate can pass.

`references/contributions.md` owns the trust boundary and states which inputs the caller,
not the framework, must establish. Copying a workflow does not activate repository
protection, and nothing here performs a merge or a deployment.

**Know the limit before relying on it.** The path scope is per path: a contribution that
exceeds its mandate inside a file the mandate authorizes is not caught. An unfulfilled
documentary obligation is caught. Neither profile proves semantic preservation.

## Distribution, dependencies and rollback

The distribution is the complete repository or a complete Git archive, also usable through
the existing plugin mechanism. Do not distribute `src/` or one script alone: schemas,
references, templates and skill bodies are runtime inputs. There is no new PyPI package,
autonomous installer, binary bundling or background service, and no third-party code is
redistributed.

```bash
python3 -m pip install -r /path/to/framework/requirements.txt
python3 /path/to/framework/schemas/generate.py --check
python3 /path/to/framework/schemas/generate_memory.py --check
python3 /path/to/framework/tests/selfcheck.py
```

Use an isolated environment. Rerun the full suite after any dependency update. Version
ranges do not pin wheel hashes or OS packages and are not a vulnerability audit.

Rollback the **tool** by selecting the preserved previous checkout and its environment; the
migration command intentionally refuses to disguise a downgrade as a forward adoption. A
maintainer may restore the matching earlier project pin with explicit approval. Do not
delete or rewrite historical artifacts. Rebuilding with new rule bytes or different
interpreter and dependency versions produces a new identity. Arbitrarily old versions,
custom scan overrides and project-promoted warnings require their own comparison. Tool
rollback does not undo a product deployment, and it does not preserve a gate that the older
tool never implemented.
