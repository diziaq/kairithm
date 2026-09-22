---
id: database-schema-design-random-primary-key-01
schema_version: 2
title: The key went random and the inserts fell off a cliff, six months later
category: database
topic: schema-design
level: senior
tags: [performance, data-modelling, operations, failure-modes]
time_estimate_min: 10
order: 660
links:
  related: [database-schema-design-natural-key-not-stable-01]
---

## Ask

A high-insert table on MySQL 8.4 with InnoDB had its primary key changed from an auto-increment
integer to a random UUID kept as a 36-character string. For months nothing happened. Once the
table outgrew the buffer pool, insert throughput fell by about a third, and every index on the
table is larger than anyone budgeted for. Explain both, and say what you would do.

## Tests

Whether the candidate can reason about where a row physically lands on this engine, and connect
one key choice to write throughput, cache behaviour and the size of every other index on the
table.

## Ideal minimal answer

On this engine the table is stored in primary key order, so a sequential key always appends to
the same end page, which stays in memory. A random key lands anywhere, so each insert pulls a
cold page in, dirties it and often splits it, leaving pages part-full. And every secondary index
entry carries the primary key, so a 36-character key is repeated in all of them.

## Listen for

- Says the rows themselves live in primary key order on this engine, so the key decides where a
  new row is physically written
- With an ascending key every insert goes to the same end page: one page in cache, dirtied
  repeatedly, written once
- With a random key each insert touches a different page, which has to be read from disk if it is
  not resident — which is why nothing happened while the whole thing fitted in memory
- Names the split: a page that is full has to be divided when a row lands in the middle of it, and
  the two halves are left part-full, so the structure is larger and less of it fits in cache
- Says every secondary index entry carries the primary key so the row can be found, so a long key
  inflates every index on the table, not only the main one
- Separates the two costs of the current choice: random ordering, and 36 bytes of text where 16
  bytes of binary would do
- Names the fixes and keeps them apart: store it as fixed-length binary, or use an identifier
  whose leading bytes are a timestamp so inserts go back to one end

## Expected knowledge

- The difference between a table stored in key order and a table stored as an unordered heap with
  indexes beside it
- An index page has to be split when a row will not fit, and splits leave both halves partly empty

## Strong signals

- Asks for the buffer pool size and the table size, and locates the crossover
- Knows the engine deliberately leaves about a sixteenth of each page free, so sequential inserts
  fill pages to roughly fifteen sixteenths and random ones leave them between half and that
- Offers the built-in conversion that rearranges a version-1 identifier so the slowly varying part
  leads, and says it does nothing for a purely random one
- Says what the migration actually is — the table is the index, so changing the key rewrites the
  whole table and every index beside it — and sizes it
- Asks why the key had to be random in the first place, since the reason decides which fix applies

## Weak signals

- "UUIDs are slow" with no mechanism
- Proposes an index on the identifier column, which is what the primary key already is
- Adds RAM as the fix and does not say what happens at the next crossover
- Blames the application's insert pattern, which did not change
- Lists binary storage, a time-ordered identifier and a surrogate key without recommending one

## Answer bands

### mid

- Says a random key scatters inserts and a sequential one appends, and that this matters once the
  data is bigger than memory.
- Connects the larger indexes to the length of the key.
- Does not distinguish the two costs, or does not know the table is stored in key order here.

### senior

- Volunteers that rows live in key order on this engine, and uses that to explain both symptoms.
- Explains the crossover: nothing was wrong while the working set was resident.
- Names the page split and what it leaves behind, and connects it to the index being larger than
  expected.
- Separates the randomness from the width, and offers a fix for each.

### lead

- Chooses between a binary column, a time-ordered identifier and going back to a sequence, from
  where the key is generated and who owns that code.
- Sizes the migration in downtime and disk, knowing the whole table is rewritten.
- Says what is measured before and after, and what would say the change had not worked.
- Decides what the team does about the other four tables with the same key, and in what order.

## Follow-ups

- It ran for six months with none of this. Why did it only appear when it did?
  probes: the working set outgrowing memory as the threshold, not the number of rows
- A colleague says on the other engine we run, where rows are not kept in key order, none of this
  applies. Is he right?
  probes: whether they separate where the row lives from what the index itself does
- The identifiers have to be minted by three services before the row is written, so a counter in
  the database is out. Does that sink your fix?
  probes: reaching for an identifier whose leading part is a timestamp
- There are 400 million rows in production and the table is written to all day. What is your plan?
  probes: that the table is the index, so the change rewrites everything, and how that is staged

## Sources

- https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html
- https://dev.mysql.com/doc/refman/8.4/en/innodb-physical-structure.html
- https://dev.mysql.com/doc/refman/8.4/en/miscellaneous-functions.html
- https://dev.mysql.com/doc/refman/8.4/en/innodb-buffer-pool.html
- https://www.postgresql.org/docs/18/functions-uuid.html

## Notes

Engine pin, and it is the whole card. On InnoDB the manual says "each `InnoDB` table has a special
index called the clustered index that stores row data" and "typically, the clustered index is
synonymous with the primary key" — the row *is* the leaf. It also says outright: "In InnoDB, each
record in a secondary index contains the primary key columns for the row, as well as the columns
specified for the secondary index... If the primary key is long, the secondary indexes use more
space, so it is advantageous to have a short primary key."

The fill figures are documented and are worth crediting exactly: "When new records are inserted
into an InnoDB clustered index, InnoDB tries to leave 1/16 of the page free for future insertions
and updates of the index records. If index records are inserted in a sequential order (ascending
or descending), the resulting index pages are about 15/16 full. If records are inserted in a
random order, the pages are from 1/2 to 15/16 full."

On PostgreSQL the answer is genuinely different and a candidate who says so is right: the table is
a heap, so a random key does not scatter the *rows*, only the entries in the primary key's own
index; and a secondary index stores a tuple pointer rather than the primary key, so it does not
inflate with the key's width. The pressure is real but smaller. Do not accept the InnoDB story
recited unchanged for PostgreSQL, and do not accept "it makes no difference" either.

The fixes, and what each is for:

- `BINARY(16)` with `UUID_TO_BIN()` fixes the width, not the ordering.
- `UUID_TO_BIN(uuid, 1)` swaps the time-low and time-high parts, which the manual says "moves the
  more rapidly varying part to the right and can improve indexing efficiency if the result is
  stored in an indexed column" — but the manual also says this "assumes the use of UUID version 1
  values", so it does nothing for a version 4 random one.
- A version 7 identifier is time-ordered by construction and fixes the ordering at the source.
  PostgreSQL 18 ships `uuidv7()`; on MySQL it has to be minted by the application.
- Going back to a sequence is still on the table and should be argued for, not dismissed because
  distributed generation sounds more modern.

Figures to release when asked: the table holds about 400 million rows at 180 GB, the buffer pool
is 64 GB, inserts ran at 4,200 a second before and about 2,800 now, and there are five secondary
indexes.
