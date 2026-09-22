---
id: http-pagination-export-misses-rows-01
schema_version: 2
title: The export that is two per cent short
category: http
topic: pagination
level: mid
tags: [correctness, consistency, api-design]
time_estimate_min: 8
order: 145
links:
  deeper: [http-pagination-jump-to-page-five-hundred-01]
  related: [database-indexing-composite-column-order-01]
---

## Ask

A nightly export walks `/orders?page=N&size=100` until it gets an empty page. Finance says the
file is missing about two per cent of yesterday's orders and has a handful of them twice.
Nothing errored, no page was skipped, and the endpoint sorts by the order's creation time. What
is happening?

## Tests

Whether the candidate can see that each page is an independent query over a set that is moving,
and name a paging scheme that does not depend on counting from the start.

## Ideal minimal answer

Each page is a separate query and rows are being written between them, so a position counted
from the start points somewhere different each time: a row that shifts earlier gets read twice
and one that shifts later is never read. Page by carrying the last row's key forward, with a
unique column in the ordering so it is total.

## Listen for

- Each page is its own query; nothing holds the result still between them
- Rows inserted ahead of the position push everything down, so one row is read twice and another
  is stepped over — with no error anywhere
- Sorting on a column that is not unique leaves ties in an arbitrary order that can differ
  between queries, which produces the same symptom with no writes at all
- Carry the last row's sort value forward and ask for what comes after it, adding a unique
  column so the ordering is total
- Says what the new scheme gives up: no jumping to an arbitrary position
- Notices the cost as well as the correctness — the skipped rows are still produced by the
  server before being thrown away

## Expected knowledge

- Rows stepped over by a position are still computed and then discarded
- An ordering that does not identify a single row order is not repeatable

## Strong signals

- Asks whether the export could simply be bounded — everything created yesterday, a closed range
  — which removes the moving set entirely and is the cheapest fix available
- Says the carried key has to cover every column in the ordering, and that an index has to match
  it or the endpoint gets slower as it goes
- Raises holding one consistent read open as the alternative, and prices what a long read costs
  on a busy table
- Asks whether the missing rows and the duplicated rows are the same rows, because that would
  point somewhere else entirely

## Weak signals

- Raises the page size
- Wraps the whole export in one transaction with no statement of what that does to a live table
- Removes duplicates on the client and calls the shortfall a separate bug
- Retries the export
- Blames the two per cent on rows created after the export started, without checking

## Answer bands

### weak

- Suggests a bigger page or a retry.
- Cannot connect ongoing writes to pages that overlap and skip.

### junior

- Says rows are being inserted while the export runs, so the pages shift.
- Explains how that produces both a duplicate and a miss.

### mid

- Proposes carrying the last row's key forward instead of counting from the start.
- Adds a unique column to the ordering and says why.
- Names what the new scheme cannot do, once asked who will miss it.

### senior

- Volunteers the non-unique ordering as a second, independent cause and says it would show the
  same symptom on a quiet night.
- Offers the bounded range as the simpler fix before the more elaborate one.
- Says what index the new query needs, and what happens without it.

## Follow-ups

- Suppose nothing at all was written last night. Could this still have happened?
  probes: a non-unique ordering and an unstable tie order, independent of any writes
- Somebody proposes holding one long read open for the whole forty minutes. What does that cost
  on a live table?
  probes: whether they can price a long-lived consistent read rather than just naming it
- Your new scheme means the caller can no longer ask for page three hundred. Who is going to
  complain, and what do you offer them?
  probes: naming what was given up, out loud, rather than pretending it is free
- Rows can also be deleted overnight. Does that change your answer?
  probes: the shift going the other way, and whether the carried key still holds

## Sources

- https://www.postgresql.org/docs/current/queries-limit.html
- https://www.postgresql.org/docs/current/functions-comparisons.html#ROW-WISE-COMPARISON

## Notes

Figures to release if asked: about 180,000 orders a day; the export runs 01:00–01:40 while a
partner feed writes continuously; the endpoint sorts by creation time only, and that column is
stored to the second, so ties are common; page size 100.

The two causes are independent and a strong candidate finds both. The PostgreSQL documentation
states each: "The rows skipped by an OFFSET clause still have to be computed inside the server;
therefore a large OFFSET might be inefficient", and "using different LIMIT/OFFSET values to
select different subsets of a query result will give inconsistent results unless you enforce a
predictable result ordering with ORDER BY... When using LIMIT, it is important to use an ORDER BY
clause that constrains the result rows into a unique order."

The second-granularity timestamp in the figures is deliberate: with roughly two orders a second
there are ties on nearly every page boundary, so the export would lose rows even with no
concurrent writes. A candidate who fixes only the moving-set problem and leaves the ordering
non-unique has half the answer.
