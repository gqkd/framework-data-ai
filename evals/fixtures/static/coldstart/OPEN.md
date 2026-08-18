---
schema: framework/open-register/v1
artifact_type: open-register
lifecycle: living
status: active
products: [ricambi-ai]
owners: [l.bianchi]
created: 2026-07-28
last_review: 2026-07-28 16:40
classification: internal
# Derived from the entries below, so the two cannot disagree about anything a
# check reads. Where a heading and a cost contradict each other, that is the
# defect this fixture is built around and it is preserved.
entries:
  OD-001:
    status: open
    cost_to_reverse: high
    default_in_force: none
  OD-002:
    status: open
    cost_to_reverse: high
    default_in_force: none
  OD-003:
    status: open
    cost_to_reverse: medium
    default_in_force: the nightly export, because it is the only one that exists
  OD-004:
    status: open
    cost_to_reverse: low
    default_in_force: Italian only
---

# Open decisions and known issues

# §1 · Open decisions

## Cost to reverse HIGH: decide before the first line of code

### OD-001 · Where the system runs

- **Question:** on Ricambi Lombardi's own hardware in Brescia, on a European region of a
  hyperscaler, or on a US-owned hyperscaler in a European region?
- **Cost to reverse:** high.
- **Default in force:** none.
- **The problem the default introduces:** the client said "no roba in cloud americano" and
  nobody has asked what that means. Every other technical choice hangs off this one.
- **Trigger:** before the first line of code.

### OD-002 · What the thing the counter clerk types into actually is

- **Question:** a search over the catalogue that ranks results, or a model that answers with
  one code and a confidence?
- **Cost to reverse:** high.
- **Default in force:** none.
- **The problem the default introduces:** the two are different products, need different
  evaluation, and the client's sentence ("gli esce il codice giusto") can be read either way.
- **Trigger:** before the first line of code.

## Cost to reverse MEDIUM: decide within the first month

### OD-003 · How stock levels reach the system

- **Question:** the nightly AS/400 export as-is, or do we ask them to add an intra-day one?
- **Cost to reverse:** medium.
- **Default in force:** the nightly export, because it is the only one that exists.
- **The problem the default introduces:** a clerk can be told a part is in Verona when it
  left Verona this morning.
- **Trigger:** before the pilot.

## Cost to reverse LOW: defer them as long as you like

### OD-004 · Which language the interface is in

- **Question:** Italian only, or Italian and English?
- **Cost to reverse:** low.
- **Default in force:** Italian only.
- **Trigger:** the first non-Italian customer.

---

# §2 · Accepted known issues

_None recorded._

---

# §3 · Parking lot

- Whether the same thing could be sold to the officine directly.

---

# §4 · Closed decisions

_None yet._
