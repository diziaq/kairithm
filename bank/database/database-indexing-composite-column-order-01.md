---
id: database-indexing-composite-column-order-01
schema_version: 1
title: Reverse the index, or add a second one?
category: database
topic: indexing
level: mid
tags: [performance, operations, data-modelling]
time_estimate_min: 8
order: 131
links:
  deeper: [database-indexing-index-not-used-01]
---

## Ask

An `events` table has one index, on `(tenant_id, created_at)`. The dashboard filters on both and
is quick. A new export filters on `created_at` only, for one day at a time, and is slow. Its
author wants a second index on `created_at`; a colleague says just reverse the existing one. Who
is right?

## Tests

Whether the candidate reasons about what a composite index is actually ordered by, and can say
which query shape each column order serves, rather than treating an index as an unordered set of
columns.

## Listen for

- The entries are ordered by the first column, then by the second within it, so one day's rows sit
  in as many separate runs as there are tenants
- Reversing it serves the export and takes away the shape the dashboard relies on — one value on
  the leading column and then a contiguous range on the next
- Both queries can be served properly, for the price of a second index that every write has to
  maintain; that is the trade, and it should be priced rather than assumed
- Is careful about which engine: MySQL uses a leftmost prefix of the index, while PostgreSQL can
  still use a multicolumn index when the leading column is unconstrained, just far less efficiently
- Asks how many tenants there are, how wide the export's range is, and how heavily the table is
  written before choosing

## Expected knowledge

- A composite index is sorted by its leading column first
- An equality on the leading column followed by a range on the next is the shape one index serves
  best

## Strong signals

- Asks whether the export could carry the tenant as well, which makes the question disappear
- Prices the second index against the write rate of a table that takes every event
- Says what the reversed index would do for the dashboard rather than asserting it would break —
  it would read a day and discard the other tenants

## Weak signals

- Says the order of columns in an index does not matter
- Adds the second index with nothing said about maintaining it
- Says the engine will work it out

## Answer bands

### weak

- Treats the two column orders as equivalent.
- Proposes indexing each column on its own and expects that to cover both queries.
- Cannot say why the dashboard is quick and the export is not.

### junior

- Says the existing index leads with the tenant, so a query that does not mention the tenant
  cannot use it the way the dashboard does.
- Sees that a second index would help the export.

### mid

- Describes the ordering inside the index and why a range on the second column alone has nothing
  contiguous to read.
- Says reversing it moves the problem onto the dashboard instead of solving both.
- Names what a second index costs on a table that is written to constantly.

### senior

- Says what the engine in front of them actually does when the leading column is unconstrained,
  rather than quoting one rule for all databases.
- Asks for the tenant count, the range width and the write rate before recommending either option.
- Offers the third answer: change the export so it carries the tenant and no new index is needed.
- Says how they would decide it was working, and what they would watch afterwards.

## Follow-ups

- The export selects only the two columns that are already in that index and nothing else. Does
  anything change?
  probes: index-only reads, and what PostgreSQL additionally needs before it can serve one
- There are four tenants and one of them is ninety per cent of the rows. Does your advice hold for
  that tenant's dashboard?
  probes: selectivity of the leading column, and whether an index is worth using for a large share
  of the table
- The table takes fifty thousand inserts a minute. How does that weigh against adding the second
  index?
  probes: write amplification as the deciding cost rather than a footnote

## Sources

- https://www.postgresql.org/docs/current/indexes-multicolumn.html
- https://dev.mysql.com/doc/refman/8.4/en/multiple-column-indexes.html
- https://www.postgresql.org/docs/current/indexes-index-only-scans.html

## Notes

The honest answer is "neither, or both, depending on numbers nobody has given you" — the card
rewards asking for them.

The engine difference is worth hearing and worth releasing if they do not: MySQL's manual describes
the leftmost prefix rule, while PostgreSQL's states that a multicolumn btree can be used even when
the leading columns are unconstrained, though it will scan much more of the index than it would
otherwise. A candidate stating the MySQL rule as universal is common and is not a fail; stating it
as universal *after* being told the system is PostgreSQL is a different matter.
