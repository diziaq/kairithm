---
id: database-query-performance-plan-row-estimates-01
schema_version: 2
title: The plan ignores the index and scans the table
category: database
topic: query-performance
level: mid
tags: [performance, observability]
time_estimate_min: 8
order: 200
links:
  deeper: [database-query-performance-plan-flipped-overnight-01]
---

## Ask

A nightly report takes 40 seconds. There is an index on `created_at`, and the plan shows a
sequential scan over the whole table instead. A developer wants to force the database to use the
index. Before you agree — what do you want to see, and which numbers in that plan would change
your mind?

## Tests

Whether the candidate reads a plan for evidence — what was expected against what actually
happened — instead of treating a full scan as a defect to be overridden.

## Ideal minimal answer

In PostgreSQL ask for `EXPLAIN ANALYZE` and compare each node's expected row count with the rows
it actually produced; a large gap is the thing to explain first. Ask what share of the table the
filter keeps, since a full read beats chasing rows one by one — and read the filter text,
because a function around the column cannot match a plain index on it.

## Listen for

- Asks for a plan with real execution figures rather than the costs alone; in PostgreSQL that is
  `EXPLAIN ANALYZE`, which runs the statement
- Compares the expected row count of a node against the row count it actually produced, and
  treats a large gap as the thing that has to be explained first
- Asks what fraction of the table survives the filter, because a filter keeping a fifth of the
  rows is cheaper to read in bulk than to chase one row at a time
- Reads the filter itself: a column wrapped in a function, or compared against a value of another
  type, cannot be matched to a plain index on that column
- Points at the node where the time was actually spent instead of the first alarming word in the
  output
- Asks how long the report is allowed to take and how often it runs, before spending a day on it

## Expected knowledge

- An index lookup fetches rows one by one and a scan reads them in bulk, so there is a crossing
  point past which reading everything wins
- The choice is made on estimated cost, and those estimates come from a sample of the table taken
  at some earlier moment, not from the data at run time
- Plain `EXPLAIN` in PostgreSQL prints estimates only; the real figures from the run itself need
  `EXPLAIN ANALYZE`

## Strong signals

- Asks whether the estimate was wrong, or the estimate was right and the query genuinely touches
  that much data — two different problems with two different fixes
- Notices the loop count on an inner node and multiplies before believing a per-loop time, because
  PostgreSQL reports the average of one loop
- Asks for buffer counts to tell a cold cache apart from a genuinely expensive plan
- Keeps the before figure and says what they will measure again after the change

## Weak signals

- Treats a full scan as a fault in itself
- Reaches for a hint or a rewrite before looking at any row count
- Reads only the total cost printed at the top
- Cannot say where the 40 seconds went

## Answer bands

### weak

- Says the database is ignoring the index and should be forced to use it.
- Calls the scan the problem without asking how many rows come out of it.

### junior

- Asks to see the plan and can point at which node consumed the time.
- Accepts that reading a table in bulk is not automatically the wrong choice.

### mid

- Compares expected rows against produced rows on the slow node and says what a large gap implies.
- Asks what share of the table the filter keeps, and accepts a full read when that share is large.
- Spots that a function applied to the column in the filter stops the plain index from matching.

### senior

- Separates a bad estimate from an honest estimate of an expensive query, and treats them apart.
- Reads per-loop figures and cache behaviour rather than the headline cost.
- Repairs the query or the sample the database holds before overriding the choice, and says what
  the override would cost the next person to touch this.

## Follow-ups

- The same report finishes in a second on a copy of the data on your laptop, with the same shape
  of plan. What do you want to know about the two machines?
  probes: data volume, cache state, and whether the two servers hold the same sample of the table
- One node says it expected one row from the filter and handed back two million. Where does a
  claim like that come from, and what makes it go bad?
  probes: where the estimate originates, and staleness after a bulk change
- The hint goes in, the report drops to four seconds, everyone goes home. Six months later it is
  slow again. What happened in between?
  probes: a frozen choice surviving a change in the data, and who owns it now
- The report runs once a night and is allowed a five-minute window. Does any of this still matter?
  probes: whether the candidate can stop, and size the effort against the requirement

## Sources

- https://www.postgresql.org/docs/current/using-explain.html
- https://www.postgresql.org/docs/current/indexes-expressional.html
- https://dev.mysql.com/doc/refman/8.0/en/index-hints.html

## Notes

Figures to release when the candidate asks, and credit the asking:

- The table is `orders`, 44 million rows, and the index is on `created_at`.
- The query filters `WHERE date(created_at) = current_date - 1`. This is the point of the card:
  the function around the column means the index on the bare column cannot be matched. PostgreSQL
  would need an index on the expression, or the filter rewritten as a half-open range on the raw
  column. A candidate who asks to see the query text, not only the plan, has found it.
- From the plan: the filter node estimates 1 row and returns 2.4 million; `Rows Removed by Filter`
  is 41.6 million; roughly 90% of the 40 seconds is in that node.
- The report runs once a night and has a five-minute window. Credit a candidate who then
  de-escalates rather than tuning for its own sake.

Engine pin: everything above is PostgreSQL. Core PostgreSQL has no index hint syntax at all —
forcing a plan means the `pg_hint_plan` extension or crude tricks with the cost settings. MySQL
has `FORCE INDEX` and SQL Server has index hints. A candidate who says "you cannot force it here
anyway" is right for PostgreSQL and is worth following up on.
