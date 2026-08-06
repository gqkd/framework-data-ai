---
schema: framework/glossary/v1
artifact_type: glossary
lifecycle: living
status: active
products: [product-a, product-b, product-c]
owners: [NAME]
created: YYYY-MM-DD
last_review: YYYY-MM-DD HH:MM
classification: internal
---

# Glossary and metrics dictionary

**One single file for all products.** It is the file where the complementarity of the
the products is either defined or lost: if the same concept has two names in two
products, or the same name means two things, the complementarity is already broken and
nobody has noticed.

**It is normative, not descriptive.** It does not record how terms are used: it
establishes how they must be used. Changing an entry requires a `DEC`.

## §Domain terms

### Name of the term

- **Definition:** one sentence, without using the term itself.
- **Does not include:** the cases someone would assume are included and are not.
  Mandatory field: this is where the value is.
- **Banned synonyms:** the other names it gets called and that must not be used.
- **Used in:** products and artifacts.
- **Owner of the definition:** who decides if it changes.

## §Metrics

### Name of the metric

- **Definition in words:** what it measures and why anyone cares.
- **Formula:** explicit, with numerator and denominator.
- **Source:** reference table or `DC`.
- **Time window:** days, calendar month, rolling.
- **Exclusions:** test accounts, returns, cancellations, internal users.
- **Do not confuse with:** the similar metric it has to be distinguished from.
- **Owner of the definition:**
- **Products that compute it:** if more than one, **they must use this formula**. If they
  cannot, they are two different metrics and need two entries with two different names.

---

## Anti-patterns

- **Defining a term using the term.** "Active customer: a customer who is active."
  It happens more often than it seems.
- **Leaving out `Does not include`.** It is the field that settles the arguments; without
  it the glossary is decorative.
- **Different formulas for the same metric in different products.** It is the typical
  failure of a complementary suite, and the most embarrassing one to explain to a
  customer comparing two dashboards.
- **Adding an entry with no owner.** A definition nobody owns decays at the first
  argument.
- **Treating it as descriptive.** If you record usages instead of establishing them, you
  have written a dictionary of disagreements.
