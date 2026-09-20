---
id: database-column-oriented-orders-in-bigquery-01
schema_version: 1
title: Orders as they happen, in BigQuery
category: database
topic: column-oriented
level: senior
tags: [data-modelling, performance, operations]
time_estimate_min: 9
order: 330
---

## Ask

A team wants to move their orders table into BigQuery and make it the only place orders live. An
order is inserted, then edited four or five times as it moves through fulfilment, and the order
screen looks one order up by its id. They say BigQuery is cheaper and faster than what they have.
Where does this go wrong?

## Tests

Whether the candidate can take a transactional workload, lay it against an analytical store's
physical design, and name exactly which operations become expensive and why.

## Listen for

- Editing one order is not an edit in place: the data sits in large blocks that get rewritten
- Four or five edits per order means the most expensive operation in that store is on the normal
  path, not the rare one
- Fetching one order by id is a seek, and an analytical engine is built to sweep, so the layout
  has to be arranged around that id before it is anything but a sweep
- Asks what response time the order screen needs, and compares it with the floor of a query on an
  analytical engine
- Knows that mutating rows is metered and limited differently from appending them, and that the
  limits favour appends
- Proposes keeping orders where they can be edited and feeding a copy in for analysis
- Asks what the team was actually unhappy about, since "cheaper and faster" is a symptom of
  something

## Expected knowledge

- Analytical stores hold data in large blocks written once; altering one value rewrites a block
- Partitioning and clustering are the physical arrangement of a table; they decide what can be
  skipped, and they are not a lookup structure on a key

## Strong signals

- Proposes the split concretely and says how fresh the copy must be and who notices when it is
  not
- Treats the amount of data a query sweeps as a cost line, because that is what is billed
- Distinguishes an append-only history of order events from a mutable current-state table, and
  notices the first fits the store far better

## Weak signals

- Approves it because BigQuery handles enormous volumes
- Compares only the price of storage between the two options
- Treats it as a swap of connection details

## Answer bands

### weak

- Approves the move because the store handles enormous volumes.
- Quotes a lower price and stops there.
- Treats it as changing where the application points.

### mid

- Says frequent single-order edits are the expensive operation in this kind of store, and there
  are several per order.
- Says looking one order up by id is not the access this store is built around.
- Suggests keeping the existing store for the live orders and copying into the new one.

### senior

- Describes data held in large blocks that are rewritten rather than altered in place, and prices
  the edit against that.
- Asks what the order screen must answer in, and compares that with what an analytical engine
  takes to answer anything at all.
- Explains how the arrangement of the table on disk decides what a filter can skip, and why a
  single-id fetch gains little from it unless the table is arranged around that id.
- Names what is actually billed and how the proposed traffic interacts with it.

### lead

- States the split as a decision: the editable copy stays where it is, a derived copy goes into
  the analytical store, and freshness is a stated number.
- Says who owns the copy, how it is rebuilt, and what breaks while it is being rebuilt.
- Goes back to what the team was trying to fix and says whether the split still fixes it.

## Follow-ups

- Suppose an order were inserted once and never touched again. Does your answer change?
  probes: whether they isolate mutation from the rest, and still catch the single-id fetch and
  the latency floor
- The team says they will never edit anything: they will append a new row per change and read the
  newest one back at query time. What have they bought, and what have they paid?
  probes: append-and-reduce as a workaround, and the work it moves onto every read
- The order screen has a hard budget of a hundred milliseconds. How does that land?
  probes: the per-query floor of an analytical engine against a point read in a row store
- Their analysts currently wait ninety seconds for a report and that is the real complaint. Where
  does that leave the proposal?
  probes: whether they can separate the problem worth solving from the solution that arrived
  attached to it

## Notes

Figures to release when asked, and credit the candidate who asks: about 50,000 orders a day,
kept for seven years; the order screen is targeted at 100 ms; analysts run roughly 200 reports a
day over the whole history; the current store is a single PostgreSQL instance.

BigQuery's quotas around mutating statements have changed repeatedly — the old per-table daily
cap on such statements was removed, and current limits are concurrency-shaped. Do not hold a
candidate to a number; the shape of the constraint, that appends are the cheap path and
mutations are not, is what the card is testing.

NEEDS-REVIEW — unverified claim about the exact current BigQuery limits on mutating statements;
the card deliberately states only the shape, but check the quotas page before quoting figures to
a candidate.

## Sources

- https://cloud.google.com/bigquery/docs/partitioned-tables
- https://cloud.google.com/bigquery/docs/clustered-tables
- https://cloud.google.com/bigquery/quotas
