---
id: database-sql-distinct-hides-fanout-01
schema_version: 1
title: Revenue tripled after a join, and DISTINCT did not fix it
category: database
topic: sql
level: mid
tags: [correctness, failure-modes, testing]
time_estimate_min: 7
order: 101
links:
  deeper: [database-sql-null-three-valued-logic-01]
  related: [database-relational-model-denormalised-copy-01, kafka-schema-evolution-required-field-01]
---

## Ask

A daily revenue figure used to be `SELECT SUM(o.total) FROM orders o`. Someone joined
`order_items` so the report could be limited to one product category, and revenue tripled. They
changed it to `SUM(DISTINCT o.total)`, the number moved, and finance says it is still wrong. Talk
me through it.

## Tests

Whether the candidate reasons about how many rows a join produces before any aggregate sees them,
and recognises a deduplication bolted on afterwards as suppressing the symptom.

## Listen for

- The join gives one row per item, so an order with three items contributes its total three times
- `DISTINCT` inside the sum collapses equal amounts, so two unrelated orders that both came to
  49.90 are now counted once between them
- Asks what the figure is supposed to mean: money from orders that contain the category, or money
  from the items in that category — two different numbers, both defensible
- Rewrites it so the join does not change the row count: a semi-join for the filter, or collapsing
  the items to one row per order first, or summing the item amounts instead of the order total
- Says how they would have caught it: count the rows before and after the join, or reconcile the
  figure against something outside the query

## Expected knowledge

- A join is evaluated before an aggregate sees the rows
- Deduplication inside an aggregate removes repeated values, not repeated source rows

## Strong signals

- Asks for the definition of the number before touching the query
- Points out that the order count in the same report stayed right, and can say why the key made
  that one safe while the amount was not
- Treats "the total must reconcile with the ledger" as something a test can assert nightly

## Weak signals

- Adds `SELECT DISTINCT` at the top and declares it fixed
- Says "there are duplicates" without saying what produced them
- Groups by the order id and then sums the grouped output without checking what is being summed

## Answer bands

### weak

- Concludes the data contains duplicate orders and proposes cleaning the table.
- Treats deduplication as the standard remedy for a number that came out too big.
- Cannot say why the figure moved when the second table was joined.

### junior

- Says the join produced more rows than there are orders and connects that to the larger figure.
- Identifies the item table as the source of the extra rows.
- Cannot yet say why the second attempt changed the number without making it right.

### mid

- Explains the multiplication in terms of one order having many items.
- Shows how deduplicating the amount folds two genuinely different orders that cost the same.
- Rewrites it in a shape where the filter does not change the row count, and says which rows each
  version counts.

### senior

- Asks which of the two revenue definitions the report is for before choosing a shape.
- Names a check that would have failed the day this shipped rather than a quarter later.
- Says where else the same defect is hiding: any report whose filter needs a child table.

## Follow-ups

- Two unrelated orders that day both came to exactly 49.90. What does their second attempt report
  for those two?
  probes: that deduplicating a value folds equal amounts from rows that have nothing to do with
  each other
- The same report also prints how many orders there were, and that figure is still right. Why did
  only one of the two move?
  probes: counting over a key versus summing over a value, and whether they see what makes one
  safe
- The product filter has to stay. Give me two ways to write it that keep the original figure, and
  say how the two differ.
  probes: a filter that does not multiply rows versus collapsing the child table first

## Sources

- https://www.postgresql.org/docs/current/sql-expressions.html#SYNTAX-AGGREGATES

## Notes

The trap is that the second attempt does change the number, so it looks like progress. If the
candidate stops at "the join duplicates rows", push them to say what the deduplicated sum does to
two different orders of the same value — that is the part that separates mid from junior here.
