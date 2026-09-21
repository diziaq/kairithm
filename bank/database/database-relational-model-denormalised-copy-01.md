---
id: database-relational-model-denormalised-copy-01
schema_version: 2
title: One customer, three email addresses, three tables
category: database
topic: relational-model
level: mid
tags: [data-modelling, consistency, maintainability]
time_estimate_min: 7
order: 111
links:
  related: [database-schema-design-money-float-01]
---

## Ask

To get rid of a join, the team copied `customer_email` onto `orders` and onto `invoices`. The
application fills it in at insert time. Marketing has just found a customer whose address differs
in all three tables, and nobody can say which one is right. How do you reason about this?

## Tests

Whether the candidate can tell a redundant copy that must agree with its source from a deliberate
record of what was true at a moment, and say what the store can actually enforce in each case.

## Ideal minimal answer

Ask what each copy is for: the address on a posted invoice is a record of what was true then and
must not be overwritten, while a copy kept only to avoid a join has to track the customer row.
Produce the tracking ones from the source — a view, a generated column, a materialised view —
rather than having the application type them in three times.

## Listen for

- Names what went wrong: one fact in three places, a writer that updates one of them, and no rule
  anywhere that keeps the three equal
- Asks which of the three is authoritative and what each copy is used for
- Separates a stale cache of a current value from a frozen record — the address an invoice was
  actually posted to, the price a customer actually paid
- Says the frozen one is legitimate and should be named so nobody "fixes" it, while the cached one
  should be produced from the source (a view, a generated column, a materialised view, a trigger)
  rather than typed in by hand
- Notices that no constraint available to them spans the three tables, so nothing in the database
  is going to catch the next divergence

## Expected knowledge

- The same fact stored in several rows drifts as soon as one writer misses a place
- Removing a join is a trade with a maintenance price, not a free speedup

## Strong signals

- Asks what the removed join actually cost before accepting the copies as necessary
- Points out an invoice is a document that was sent to somebody, so overwriting its copy is wrong
  even when the copy is out of date
- Plans the one-off reconciliation as well as the ongoing rule, and says who decides which value
  wins

## Weak signals

- Says "denormalised for performance" as though that settles it
- Proposes a nightly job to sync the columns, with no view on the hours in between
- Wants every copy removed, including the one on the invoice, with no account of why the join was
  dropped

## Answer bands

### weak

- Picks whichever value looks newest and moves on.
- Says the application should write all three and treats that as the whole fix.
- Does not ask what any of the copies is for.

### junior

- Says the fact is stored three times with nothing keeping the copies equal.
- Can describe a write path that updates one table and misses the others.

### mid

- Asks which copy the business treats as true, and what each is read for.
- Distinguishes the copy that must track the source from the copy that is supposed to record what
  it was at the time.
- Says the tracking copies should be derived from the source rather than written twice, and names
  a mechanism.

### senior

- Puts the rule where a writer cannot skip it, and is explicit about what the store can and cannot
  check across tables.
- Prices the join that was removed against the reconciliation work now permanently owned.
- Says what happens to the rows already written during the change, and who signs off which value
  is correct.

## Follow-ups

- One of the three sits on an invoice that was posted two years ago and has been paid. Should that
  value ever change?
  probes: whether they spot the legitimate frozen record instead of removing all redundancy
- That join sat on a page that gets a hundred hits a second. Does knowing that change your answer?
  probes: whether they take the original motive seriously and cost it, rather than dismissing it
- Where does the next copy like this come from, and what would stop it before it lands?
  probes: a review habit versus a rule the store enforces; derived columns and views

## Sources

- https://www.postgresql.org/docs/current/ddl-generated-columns.html
- https://dev.mysql.com/doc/refman/8.4/en/create-table-generated-columns.html

## Notes

The card fails if the candidate answers "normalise it" for all three copies, and it also fails if
they answer "denormalisation is normal". The signal is whether they ask what each copy means
before deciding. The invoice copy is the one that should survive the conversation.
