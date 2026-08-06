# Template degli artefatti

Un file per artefatto. Copia, rinomina secondo la convenzione, compila. Ogni template
contiene gli **anti-pattern** in fondo: sono la parte più utile, perché descrivono i modi
concreti in cui quel documento diventa inutile.

| File | Artefatto | Classe | Naming |
|---|---|---|---|
| `AGENTS.md` | Control plane per agenti | vivente | `AGENTS.md` |
| `OPEN.md` | Decisioni aperte e problemi noti | vivente | `OPEN.md` |
| `PLATFORM.md` | Architettura del substrato condiviso | vivente | `PLATFORM.md` |
| `product.yaml` | Manifest prodotto | vivente, in parte generato | `products/<p>/product.yaml` |
| `COMMITMENTS.md` | Impegni commerciali | vivente | `COMMITMENTS.md` |
| `GLOSSARY.md` | Glossario e metriche | vivente | `GLOSSARY.md` |
| `PBR.md` | Product brief | vivente | `products/<p>/PBR.md` |
| `PRB.md` | Formulazione problema | immutabile | `initiatives/<i>/PRB-NNN.md` |
| `HYP.md` | Ipotesi soluzione | immutabile | `initiatives/<i>/HYP-NNN.md` |
| `WF.md` | Workflow corrente/target/delta | vivente | `products/<p>/WF.md` |
| `EVD.md` | Problem evidence brief | immutabile | `initiatives/<i>/EVD-NNN.md` |
| `CMP.md` | Comparativa competitor | immutabile | `initiatives/<i>/CMP-NNN.md` |
| `DFB.md` | Data feasibility brief | immutabile | `initiatives/<i>/DFB-NNN.md` |
| `SD.md` | Solution design + MVA | immutabile | `initiatives/<i>/SD-NNN.md` |
| `EVP.md` | Evaluation plan | vivente | `products/<p>/EVP.md` |
| `DC.md` | Data contract | vivente | `products/<p>/contracts/DC-NNN.md` |
| `DEC-ADR.md` | Decision record (prodotto o architettura) | immutabile | `decisions/DEC-NNN-slug.md` |
| `ARC.md` | Architettura corrente | vivente | `products/<p>/ARC.md` |
| `RB.md` | Runbook + SLO | vivente | `products/<p>/RB.md` |
| `EVR.md` | Evaluation report | immutabile | `products/<p>/releases/EVR-NNN.md` |
| `REL.md` | Release note | immutabile | `products/<p>/releases/REL-NNN.md` |
| `RLM.yaml` | Release manifest | immutabile | `products/<p>/releases/RLM-NNN.yaml` |
| `LOG.md` | Registro segnali | append-only | `products/<p>/LOG.md` |
| `ING.md` | Registro di ingestione corpus business | append-only | `ING.md` |
| `RMP.md` | Roadmap progressiva | vivente | `products/<p>/RMP.md` |
| `CHG.md` | Change contract | immutabile | `products/<p>/changes/CHG-NNN.md` |
| `IMP.md` | Cycle implementation plan | vivente | `products/<p>/IMP.md` |
| `RSK.md` | Registro rischi | vivente | `products/<p>/RSK.md` |
