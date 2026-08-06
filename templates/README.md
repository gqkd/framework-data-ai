# Artifact templates

One file per artifact. Copy it, rename it following the convention, fill it in. Every
template carries its **anti-patterns** at the end: they are the most useful part, because
they describe the concrete ways that document becomes useless.

| File | Artifact | Class | Naming |
|---|---|---|---|
| `AGENTS.md` | Control plane for agents | living | `AGENTS.md` |
| `OPEN.md` | Open decisions and known issues | living | `OPEN.md` |
| `PLATFORM.md` | Shared substrate architecture, only if you have one | living | `PLATFORM.md` |
| `product.yaml` | Product manifest | living, partly generated | `products/<p>/product.yaml` |
| `COMMITMENTS.md` | Commercial commitments | living | `COMMITMENTS.md` |
| `GLOSSARY.md` | Glossary and metrics | living | `GLOSSARY.md` |
| `PBR.md` | Product brief | living | `products/<p>/PBR.md` |
| `PRB.md` | Problem statement | immutable | `initiatives/<i>/PRB-NNN.md` |
| `HYP.md` | Solution hypothesis | immutable | `initiatives/<i>/HYP-NNN.md` |
| `WF.md` | Current/target/delta workflow | living | `products/<p>/WF.md` |
| `EVD.md` | Problem evidence brief | immutable | `initiatives/<i>/EVD-NNN.md` |
| `CMP.md` | Competitor comparison | immutable | `initiatives/<i>/CMP-NNN.md` |
| `DFB.md` | Data feasibility brief | immutable | `initiatives/<i>/DFB-NNN.md` |
| `SD.md` | Solution design + MVA | immutable | `initiatives/<i>/SD-NNN.md` |
| `EVP.md` | Evaluation plan | living | `products/<p>/EVP.md` |
| `DC.md` | Data contract | living | `products/<p>/contracts/DC-NNN.md` |
| `DEC-ADR.md` | Decision record (product or architecture) | immutable | `decisions/DEC-NNN-slug.md` |
| `ARC.md` | Current architecture | living | `products/<p>/ARC.md` |
| `RB.md` | Runbook + SLO | living | `products/<p>/RB.md` |
| `EVR.md` | Evaluation report | immutable | `products/<p>/releases/EVR-NNN.md` |
| `REL.md` | Release note | immutable | `products/<p>/releases/REL-NNN.md` |
| `RLM.yaml` | Release manifest | immutable | `products/<p>/releases/RLM-NNN.yaml` |
| `LOG.md` | Signal log | append-only | `products/<p>/LOG.md` |
| `ING.md` | Business corpus ingestion log | append-only | `ING.md` |
| `RMP.md` | Progressive roadmap | living | `products/<p>/RMP.md` |
| `CHG.md` | Change contract | immutable | `products/<p>/changes/CHG-NNN.md` |
| `IMP.md` | Cycle implementation plan | living | `products/<p>/IMP.md` |
| `RSK.md` | Risk register | living | `products/<p>/RSK.md` |
