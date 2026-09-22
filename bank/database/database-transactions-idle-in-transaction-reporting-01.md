---
id: database-transactions-idle-in-transaction-reporting-01
schema_version: 2
title: Open at 08:00, closed at 18:00, and the disk kept growing
category: database
topic: transactions
level: senior
tags: [transactions, operations, performance, failure-modes]
time_estimate_min: 10
order: 620
links:
  related: [database-indexing-index-only-scan-heap-fetches-01]
---

## Ask

A reporting tool on PostgreSQL opens a transaction at 08:00 and leaves it sitting idle until
18:00. Over the day, write latency climbs on tables the report never reads, disk use grows, and
the daily log shows the cleanup daemon running and removing almost nothing. The DBA has doubled
the number of cleanup workers twice. What is really happening?

## Tests

Whether the candidate can connect one client's open transaction to storage growth on unrelated
tables, and say why running the cleanup harder is the one thing that cannot help.

## Ideal minimal answer

One open transaction holds back the point beyond which old row versions may be reclaimed, and
that point is one number for the whole cluster, not per table. So every superseded version
created since 08:00 has to be kept, the tables grow, and the daemon runs and removes nothing.
More workers cannot help. Bound the transaction, or stop the report holding one.

## Listen for

- Every update and delete leaves the earlier version of the row in place, and it can only be
  reclaimed once no transaction could still need to see it
- The oldest transaction still open decides that point, and it is a property of the cluster, so a
  report that reads one schema pins the whole database
- The daemon is running correctly and reporting honestly: it is finding dead rows and being told
  it may not remove them
- So adding workers, raising the cost limit or lowering the thresholds changes nothing, and the
  team has spent a week tuning the wrong knob
- Write latency climbs because the tables and their indexes keep growing, so the same query reads
  more pages and more of the cache is spent on space that holds nothing
- Wants the transaction bounded: a timeout that ends an idle one, splitting the report into
  statements that each stand alone, or moving it to a copy
- Asks why the tool holds a transaction at all — very often nobody turned autocommit on

## Expected knowledge

- A reclaim is blocked by visibility, not by locks; a session holding no locks at all still blocks
  it
- Reclaiming in place returns space for reuse by the same table; it does not usually return it to
  the operating system
- A replica or a slot can hold the same point back, so the open session is one of several possible
  holders

## Strong signals

- Asks whether the report is read-only, and then says it makes no difference
- Says a rewrite of the table would reclaim the space and takes an exclusive lock to do it, and
  that it treats the symptom while the cause is still holding
- Names the other holders — a physical or logical slot, a standby configured to feed back, a
  prepared transaction left behind — and says how to tell which one it is
- Wants an alarm on the age of the oldest open transaction rather than on disk use, because disk
  use is the last thing to move
- Asks what the report is for, and whether a nightly copy would serve it

## Weak signals

- Rewrites the tables, or adds disk, and closes the ticket
- Tunes the daemon harder, having already seen that it runs and removes nothing
- Blames the write rate on the busy tables, which is the one thing that did not change
- Says the database needs restarting on a schedule
- Recounts a past bloat incident without saying what to do about this one

## Answer bands

### mid

- Says the long-open transaction is the cause and the report should not hold one all day.
- Knows old row versions are kept and that something has to remove them.
- Does not explain why the daemon cannot make progress, or why unrelated tables are affected.

### senior

- Says without being led there that the reclaim point is held cluster-wide by the oldest open
  transaction, and uses that to explain the unrelated tables.
- Says the daemon is working and being refused, so tuning it is spending effort in the wrong
  place.
- Connects the growth to the write latency through pages read and cache occupied.
- Proposes bounding the transaction and says which mechanism and what it breaks for the report.

### lead

- Chooses between a server-side timeout, a change to the tool, and a separate copy, from who owns
  each and what each costs to keep true.
- Names the other things that can hold the same point back, so the fix is not written for one
  cause.
- Says what is watched from tomorrow, and why the signal is the age of a session rather than the
  size of a disk.
- Decides what happens to a report that is genuinely killed halfway through.

## Follow-ups

- The report is read-only and only ever looks at one schema. Does that limit the damage to that
  schema?
  probes: whether they see the reclaim point as one number for the cluster, not per table
- Someone proposes rewriting the two biggest tables overnight to claw the space back. Would you
  let them?
  probes: the exclusive lock and the rewrite cost, and that it does nothing about tomorrow
- The same symptom turns up on a Saturday with the report not running at all.
  probes: slots, feedback from a standby, a prepared transaction left behind
- You would rather find out at nine in the morning than at six in the evening. What do you put on
  a dashboard?
  probes: the age of the oldest open session as the leading signal, ahead of disk use

## Sources

- https://www.postgresql.org/docs/current/routine-vacuuming.html
- https://www.postgresql.org/docs/current/runtime-config-client.html
- https://www.postgresql.org/docs/current/sql-vacuum.html
- https://www.postgresql.org/docs/current/monitoring-stats.html
- https://www.postgresql.org/docs/current/mvcc-intro.html

## Notes

The documented sentence this card rests on, from `idle_in_transaction_session_timeout`: "Even when
no significant locks are held, an open transaction prevents vacuuming away recently-dead tuples
that may be visible only to this transaction; so remaining idle for a long time can contribute to
table bloat."

And on the manual's advice for long transactions: find them in `pg_stat_activity` by rows where
`age(backend_xid)` or `age(backend_xmin)` is large, and commit, roll back or terminate them.

Figures to release when asked:

- The cluster is PostgreSQL 16 on a managed instance; the report runs a few dozen statements over
  the day through a BI tool with autocommit off.
- Two tables take about 12,000 updates a minute between them. Neither is read by the report.
- The autovacuum log line for those tables reports a large number of rows "dead but not yet
  removable" and an `oldest xmin` that does not advance between 08:00 and 18:00. The exact wording
  of that line has changed across major versions; the number that matters is the one that does not
  move.

On the fixes, in the order they are usually right: turn on autocommit in the tool; set
`idle_in_transaction_session_timeout` on the reporting role so a stuck session is ended rather
than tolerated; on PostgreSQL 17 and later `transaction_timeout` bounds the whole transaction, not
just the idle part; point the report at a replica and accept that a replica configured to feed its
own horizon back re-creates the problem on the primary.

`VACUUM FULL` is the answer this card is fishing for as a mistake. It does reclaim the space —
the manual notes it "requires an ACCESS EXCLUSIVE lock on the table" and rewrites it — and the
report will refill it tomorrow.
