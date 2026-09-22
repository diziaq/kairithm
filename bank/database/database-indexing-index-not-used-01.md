---
id: database-indexing-index-not-used-01
schema_version: 2
title: The index is right there and login is still getting slower
category: database
topic: indexing
level: senior
tags: [performance, correctness, maintainability]
time_estimate_min: 8
order: 132
links:
  related: [database-schema-design-natural-key-not-stable-01]
---

## Ask

`users` has an index on `email`. Login runs `WHERE lower(email) = $1` and has got slower every
week for a year, in step with the table. Adding application workers changed nothing. The team has
booked a maintenance window to rebuild the index. Before they do — what do you tell them?

## Tests

Whether the candidate can say what an index is keyed on, recognise the predicate shapes that put a
query outside it, and separate an index that cannot be used from one the engine declines to use.

## Ideal minimal answer

`lower(email)` is not the value the index is ordered by, so it cannot be used and the work has
always been proportional to the table — which is the year-long slope; rebuilding changes
nothing. Repair it with an index on the expression in PostgreSQL, a functional key part or
generated column in MySQL 8, or store the address already normalised and compare it as stored.

## Listen for

- The index holds the values as they are stored; the query asks about a derived value, so the two
  are not the same question and the ordering in the index says nothing about it
- Names the repairs and which engine they belong to: an index on the expression in PostgreSQL, a
  functional key part or a generated column in MySQL 8, or store the address already normalised
  and compare it as stored
- Lists other predicates with the same cause: a leading wildcard, arithmetic on the column, a
  comparison that forces the column to be converted to another type, a mismatched collation
  between two joined columns
- Says rebuilding changes nothing here, and explains the year-long trend — the work was always
  proportional to the table, and the table grew
- Distinguishes "the engine cannot use it" from "the engine decided not to", and can give a reason
  the second one is sometimes right

## Expected knowledge

- A btree index is ordered by the stored values
- Wrapping the column in a call no longer asks about those values

## Strong signals

- Asks what type the parameter is, in case a conversion is happening where nobody wrote one
- Prefers storing the normalised form once over computing it on every read, and can argue it
- Knows the engines differ on whether the plain index would have sufficed without the call at all

## Weak signals

- Rebuilds or reorganises the index, then reports it fixed once the cache has warmed
- Adds a second plain index on the same column
- Concludes the database cannot do this kind of lookup and moves it into the application

## Answer bands

### weak

- Blames a corrupt or fragmented index and keeps the maintenance window.
- Says the table simply got too big and asks for a larger machine.
- Cannot say what the index is sorted by.

### mid

- Says the stored values and the thing being compared are not the same, so the index does not
  apply.
- Proposes indexing the computed form or storing it, and knows one of the two spellings for the
  engine in use.

### senior

- Generalises to the other predicate shapes that put a query outside an index, producing two from
  memory before either is put to them.
- Says which repairs change the behaviour of rows already stored and which leave them alone.
- Separates an index that cannot serve the query from one that could and is skipped anyway, and
  gives a reason for the second.
- Explains the slope of the last year rather than only the state today.

### lead

- Chooses between normalising on write and indexing the derived value from what else reads that
  column, and says exactly what the migration touches.
- Says how the team finds the other queries with the same shape before a customer reports one.
- Gets the meaning of the address as a credential written down — case, surrounding spaces,
  plus-addressing — so the rule stops being folklore.

## Follow-ups

- An account number column holds text and the application passes it a number. Same family of
  problem?
  probes: a comparison that converts the column rather than the parameter; whether the rule
  generalises past the obvious case
- They decide to store it already cleaned up instead. What happens to the eight million rows
  already there, and to the two other places that insert?
  probes: backfill, and every writer; whether the rule is enforced or merely intended
- Support says a customer typing capitals cannot sign in against one of our two databases but can
  against the other. Explain that.
  probes: collation defaults differing between engines, and whether they know which one is theirs

## Sources

- https://www.postgresql.org/docs/current/indexes-expressional.html
- https://dev.mysql.com/doc/refman/8.4/en/create-index.html
- https://dev.mysql.com/doc/refman/8.4/en/type-conversion.html

## Notes

MySQL supports functional key parts from 8.0.13; before that the idiom is a stored generated
column with an index on it. PostgreSQL has had indexes on expressions for far longer. On MySQL the
call may not be needed at all, because the default collation already compares case-insensitively —
worth releasing if the candidate has gone deep on PostgreSQL and never mentioned the other side.

Keep this on why the index is or is not applicable. If the candidate starts narrating how they
would read the engine's output for this query, note it as a positive and steer them back to the
predicate.
