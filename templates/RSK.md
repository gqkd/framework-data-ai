---
schema: framework/risk-register/v1
artifact_type: risk-register
lifecycle: living
status: active
version: 1.0.0
products: [product-a]
owners: [NAME]
created: YYYY-MM-DD HH:MM
last_review: YYYY-MM-DD HH:MM
classification: confidential
# §state, where a check can read it. The body below keeps the mitigation, the owner and
# the argument; §acceptances and §events stay prose entirely, because an acceptance is
# somebody's signature under a sentence and an event is a story with a date.
#
# `commitment` is the field that makes the pair joinable: a risk about a promise names the
# promise. On a `commercial` risk the field is expected either way -- `CMT-NNN` when somebody
# promised this, `none` when the exposure is real and nobody promised anything, which is the
# ordinary case for a market hypothesis nobody has tested or an IP transfer nobody completed.
# Silence is `REF006`, and it reads as the first: a promise made and recorded nowhere.
risks:
  RSK-001:
    category: technical
    state: open
    likelihood: M
    impact: H
  RSK-002:
    category: commercial
    state: open
    likelihood: M
    impact: H
    commitment: CMT-001
  RSK-003:
    category: commercial
    state: open
    likelihood: M
    impact: M
    commitment: none                  # a commercial exposure nobody promised: said out
                                      # loud, because silence here reads as a promise
                                      # somebody made and nobody wrote down
---

# Risk and compliance register: Product name

**Question:** which risks do we know about, what state are they in, and what have we
decided about each one?

**One file, three sections.** A risk register cannot be immutable (it has to show the
current state) but risk acceptances can be, and so can the sequence of events. Three
regimes in one file, split into sections, because separate files would diverge.

---

<!-- section: state -->
# §state

Living. The current truth. One row per risk.

| ID | Risk | Category | Likelihood | Impact | State | Mitigation | Owner | Reviewed |
|---|---|---|---|---|---|---|---|---|
| RSK-001 | | technical · data · AI · security · compliance · commercial · organisational · vendor | L/M/H/C | L/M/H | | | | YYYY-MM-DD |

`state`: `open` · `mitigated` · `accepted` · `transferred` · `closed` · `expired`

`likelihood` `C` is certain, and it is not a fourth degree of likely: the thing has happened,
or what is written down already contradicts what was said outside. Leaving the field empty
because `H` would be an understatement takes the row out of every ordering that reads a
likelihood, which is the one outcome worse than an imprecise letter.

`security` is not `compliance` — one is whether somebody gets in, the other whether a rule is
broken — and `organisational` is the risk that the person is not there: a decision whose
validity depends on somebody being on shift rather than on code.

`expired` deserves attention: it is a risk whose mitigation was tied to a condition that no
longer holds. These are the most dangerous, because they look managed.

## Compliance

| Processing | Legal basis | Retention | Non-EU | Automated decision | `DC` |
|---|---|---|---|---|---|

For AI systems, add: known biases and how they were measured · human oversight, where it
sits and what it can overturn · explainability available to the end user.

---

<!-- section: acceptances -->
# §acceptances

Immutable. One entry per accepted risk: you do not modify it, you supersede it.

### RSK-NNN accepted on YYYY-MM-DD

Who accepted it · why · estimated exposure · conditions under which the acceptance lapses ·
reference `DEC`.

An accepted risk with no lapse condition is a forgotten risk with more bureaucratic steps.

---

<!-- section: events -->
# §events

Append-only. What actually happened, so you can check after the fact whether the estimates
were sensible.

| Date | `RSK` | Event | `SIG` | Consequence |
|---|---|---|---|---|

This section is the only way to find out that you were systematically misjudging one
category of risk.

---

## Anti-patterns

- **A register written once and never reviewed.** A risk without a recent `Reviewed` date
  is not managed: it is filed away.
- **Every risk `open`.** It means you do not decide: you assess.
- **Acceptance with no lapse condition.**
- **Leaving out the commercial risks** because "they are not technical". An out of reach
  commitment in `COMMITMENTS` is the biggest risk in the project and it belongs here too.
- **No rows in `§events`.** If you do not record the incidents here as well, you will never
  know whether your likelihood estimates were worth anything.
