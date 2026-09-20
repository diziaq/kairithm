---
id: database-sql-null-three-valued-logic-01
schema_version: 1
title: The same query returns 4000 rows in staging and none in production
category: database
topic: sql
level: senior
tags: [correctness, failure-modes, data-modelling]
time_estimate_min: 8
order: 102
---

## Ask

This lists customers who have never had an order cancelled:

```sql
SELECT id FROM customers
WHERE id NOT IN (SELECT customer_id FROM orders WHERE status = 'cancelled')
```

In staging it returns four thousand rows. In production it returns none, with no error, and has
done for a month. The team says nothing is broken. Where do you look first?

## Tests

Whether the candidate can reason about a predicate that is neither true nor false, and trace an
empty result back to one row of data rather than to a configuration difference.

## Listen for

- Asks whether the subquery column is nullable, and what a single empty value in that list does
- Works the logic through: the row is kept only when the predicate is true, and comparing anything
  with an unknown value yields unknown, so one unknown in the list sinks every row
- Says the positive form does not fail the same way — an unknown there only fails to match
- Rewrites with a correlated existence test, or excludes the empty values in the subquery, and can
  say why the rewrite is immune
- Treats the difference between the two environments as data, not settings: production has one row
  staging does not

## Expected knowledge

- A filter admits rows whose predicate evaluates true; false and unknown are both dropped
- Aggregates skip empty values, so counting a column and counting rows give different answers

## Strong signals

- Wants the column constrained so the value cannot come back, and treats the query rewrite as the
  smaller half of the fix
- Knows the null-safe comparison in the engine they use — `IS DISTINCT FROM` in PostgreSQL,
  `<=>` in MySQL
- Knows a `CHECK` constraint passes when its expression is unknown, so the same logic lets bad
  rows in elsewhere

## Weak signals

- Blames "a data difference between environments" and stops before naming the row
- Recites that null means unknown without applying it to the operator on the screen
- Swaps in an existence test because "it performs better", with no account of the different result

## Answer bands

### weak

- Concludes production genuinely has no such customers and closes the ticket.
- Argues the query must be fine because it runs and returns without an error.
- Suggests rewriting it at random until the count looks plausible.

### mid

- Asks whether the subquery can yield an empty value and connects that to the empty result.
- Rewrites it so that value no longer decides the outcome, and checks the new count against the
  data.

### senior

- Works the predicate through term by term and says exactly which comparison is neither true nor
  false.
- Explains why the positive and negative forms behave differently, instead of calling both unsafe.
- Fixes the column so the value cannot reappear, not only the one query.
- Says what the aggregates in the same report are quietly doing with those rows.

### lead

- Finds the other places in the schema where the same predicate silently passes or silently
  drops everything, and says how the team would sweep for them.
- Weighs constraining the column plus a backfill against a rewrite every author has to remember.
- Says what would have made the two environments disagree loudly a month ago instead of quietly.

## Follow-ups

- Someone writes the positive version — the customers who do have one of those orders — against
  the same data. Does that one break too?
  probes: the asymmetry between the two forms when a value is unknown
- Staging runs the same code against the same schema. What could differ between the two databases
  to give four thousand rows against none?
  probes: whether they reduce it to a single row of data rather than a setting or a version
- A colleague proposes adding a test inside the inner query to drop the empty values, and nothing
  else. Would you sign that off?
  probes: whether they want the column itself to stop producing them, and who else writes the
  same shape

## Sources

- https://www.postgresql.org/docs/current/functions-subquery.html
- https://www.postgresql.org/docs/current/functions-comparison.html
- https://dev.mysql.com/doc/refman/8.4/en/working-with-null.html
- https://www.postgresql.org/docs/current/ddl-constraints.html

## Notes

`orders.customer_id` is nullable and production picked up one row with it empty — a guest
checkout, an import, a partial rollback. The interviewer can release that if the candidate is
circling but has not landed.

A `CHECK` constraint is satisfied when its expression evaluates to true *or* to unknown; this is
standard behaviour and is stated in the PostgreSQL documentation linked above. It surprises people
who expect the constraint to reject the row.
