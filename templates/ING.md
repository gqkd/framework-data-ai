---
schema: framework/ingestion-register/v1
artifact_type: ingestion-register
lifecycle: append-only
status: active
products: [product-a, product-b, product-c]
owners: [NAME]
created: YYYY-MM-DD
classification: confidential
---

# Business corpus ingestion log

**Question:** what do the documents produced by the business claim, where exactly is it
written, and what did we do with it?

**Why it is not written straight into the final artifacts.** Three concrete reasons:

- **Provenance.** The pointer to document and slide stays here. In the final artifact that
  trace is lost, and you will need it every time a claim has to be checked.
- **Review queue.** Two hundred slides produce more claims than anyone can assess in one
  sitting. This log is the state of that work and it lets you stop halfway.
- **Traceable rejection.** You can reject a claim while keeping the fact that the business
  made it. That is exactly what you need when someone asks, eight months later, why that
  feature is not there.

**Append-only:** rows are not edited. Only the `Outcome` column changes, and if an
assessment changes you add a new row that points back to the previous one.

<!-- section: claims -->
## §claims

| ID | Document | Position | Verbatim | Type | Destination | Outcome |
|---|---|---|---|---|---|---|
| ING-001 | customer-offer.pptx | slide 1 | "A single experience across the three modules" | constraint disguised as a claim | `OPEN.md` OD-003 | routed |
| ING-002 | customer-offer.pptx | slide 2 | "30% reduction in reconciliation time" | numeric target | `CMT-004` + `EVP` threshold | routed |
| ING-003 | customer-offer.pptx | slide 2 | "Active customer: anyone who logged in within 30 days" | definition | `GLOSSARY` | routed |

`Type`: use the taxonomy of the ingestion routing reference.

`Outcome`: `to assess` · `routed` · `rejected` · `deferred` · `contradiction`

For `rejected` the reason is mandatory: it is the information this log exists for.

<!-- section: contradictions -->
## §contradictions

The most valuable part of the log. Every entry carries **both** provenances.

| ID | Claim A | Source A | Claim B | Source B | Nature | Where it went |
|---|---|---|---|---|---|---|
| ING-C01 | "Real time data" | customer-offer.pptx slide 2 | "Hourly refresh, existing nightly batch" | requirements.docx §Constraints | incompatible timing promise | `OPEN.md` OD-011 |

**If the two versions were told to two different customers**, this is not a technical
decision: it is a commitment to renegotiate. It goes in `COMMITMENTS §Out of reach` and it
gets raised immediately. Two customers who were promised opposite things is a problem that
only gets solved by talking about it.

<!-- section: to-review -->
## §to review

Slides and pages that came out of extraction with almost no text, which usually means they
are drawings.

| Document | Pages | Reviewed | What it contained |
|---|---|---|---|
| customer-offer.pptx | 3 | yes | three box diagram: implies shared tenancy → OD-003 |

On a sales deck the architectural constraint is often drawn rather than written. The
`Reviewed` column exists because the temptation to skip this step is strong.

## §tally

Filled in at the end of each ingestion batch.

- Documents processed:
- Claims classified:
- Routed / rejected / deferred:
- **Contradictions found:**
- **Commitments that turned out to be out of reach:**

---

## Anti-patterns

- **Extracting everything for completeness.** A forty slide deck holds perhaps fifteen
  claims with consequences. The rest is sales narrative, and including it makes what
  matters impossible to find.
- **Paraphrasing the verbatim.** The column is called verbatim for a reason: the ambiguity
  of the original is precisely the information you need in order to negotiate.
- **No rows in `§contradictions`.** With three or more documents written by different
  people that does not mean there are none. It means you have not compared them.
- **Treating the corpus as a specification.** It is the record of what was promised. Its
  main destination is `COMMITMENTS`, not a product document.
- **Skipping `§to review`.** That is where the architectural constraints nobody wrote down
  are hiding.
