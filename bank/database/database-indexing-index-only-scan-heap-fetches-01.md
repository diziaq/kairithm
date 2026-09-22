---
id: database-indexing-index-only-scan-heap-fetches-01
schema_version: 2
title: It says Index Only Scan and it touches the table 2.4 million times
category: database
topic: indexing
level: senior
tags: [performance, operations, observability, failure-modes]
time_estimate_min: 10
order: 630
links:
  shallower: [database-indexing-composite-column-order-01]
---

## Ask

A PostgreSQL plan says `Index Only Scan`, and the line under it says `Heap Fetches: 2418332`. The
query takes nine hundred milliseconds. The author's position is that the index already covers
every column the query selects, so the scan is as good as it gets and there is nothing left to
tune. Is he right?

## Tests

Whether the candidate can read a plan node that names one mechanism while reporting that the
mechanism did not apply, and follow the cause out of the index and into the table's upkeep.

## Ideal minimal answer

The scan is doing what it claims; it still went to the table 2.4 million times, because those
pages are not marked as holding only rows every reader can see. Vacuum sets that mark and is
being outrun by the write rate. The index covers the query — the table's upkeep does not, and
another column on the index will not change it.

## Listen for

- Names what the plan node is actually saying: the entries were found in the index, and for most
  of them the engine still had to open the table page to decide whether the row should be seen
- An index in PostgreSQL does not record which readers may see a row, so the engine consults a
  per-page map of pages known to hold only rows visible to everyone
- That map is maintained by vacuum, so a heavily written table has most of its pages unmarked and
  a scan that is nominally index-only pays a table visit per entry
- Concludes the cost is in the table's upkeep, not in the index definition, and that adding
  columns to the index cannot help
- Says what to change: make the daemon run on this table far more often, or accept the shape is
  wrong for a table written at this rate
- Wants the count of visits compared against the row count, because the ratio is the measurement,
  not the raw figure
- Asks whether anything is holding the reclaim point back, since a table can be vacuumed
  constantly and still have nothing marked

## Expected knowledge

- A plan node names the strategy chosen, not the work actually avoided
- The map is consulted per page, so one recently written row spoils the page for every entry that
  points into it

## Strong signals

- Asks for the write rate and the update pattern before proposing anything
- Points out that an update that leaves the indexed columns alone is cheaper, and that a fill
  factor below the default gives those updates somewhere to go on the same page
- Says the same index on a table that stops changing becomes fast with no change to the index at
  all, and offers that as the test
- Notices that a long-open transaction elsewhere in the cluster would produce this symptom with
  the daemon running flat out, and says how to rule it out
- Prices running the daemon harder against the write throughput it competes with

## Weak signals

- Adds the remaining columns to the index as payload and expects the visits to drop
- Rebuilds or reindexes, reports it fixed once the cache is warm
- Reads the node's name as proof the table was not touched
- Concludes PostgreSQL is lying and moves the query to the application
- Lists three possible causes with fair trade-offs and will not say which one to chase first

## Answer bands

### mid

- Says the number under the node means the table was visited anyway, so the scan is not free.
- Knows the index alone cannot decide whether a row should be seen.
- Suggests running the cleanup on that table, without saying what it is for here.

### senior

- Explains the per-page mark and who maintains it unasked, and ties the figure to the write
  rate.
- Says adding columns to the index cannot reduce the visits, and why.
- Compares the visit count to the rows returned rather than reacting to a large number.
- Proposes a change to the table's upkeep and names how they would know it worked.

### lead

- Decides whether this query should be served this way at all given the write rate, rather than
  tuning it.
- Weighs the cost of running the daemon aggressively on this table against the writes it slows.
- Says how the team catches the next plan whose name flatters it, without reading every plan.
- Owns the setting: puts it on the table, writes down why, and says what would make it wrong.

## Follow-ups

- The same query takes forty milliseconds at seven in the morning and nine hundred by lunchtime,
  every day. What does that tell you?
  probes: whether they tie the swing to the upkeep pass rather than to a warm cache
- The author offers to put the remaining two columns into the index as payload. Where does that
  get him?
  probes: whether they see that covering more columns does not remove the table visit
- The table takes eighteen thousand updates a minute and every row is changed within an hour of
  arriving. Does your advice survive that?
  probes: whether they conclude the shape is wrong here rather than under-tuned
- You set it up and a week later the figure is unchanged, with the daemon running on that table
  around the clock. What now?
  probes: something else holding the reclaim point back across the whole cluster

## Sources

- https://www.postgresql.org/docs/current/indexes-index-only-scans.html
- https://www.postgresql.org/docs/current/routine-vacuuming.html
- https://www.postgresql.org/docs/current/using-explain.html
- https://www.postgresql.org/docs/current/storage-vm.html
- https://www.postgresql.org/docs/current/storage-hot.html

## Notes

The manual is explicit on both halves. On the map: vacuum "maintains a visibility map for each
table to keep track of which pages contain only tuples that are known to be visible to all active
transactions", and an index-only scan "checks the visibility map first. If it's known that all
tuples on the page are visible, the heap fetch can be skipped." On when it pays: index-only scans
are a win "only if a significant fraction of the table's heap pages have their all-visible map
bits set", and "there is little point in including payload columns in an index unless the table
changes slowly enough that an index-only scan is likely to not need to access the heap."

The `Heap Fetches:` line is standard `EXPLAIN (ANALYZE)` output under an `Index Only Scan`; the
manual's own example shows it reading zero.

Figures to release when asked:

- The scan returns about 2.6 million rows, so nearly every entry cost a table visit.
- The table takes roughly 18,000 updates a minute and has an `autovacuum_vacuum_scale_factor` left
  at the instance default.
- The index was added a month ago with `INCLUDE` columns specifically to make this query
  index-only, and the author measured it on a restored copy that was not being written to.

That last point is the whole card in one line: the change was correct and was measured on a table
where the map was fully set, which is exactly the condition production does not have.

Two answers that are right and less common: lower the table's own vacuum scale factor so the
daemon visits it on a much smaller number of changed rows, and lower the fill factor so updates
stay on the page and leave more of the table undisturbed. A candidate who reaches for a long-open
transaction elsewhere as the alternative explanation has connected this card to the one about the
reporting connection, which is the intended pairing.
