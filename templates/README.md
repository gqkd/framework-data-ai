# Artifact templates

One file per artifact. Copy it, rename it following the convention, fill it in. Every
template carries its **anti-patterns** at the end: they are the most useful part, because
they describe the concrete ways that document becomes useless.

<!-- generated: catalog-templates -->
*Generated from `schemas/artifact-types.yaml`. Edit that file, not this table.*

| File | Artifact | Class | Naming |
|---|---|---|---|
| `AGENTS.md` | Control plane for agents | living | `AGENTS.md` |
| `OPEN.md` | Open decisions and known issues | living | `OPEN.md` |
| `COMMITMENTS.md` | Commercial commitments made | living | `COMMITMENTS.md` |
| `GLOSSARY.md` | Glossary and metric dictionary | living | `GLOSSARY.md` |
| `PLATFORM.md` | Architecture of the shared substrate | living | `PLATFORM.md` |
| `product.yaml` | Product manifest | living, partly generated | `products/<p>/product.yaml` |
| `PBR.md` | Product brief | living | `products/<p>/PBR.md` |
| `PRB.md` | Problem statement | immutable | `initiatives/<i>/PRB-NNN.md` |
| `HYP.md` | Solution hypothesis | immutable | `initiatives/<i>/HYP-NNN.md` |
| `WF.md` | Current / target / delta workflow | living | `products/<p>/WF.md` |
| `EVD.md` | Problem evidence brief | immutable | `initiatives/<i>/EVD-NNN.md` |
| `CMP.md` | Competitor comparison | immutable | `initiatives/<i>/CMP-NNN.md` |
| `DFB.md` | Data feasibility brief | immutable | `initiatives/<i>/DFB-NNN.md` |
| `SD.md` | Solution design + MVA | immutable | `initiatives/<i>/SD-NNN.md` |
| `EVP.md` | Evaluation plan | living, frozen for RC | `products/<p>/EVP.md` |
| `DC.md` | Data contract | living, versioned | `products/<p>/contracts/DC-NNN.md` |
| `DEC-ADR.md` | Decision record: product **or** architecture | immutable | `decisions/DEC-NNN-slug.md` |
| `ARC.md` | Current architecture | living | `products/<p>/ARC.md` |
| `RB.md` | Runbook + SLO + monitoring | living | `products/<p>/RB.md` |
| `EVR.md` | Evaluation report | immutable | `products/<p>/releases/EVR-NNN.md` |
| `REL.md` | Release note (for humans) | immutable | `products/<p>/releases/REL-NNN.md` |
| `RLM.yaml` | Release manifest (for machines) | immutable | `products/<p>/releases/RLM-NNN.yaml` |
| `LOG.md` | Signal log | append-only | `products/<p>/LOG.md` |
| `ING.md` | Business corpus ingestion log | append-only | `ING.md` |
| `RMP.md` | Progressive implementation roadmap | living | `products/<p>/RMP.md` |
| `CHG.md` | Change contract | immutable | `products/<p>/changes/CHG-NNN.md` |
| `IMP.md` | Cycle implementation plan | living, replaced | `products/<p>/IMP.md` |
| `RSK.md` | Risks: state / acceptances / events | living | `products/<p>/RSK.md` |
<!-- /generated -->

## The `<!-- section: ... -->` markers

Four templates carry an invisible marker above some of their headings:

```markdown
<!-- section: what-must-not-change -->
### 2 · What must NOT change
```

Those sections are mandatory, and something has to be able to check that they are still
there. The marker carries the identity, the heading carries the prose: renumber the
heading, reword it, translate it into another language, and the check still finds the
section. **Do not delete them and do not rename them.** Which sections are mandatory for
which artifact is in `schemas/artifact-types.yaml`.

Only the mandatory ones are marked. A template with three markers and eight headings is
not half done: the other five headings are yours to change.
