---
id: database-indexing-partial-index-pending-queue-01
schema_version: 2
title: 300 rows in 200 million, and the worker waits eight seconds
category: database
topic: indexing
level: senior
tags: [performance, data-modelling, operations]
time_estimate_min: 10
order: 640
links:
  shallower: [database-indexing-too-many-indexes-01]
---

## Ask

A 200-million-row queue table on PostgreSQL holds 300 rows in state `pending`. The worker runs
`WHERE status = 'pending' ORDER BY created_at LIMIT 10` and it takes eight seconds. There is
already an index on `status`. A reviewer says `status` has four distinct values, so indexing it
was the mistake in the first place. What do you do?

## Tests

Whether the candidate can recognise that the familiar rule about low-cardinality columns is a
statement about even spread, and design an index that answers the filter and the ordering in one
small structure.

## Ideal minimal answer

The rule assumes the four values are spread across the table; 300 rows in 200 million is not that
case, and the planner is choosing a full scan because its estimate for `pending` is wildly high.
Build the index over only the pending rows, keyed on `created_at`: 300 entries that give the
filter and the ordering together and cost nothing to maintain.

## Listen for

- Says the advice about few distinct values is really advice about even spread, and this column is
  not evenly spread
- Wants the plan before anything else, and expects to find a full scan with a top-ten sort rather
  than a use of the existing index
- Explains why: the engine's estimate for a rare value comes out far too high, so it prices the
  index as returning tens of millions of rows and declines it
- Proposes an index restricted to the rows in that state, keyed on the ordering column, and says
  what that buys: the filter is implied by the index existing, and the entries are already in the
  order the query wants, so there is no sort and no limit to apply after one
- Says the structure holds hundreds of entries, not millions, so it stays in cache and costs
  almost nothing per write
- Points out that a row leaving the state leaves the index, so it self-trims and never grows with
  the table
- Asks what the worker does after it reads the ten rows, because a queue read by several workers
  is a different question from an index question

## Expected knowledge

- An index can be defined over a subset of rows, and the engine will only use it for a query it
  can prove stays inside that subset
- An index provides an ordering, so a query whose sort matches the index does not need a sort step

## Strong signals

- Asks whether the worker's statement carries the state as a literal or as a parameter, because
  the engine matches the restriction at planning time
- Raises several workers racing for the same ten rows and reaches for a clause that skips rows
  another worker already holds
- Notices the existing index on the column can be dropped once the restricted one is in, and says
  what the other three states are queried by
- Says what happens if the queue ever backs up to two million rows, and whether the answer still
  holds then
- Asks whether a table that is 99.9999 per cent finished work should be a queue table at all

## Weak signals

- Agrees with the reviewer and drops the index, because the rule says so
- Adds a two-column index and stops, without saying what the estimate problem was
- Raises the statistics target on the column and expects the ordering to sort itself out
- Proposes reading the whole table into the application and filtering there
- Lists the options accurately and declines to recommend one

## Answer bands

### mid

- Says 300 rows out of 200 million is the opposite of the case the rule is about.
- Proposes an index covering both the state and the timestamp.
- Does not say why the existing index was not being used.

### senior

- Asks for the plan and predicts what is in it before being shown.
- Explains the estimate for a rare value, and that the engine declined the index rather than
  failing to find it.
- Restricts the index to the rows in that state without being pointed at it, and says it serves
  the ordering as well as the filter.
- Says what the structure costs per write and that it does not grow with the table.

### lead

- Asks how the statement reaches the server before promising the index will be used.
- Decides what happens when several workers read the queue at once, and whether that belongs in
  this change.
- Says what to watch after the change, and what would tell them the queue has outgrown the design.
- Weighs keeping the old index against dropping it from what else queries that column.

## Follow-ups

- The worker is a prepared statement and the state arrives as a parameter rather than being
  written into the text. Does that change what you promised?
  probes: matching happens at planning time and a parameter may not be provable
- Four workers run this on a timer, ten seconds apart. What do they do to each other?
  probes: several readers taking the same rows; skipping rows another holds; the lock duration
- A bad afternoon leaves two million rows in that state instead of 300. Does your answer still
  stand?
  probes: whether the design was tuned to one number, and what degrades first
- The reviewer wants to see the number that justified it. What do you show him?
  probes: comparing plans and timings rather than asserting the rule back at him

## Sources

- https://www.postgresql.org/docs/current/indexes-partial.html
- https://www.postgresql.org/docs/current/indexes-ordering.html
- https://www.postgresql.org/docs/current/row-estimation-examples.html
- https://www.postgresql.org/docs/current/sql-select.html
- https://www.postgresql.org/docs/current/planner-stats.html

## Notes

The manual's own framing: "One major reason for using a partial index is to avoid indexing common
values... This reduces the size of the index, which will speed up those queries that do use the
index. It will also speed up many table update operations because the index does not need to be
updated in all cases." Its Example 11.2 is this exact shape — a table of billed and unbilled
orders where "the unbilled orders take up a small fraction of the total table and yet those are
the most-accessed rows."

The subtlety worth the strong-signal credit, straight from the same page: "a partial index can be
used in a query only if the system can recognize that the WHERE condition of the query
mathematically implies the predicate of the index... Matching takes place at query planning time,
not at run time. As a result, parameterized query clauses do not work with a partial index." A
worker whose statement is prepared with the state as a parameter can therefore fail to get the
index the candidate has just designed. Release this only after they have proposed the index.

Figures to release when asked, and credit the asking:

- The plan is a parallel sequential scan with a top-ten sort. The estimate for `status = 'pending'`
  is about 50 million rows; the actual is 300.
- There is no index on `created_at`, so there is no ordered path for the planner to walk instead.
- Rows move to `done` and stay in the table for seven years for audit.
- Writes run at about 900 rows a minute.

`SKIP LOCKED` is the right answer to the several-workers follow-up and the manual says what it
costs: it "provides an inconsistent view of the data, so this is not suitable for general purpose
work, but can be used to avoid lock contention with multiple consumers accessing a queue-like
table."

The reviewer is repeating a rule that is usually right. The card is not about catching him out; it
is about whether the candidate can say what the rule is really about and then notice that this
table does not meet the condition.
