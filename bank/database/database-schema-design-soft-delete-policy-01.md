---
id: database-schema-design-soft-delete-policy-01
schema_version: 1
title: Every table has deleted_at, and every query has to remember
category: database
topic: schema-design
level: lead
tags: [data-modelling, correctness, operations, maintainability]
time_estimate_min: 10
order: 122
---

## Ask

Every table in a five-year-old schema carries `deleted_at`, and every query is supposed to filter
on it. Two incidents this quarter came from a query that did not. A user who was removed cannot
sign up again with the same address. Legal is now asking how erasure requests are handled. What do
you do?

## Tests

Whether the candidate can turn a blanket schema convention into a decision per table, driven by
what each table's data is for, what the store can enforce, and what the business is obliged to do.

## Listen for

- The forgotten filter is a property of the design, not of the two authors: the default is wrong
  unless every reader, forever, remembers to say so
- Makes the safe path the default — the live rows behind a view or a separate relation with the
  raw table renamed out of the way, row-level security in PostgreSQL, or a data layer nobody
  bypasses
- Sees that the uniqueness rule now counts rows that are supposed to be gone, and knows the
  engine-specific answer: PostgreSQL can carry a partial unique index restricted to live rows,
  MySQL has no partial index and needs a generated column or a sentinel inside the key
- Says hiding a row is not erasing it, so a legal request needs the row gone or the personal
  columns overwritten, and a flag satisfies neither
- Decides per table: an audit trail, an archive, a real delete plus an event, and history nobody
  ever reads are four different answers
- Names the running cost: the dead rows sit in every table and every index forever, and every
  query carries the filter

## Expected knowledge

- A uniqueness rule knows nothing about a flag column unless it is written into the rule
- Both engines treat absent values in a unique index as distinct from each other, so putting the
  flag in the key does not do what people expect

## Strong signals

- Splits the question per table instead of answering it once for the whole schema
- Asks who gets paged when a removed row turns up in an export, and designs so that cannot happen
  rather than so it gets reviewed
- Says what would be shown to an auditor as evidence the data is actually gone

## Weak signals

- Proposes a review rule, a checklist or a lint that everyone has to remember
- Says a real delete is never acceptable, and never addresses the legal request
- Moves everything into archive tables without saying how anything reads back out

## Answer bands

### weak

- Fixes the two queries that forgot and treats the whole class as handled.
- Says the data must never really leave, with nothing said about the request from legal.
- Suggests the application filter it out on the way to the screen.

### mid

- Points out that the default is unsafe and looks for a way to make the filtered relation the
  thing people naturally read.
- Connects the failed sign-up to the uniqueness rule counting rows that are meant to be gone.

### senior

- Decides table by table whether the row has to survive, and says what each table's data is for.
- Says what the uniqueness rule has to mean once a row can be dead, and how that is written in the
  engine actually in use.
- Separates hiding a row from destroying the personal data inside it, and says which one the
  request needs.
- Names what the dead rows cost in space and in every index that carries them.

### lead

- Sets a default plus a named exception route, and says who decides and on what evidence.
- Sequences the change so neither failure can recur while the migration is half done, and says
  what is reversible.
- Puts a retention period on the tables that keep history, with an owner, rather than keeping
  everything forever by default.
- Says what the team gives up by making the change and argues it is worth it.

## Follow-ups

- The same person signs up again the day after asking to be removed. What does the database do
  with them?
  probes: the uniqueness rule counting rows that are supposed to be gone; what a second removal of
  the same natural key means
- A report nobody has touched in three years feeds the finance close and reads the table directly.
  Does your change reach it?
  probes: every existing reader assumes the old shape; the risk of renaming a relation under them
- One of these tables records who changed what and when. Does it get the same treatment?
  probes: whether the answer is per table; append-only data has different rules from live data

## Sources

- https://www.postgresql.org/docs/current/indexes-partial.html
- https://dev.mysql.com/doc/refman/8.4/en/create-index.html
- https://www.postgresql.org/docs/current/ddl-rowsecurity.html

## Notes

The uniqueness trap is worth having ready: a unique index on `(email, deleted_at)` does not stop
two live rows, because both carry an absent value there and both engines treat absent values in a
unique index as distinct from one another. PostgreSQL 15 added `NULLS NOT DISTINCT` on unique
indexes, which changes that if the team is on a recent version; MySQL has no equivalent, and no
partial indexes either, so the usual MySQL answer is a generated column that holds the address
only while the row is live.

Do not steer the candidate into a general debate about deleting data. The question is whether they
can decide per table and name what the store will enforce for them.
