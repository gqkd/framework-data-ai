---
schema: framework/glossary/v1
artifact_type: glossary
lifecycle: living
status: active
products: [product-a, product-b, product-c]
owners: [NAME]
created: YYYY-MM-DD HH:MM
last_review: YYYY-MM-DD HH:MM
classification: internal
# The terms, where a check can find them. The body below keeps the definition, the examples
# and the argument; this map keeps the names, so that a document citing `GLOSSARY §Term` has
# something to resolve against -- `REF005`. Not the `###` headings: two checks here were
# built on headings once and went quiet the day somebody reworded a label.
#
# `blocked_by` is for the term whose definition is waiting on a decision nobody has taken.
# It is the state that used to be written as absence, and a word that is simply missing
# reads as a word defined somewhere else.
terms:
  Name of the term:
    kind: domain
  Name of the metric:
    kind: metric
  Term nobody can define yet:
    blocked_by: OD-001              # `kind` is not required beside `blocked_by`: a term can
                                    # be blocked precisely because whether it is a metric or
                                    # a domain concept is part of what has to be decided
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
- **Origin of the definition:** the `ING-NNN` it came out of. A name here instead, or
  beside it, means a person changed the wording by hand and owns the change.

## §Metrics

### Name of the metric

- **Definition in words:** what it measures and why anyone cares.
- **Formula:** explicit, with numerator and denominator.
- **Source:** reference table or `DC`.
- **Time window:** days, calendar month, rolling.
- **Exclusions:** test accounts, returns, cancellations, internal users.
- **Do not confuse with:** the similar metric it has to be distinguished from.
- **Origin of the definition:** the `ING-NNN`, or a name if a person wrote it.
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
- **Writing a name where the origin belongs.** Most entries come out of the corpus, and
  the honest answer to "who decided this" is "nobody, it is what the customer's deck said".
  An `ING-NNN` records that and stays checkable. A name put there because the field looked
  like it wanted one attributes a definition to somebody who only transcribed it, and the
  next reader treats the wording as a decision that was taken.
- **A definition changed by hand with the origin left as it was.** The moment somebody
  rewords an entry it stops being what the corpus said, and the `ING` alone now points at a
  sentence that no longer matches. Put the name there. That is the whole signal this field
  carries: a definition nobody chose decays at the first argument, and one somebody chose
  has somebody to argue with.
- **Treating it as descriptive.** If you record usages instead of establishing them, you
  have written a dictionary of disagreements.
