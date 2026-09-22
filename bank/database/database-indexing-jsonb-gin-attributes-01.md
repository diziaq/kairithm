---
id: database-indexing-jsonb-gin-attributes-01
schema_version: 2
title: A GIN index over a jsonb column on a table taking 4,000 writes a minute
category: database
topic: indexing
level: senior
tags: [performance, data-modelling, operations, maintainability]
time_estimate_min: 10
order: 680
links:
  related: [database-document-stores-review-array-grows-01]
---

## Ask

A product table on PostgreSQL 17 keeps its variable attributes in a `jsonb` column. Search filters
on those attributes with the containment operator and is slow. Someone has proposed a GIN index
on the column, one line, ship it Friday. The table takes about four thousand writes a minute.
What do you want settled before that goes in?

## Tests

Whether the candidate can price an index whose per-row cost is not one entry but many, and choose
between the available operator classes from the queries rather than taking the default.

## Ideal minimal answer

It will serve containment, but one row produces an entry per key and value under the default
class, so the write cost is the question, not the read gain. New entries also land on an unsorted
pending list that is folded in later, which trades a steady response time for periodic bursts.
If only containment is used, the other class stores one hashed entry per value and is smaller.

## Listen for

- Says the cost of this index is not one entry per row: the default class produces an independent
  entry for every key and every value in the document, so a document with thirty attributes costs
  sixty
- Asks what the search actually does — containment only, or also asking whether a key is present
  at all — because the answer decides which class is available
- Knows there are two classes and what separates them: one indexes keys and values separately and
  supports the key-presence operators; the other stores a hash of the value together with the path
  to it, supports fewer operators, and is usually much smaller and more selective
- Raises the pending list: new entries are held in an unsorted area and moved into the structure
  in bulk later, so inserts are cheap and the fold-in is not, and it lands on whoever triggers it
- Says that behaviour can be turned off per index if a steady response time matters more than
  insert speed
- Asks what fraction of queries this index is for, because a structure maintained on every write
  should not exist for a page nobody visits
- Asks whether the attributes are genuinely variable, or whether two or three of them are on every
  row and always filtered on

## Expected knowledge

- An inverted index stores one entry per extracted key, so one row can cause many insertions
- The default class for a document column is not always the right one, and changing it requires
  rebuilding

## Strong signals

- Proposes pulling the two or three universal attributes into real columns with ordinary indexes
  and leaving the rest in the document
- Says an expression index on one extracted attribute is a third option and is far cheaper when
  the query only ever asks about that one
- Wants the bulk load planned around the index — dropped and rebuilt rather than maintained — and
  knows the build is sensitive to the memory setting
- Notices the fold-in is also done by the cleanup daemon, so the two subjects are connected and
  the daemon's schedule is part of the answer
- Asks for the index size on a restored copy before agreeing to anything

## Weak signals

- "Just add the index, it is one line"
- Treats the column as free-form because the schema does not constrain it, and never asks what the
  queries look like
- Proposes indexing every attribute individually
- Says the document store would have been faster, without a measurement
- Lists the two classes with correct trade-offs and will not pick one

## Answer bands

### mid

- Says the index will help the search and asks what it costs on write.
- Knows one row can produce many entries in this kind of index.
- Does not distinguish the classes or does not raise the pending list.

### senior

- Raises the question of which operators the search uses before choosing, and picks the class from
  the answer.
- Explains the per-key and per-value cost concretely, in entries per row at the stated write rate.
- Raises the pending list and says what it trades and how to turn it off.
- Says how they would measure the index size and the write cost before Friday.

### lead

- Decides how much of the document should stay a document at all, and which attributes become
  columns.
- Says who owns the shape of that column, given nothing in the schema constrains it today.
- Prices the index against the pages it serves, and is willing to say the search should be
  narrowed instead.
- Plans the rollout: build it without holding writes, measure, and say what would make them
  remove it again.

## Follow-ups

- Search picks up a filter that asks only whether a given attribute is there at all, with no
  value. Does what you chose still serve it?
  probes: the class that drops key-presence support, and whether they remember they gave it away
- The team cares about a steady ninety-ninth percentile and the writes arrive in bursts. What do
  you change?
  probes: the pending list as a latency trade, and who pays for the fold-in
- Two of these attributes are on every single product and are always filtered on. Would you index
  those the same way?
  probes: pulling stable fields into columns, or an expression index, instead of the whole column
- A bulk load of nine million rows is planned for Saturday night. Does that affect anything you
  have said?
  probes: dropping and rebuilding rather than maintaining, and the memory the build depends on

## Sources

- https://www.postgresql.org/docs/current/gin.html
- https://www.postgresql.org/docs/current/datatype-json.html
- https://www.postgresql.org/docs/current/functions-json.html
- https://www.postgresql.org/docs/current/runtime-config-client.html
- https://www.postgresql.org/docs/current/sql-createindex.html

## Notes

Written from the PostgreSQL manual, because this ground is not covered anywhere else in the bank
and is easy to get half-right from memory.

The two classes, verbatim from the `jsonb` documentation: the default `jsonb_ops` "supports
queries with the key-exists operators `?`, `?|` and `?&`, the containment operator `@>`, and the
jsonpath match operators `@?` and `@@`", and "creates independent index items for each key and
value in the data". The non-default `jsonb_path_ops` "does not support the key-exists operators,
but it does support `@>`, `@?` and `@@`", and "creates index items only for each value in the
data... each `jsonb_path_ops` index item is a hash of the value and the key(s) leading to it". The
manual's own summary: "A `jsonb_path_ops` index is usually much smaller than a `jsonb_ops` index
over the same data, and the specificity of searches is better."

Its one documented hole is worth releasing to a strong candidate: `jsonb_path_ops` "produces no
index entries for JSON structures not containing any values, such as `{"a": {}}`", so a search
for such a document falls back to a full scan of the index.

The pending list, from the GIN chapter: "Updating a GIN index tends to be slow because of the
intrinsic nature of inverted indexes: inserting or updating one heap row can cause many inserts
into the index (one for each key extracted from the indexed item). GIN is capable of postponing
much of this work by inserting new tuples into a temporary, unsorted list of pending entries."
Those entries move into the main structure "when the table is vacuumed or autoanalyzed, or when
`gin_clean_pending_list` function is called, or if the pending list becomes larger than
`gin_pending_list_limit`" — which defaults to 4 MB. And: "If consistent response time is more
important than update speed, use of pending entries can be disabled by turning off the
`fastupdate` storage parameter."

For the Saturday load: "for bulk insertions into a table it is advisable to drop the GIN index and
recreate it after finishing bulk insertion", and "build time for a GIN index is very sensitive to
the `maintenance_work_mem` setting".

Figures to release when asked: about 40 million rows; a typical document has 25 to 40 attributes;
the search page is roughly 3 per cent of traffic; nobody has measured what the index would weigh.
That last figure is the one a good candidate asks for first, and it usually ends the argument.
