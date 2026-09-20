---
id: database-column-oriented-select-star-dashboard-01
schema_version: 1
title: The dashboard asks for all three hundred columns
category: database
topic: column-oriented
level: mid
tags: [performance, data-modelling, scalability]
time_estimate_min: 7
order: 320
links:
  deeper: [database-column-oriented-orders-in-bigquery-01]
---

## Ask

A dashboard tile over a ClickHouse table of two billion events takes forty seconds. The table is
three hundred columns wide. The query is `SELECT * FROM events WHERE day = today()`, and the
dashboard then adds up one field in application code. What do you change first, and why does it
help?

## Tests

Whether the candidate knows what an analytical store actually pulls off disk for a given query,
and reaches for the field list before reaching for hardware.

## Listen for

- Asking for every field defeats the one thing this kind of store is built to do, which is to
  touch only what was named
- Do the addition in the query and send back one row, instead of shipping a day of rows to the
  caller
- Values of a single field sit next to each other on disk and squeeze down well because they look
  alike; a full-width read gives that up
- Asks how the table is arranged and split by day, so the filter can skip whole parts instead of
  reading and discarding them
- Keeps the bytes lifted off disk separate from the bytes pushed over the network, and says which
  one is hurting here

## Expected knowledge

- A column store keeps the values of one field side by side; a row store keeps one record side by
  side
- Values that resemble each other squeeze down far better than values that do not

## Strong signals

- Estimates the size of the read before and after the change instead of guessing
- Says the same fix would help much less on a row-oriented store, and explains why

## Weak signals

- Reaches first for more nodes, more memory or a faster disk
- Suggests keeping fewer days of data as the opening move
- Says "add an index" without saying what would then be read

## Answer bands

### weak

- Proposes more hardware, more nodes or more memory as the first move.
- Says two billion is simply too many and suggests throwing rows away.
- Leaves the query itself untouched.

### junior

- Notices the query asks for far more fields than the tile displays.
- Names the fields the tile needs and asks only for those.
- Lets the store do the addition so one row comes back.

### mid

- Says this kind of store fetches per field, so the width of the request sets how much is lifted
  off disk.
- Separates the volume read from the volume transferred, and says both drop here.
- Notes that the remaining two hundred and ninety four fields cost nothing once they are not
  asked for.

### senior

- Explains that values of one field sit adjacent and squeeze down because they resemble each
  other, and that a full-width read forfeits both effects.
- Asks how the table is laid out and divided by day, and whether the filter lets whole parts go
  unread rather than being read and thrown away.
- Puts rough numbers on the two versions and says which change he expects to dominate.

## Follow-ups

- The tile is fixed, names its six fields and now answers in under a second. The product owner
  asks for a screen showing one whole event by its id. What do you expect?
  probes: whether they see a point lookup as the awkward case here, and what reassembling one row
  costs
- A new field is added to the table every week and it is now four hundred wide. Does that alone
  make the fixed query slower?
  probes: whether they know an unnamed field is never touched
- Half the forty seconds turns out to be the caller looping over the rows it received. Does that
  change what you fix?
  probes: whether they can tell a storage problem from a transport and deserialisation problem

## Notes

Figures to release when asked, and credit the candidate who asks: two billion rows total, about
sixty million for today; six of the three hundred fields are shown; the sum is over one numeric
field; the dashboard refreshes every thirty seconds for around forty users.

Both changes matter and the candidate should get to both: naming the fields cuts what is read,
aggregating in the query cuts what is sent. A candidate who only does one has half the answer.

## Sources

- https://clickhouse.com/docs/en/intro
- https://parquet.apache.org/docs/file-format/
