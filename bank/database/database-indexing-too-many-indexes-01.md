---
id: database-indexing-too-many-indexes-01
schema_version: 2
title: An index on every column, and the nightly import tripled
category: database
topic: indexing
level: junior
tags: [performance, operations, maintainability]
time_estimate_min: 6
order: 130
links:
  deeper: [database-indexing-composite-column-order-01]
---

## Ask

The orders page was slow, so a team put an index on every column of the table — fourteen of them.
The page is exactly as slow as it was. The nightly import that used to take twenty minutes now
takes over an hour. Tell me what they bought and what they paid.

## Tests

Whether the candidate can state both sides of an index — the reads it can serve and the write work
it adds to every row — instead of treating one as a general-purpose speedup switch.

## Ideal minimal answer

Every insert and update has to maintain all fourteen indexes, which is why the import tripled,
and an index only helps a query that filters, joins or sorts on that column — none of the
fourteen was chosen from what the page runs. Drop the ones nothing queries, and start from the
page's actual query.

## Listen for

- Every insert, every delete, and every update that touches an indexed column has to maintain each
  index, so the import's per-row work grows with the number of them
- An index only helps a query that asks a question the index can answer; one on a column nobody
  filters, joins or sorts by helps nothing at all
- Nobody established which query the page was waiting on, so there is no reason any of the fourteen
  would have helped
- They also cost disk and memory, and compete for the same cache the table wants
- Asks what the page actually queries before recommending which ones to keep

## Expected knowledge

- An index is a separate structure the engine keeps in step with the table, not a property of a
  column
- A column with very few distinct values gives an index almost nothing to narrow down

## Strong signals

- Asks for the row count and what the page filters on before saying anything else
- Knows some of the fourteen are redundant given others, and can say what makes one redundant
- Knows an update that leaves the indexed columns alone is cheaper than one that does not
  (PostgreSQL's heap-only tuple update)

## Weak signals

- "More indexes make reads faster", with no cost named at all
- Suggests indexing the primary key column as well
- Blames the import tool or the hardware

## Answer bands

### weak

- Says indexes cannot have made the import slower, because indexes make things faster.
- Proposes adding more of them, or indexing whatever columns are left.
- Cannot name anything an index costs.

### junior

- Says each one has to be kept up to date on every write, so fourteen multiply the import's work.
- Says an index is only used when a query asks about the column it covers.
- Suggests removing the ones nothing queries.

### mid

- Starts from the queries the page runs and keeps only what serves them.
- Points out that a column holding two distinct values across the whole table narrows almost
  nothing, so the index would be skipped even where it applies.
- Names the space and memory they occupy, and that the writes and the reads fight over the same
  cache.

## Follow-ups

- One of the fourteen is on a column that is either yes or no across ten million rows. Is that one
  earning its keep?
  probes: selectivity; whether an index on a column with two values narrows anything worth the
  maintenance
- They drop all fourteen. The import is fast again and the page is unchanged. What do you do next?
  probes: whether they work from the queries the page runs rather than from the columns the table
  happens to have
- The import only ever inserts; it never changes or removes a row. Does that change the bill?
  probes: which write operations touch an index at all, and whether they separate the three

## Sources

- https://www.postgresql.org/docs/current/indexes-intro.html
- https://dev.mysql.com/doc/refman/8.4/en/mysql-indexes.html
- https://www.postgresql.org/docs/current/storage-hot.html

## Notes

If the candidate asks for figures, give them: the table holds about forty million rows, the import
inserts two million a night, and the page shows one customer's last twenty orders. A candidate who
asks for those before answering is ahead of one who recites the trade-off from memory.
