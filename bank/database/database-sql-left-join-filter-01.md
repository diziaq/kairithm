---
id: database-sql-left-join-filter-01
schema_version: 2
title: The customers with no orders vanished from the report
category: database
topic: sql
level: junior
tags: [correctness, failure-modes]
time_estimate_min: 6
order: 100
links:
  related: [general-testing-bug-escaped-with-green-tests-01]
  deeper: [database-sql-distinct-hides-fanout-01]
---

## Ask

This is meant to list every customer with what they have spent, including the ones who have never
bought anything:

```sql
SELECT c.id, c.name, SUM(o.total)
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE o.status = 'paid'
GROUP BY c.id, c.name
```

Customers with no orders are not in the output. Why?

## Tests

Whether the candidate reads a query as rows surviving one clause at a time, rather than reading
the join keyword and assuming the result matches the intent.

## Ideal minimal answer

The join does produce a row for a customer with no orders, with the order columns empty, and
then `WHERE o.status = 'paid'` is applied to those joined rows — an empty value is not equal to
'paid', so they are thrown away again. Move that test into the `ON` condition, or allow the
empty case in the filter.

## Listen for

- The join does produce a row for such a customer, with the order columns empty
- That filter is applied to the joined rows, and an empty value is not equal to `'paid'`, so those
  rows are thrown away again
- Names the repair: move the test into the join condition, or allow the empty case in the filter
- Says what the spend column holds for a customer with nothing paid, and that it is not zero
  unless somebody makes it zero
- Recognises the shape: a filter on the optional table written outside the join turns the whole
  thing back into an inner join

## Expected knowledge

- An outer join fills the columns of the unmatched side with nothing
- The same test in the join and in the filter does not mean the same thing

## Strong signals

- Reproduces it in their head on three rows rather than guessing at the rule
- Asks what the report should show for a customer whose only order was refunded, before rewriting

## Weak signals

- Swaps the join for a different one, or reorders the two tables, and expects the rows back
- Says the data must be missing for those customers
- Adds a grouping column or a `DISTINCT` and checks whether the count looks better

## Answer bands

### weak

- Concludes those customers have nothing to show and the report is right.
- Changes the join type or the table order and waits to see what happens.
- Cannot say which clause removes a row.

### junior

- Points at the filter on the order columns as the thing that drops the rows.
- Says the dropped rows had empty order columns after the join.
- Repairs it by moving that test into the join, or by admitting the empty case in the filter.

### mid

- Walks the clauses in the order they apply and says the filter sees already-joined rows.
- Notes the spend comes back empty rather than zero, and converts it on purpose rather than by
  accident.
- Says this is a pattern, not a one-off, and where else in the codebase to look for it.

## Follow-ups

- Someone rewrites the test as `o.status <> 'cancelled'`. Do the missing customers come back?
  probes: whether the same reasoning survives a negated test, and whether they see the empty
  value fails that one too
- The amount column is now blank rather than 0 for those customers. Does that matter, and to
  whom?
  probes: null versus zero out of an aggregate, and whether the conversion is deliberate
- Finance wants the opposite list — only the customers who have never bought anything. How would
  you write that?
  probes: anti-join shapes; whether they reach for a test on the unmatched side or a `NOT EXISTS`

## Sources

- https://www.postgresql.org/docs/current/queries-table-expressions.html#QUERIES-FROM

## Notes

The candidate does not have to know the word for this. What separates the bands is whether they
can say which clause removes which row, and in what order. If they fix it by moving the test into
the join, ask them what the `SUM` now returns for an unmatched customer — that is where the
second half of the card lives.
