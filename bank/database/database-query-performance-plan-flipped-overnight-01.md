---
id: database-query-performance-plan-flipped-overnight-01
schema_version: 1
title: Fast for a year, 90 seconds on Tuesday, fine on Wednesday
category: database
topic: query-performance
level: senior
tags: [performance, failure-modes, observability, operations]
time_estimate_min: 12
order: 201
links:
  related: [spring-troubleshooting-slow-in-production-01]
  deeper: [database-query-performance-what-the-team-maintains-01]
---

## Ask

A search query has run in 200 milliseconds for a year. On Tuesday morning it started taking 90
seconds — no deploy, no schema change, no unusual traffic. By Wednesday it was quick again and
nobody had touched anything. Ops want a standing instruction to restart the database when it
happens. What do you do instead?

## Tests

Whether the candidate can explain how one unchanged statement gets served two different ways on
two days, and turn a recurring mystery into something that arrives with evidence attached.

## Listen for

- First asks whether the plan was the same on both days, and whether anybody captured it while it
  was slow
- Says the figures the optimiser relies on are a sample taken at some past moment, and that a bulk
  load or a large delete can leave them describing a table that no longer exists
- Knows a plan built for one set of values can be reused for a later call with very different
  ones, so the first call seen decides the shape for everyone after it
- Asks which values were being searched for during the slow window, because an uneven column makes
  one value match a thousand rows and another match four million
- Wants automatic capture — log the plan whenever the statement crosses a threshold — so the next
  occurrence is evidence rather than a story
- Treats "restart and it goes away" as a hint that something was being held, not as a fix

## Expected knowledge

- In PostgreSQL the autovacuum daemon also refreshes the sample, on a threshold tied to how many
  rows have changed, so a bulk change can outpace it
- In SQL Server a compiled plan is cached and reused for later calls with different values; the
  value present when it was compiled shapes what everyone else gets
- PostgreSQL re-plans a prepared statement for its own values up to five times, then may switch to
  one built without them; `plan_cache_mode` controls this
- MySQL 8.0 removed the query cache, and what it removed was a result cache, not a plan cache — do
  not let a candidate carry the SQL Server story across to MySQL unexamined

## Strong signals

- Refuses to theorise until they have the plan from the slow window, and says how to get it next
  time
- Separates "the estimate was wrong" from "the estimate was right and that value really is
  expensive"
- Proposes forcing a fresh sample as a diagnosis step and says how they would know it worked
- Points out that a restart discards several things at once — plans, cache, connections — so it
  confirms nothing
- Lists what to record now so the next occurrence takes ten minutes: statement, values, plan, row
  counts, timings

## Weak signals

- Blames load or the network with no evidence
- Proposes a new index without knowing which plan ran
- Accepts the restart because it worked
- Says the database picks a plan at random

## Answer bands

### mid

- Asks whether the same plan ran on the fast day and the slow day.
- Names something that changes with no deploy: the volume of data, the values being searched for,
  the sample the database holds.

### senior

- Explains how one statement can be served two different ways on two days, naming a mechanism
  rather than calling it random.
- Asks for the values used during the slow window and connects them to an uneven spread of data.
- Says the restart worked because it discarded something, and identifies what.
- Sets up capture so the next occurrence arrives with a plan attached.

### lead

- Decides what the team does while the cause is still unknown, and what the page falls back to.
- Chooses between refreshing the sample on a schedule, pinning the shape of the plan, and
  rewriting the query, with the upkeep each one carries.
- Puts a number on how often this may happen before it stops being an incident and becomes a
  project with an owner.

## Follow-ups

- Overnight a job deletes eleven million rows from that table. Does that change your answer?
  probes: whether they connect a bulk change to the sample the optimiser relies on
- The slow runs were all for one customer with four million rows; the fast ones were for customers
  with a dozen. What is going on?
  probes: skew, and one cached shape reused across values with wildly different result sizes
- Ops restart it again and it stays quick for three weeks. What have you learnt?
  probes: that clearing state confirms state was held, and says nothing about the cause
- You cannot reproduce it on demand. What do you switch on today?
  probes: automatic capture and slow-statement logging as the deliverable of this incident

## Sources

- https://www.postgresql.org/docs/current/sql-prepare.html
- https://www.postgresql.org/docs/current/runtime-config-query.html
- https://www.postgresql.org/docs/current/routine-vacuuming.html
- https://www.postgresql.org/docs/current/auto-explain.html
- https://learn.microsoft.com/en-us/sql/relational-databases/performance/parameter-sensitivity-plan-optimization
- https://dev.mysql.com/doc/refman/8.0/en/mysql-nutshell.html

## Notes

Figures to release when asked, and credit the asking:

- The table grew from 4 million to 60 million rows over the year; a monthly archive job ran on
  Monday night and removed 11 million.
- The statement is a prepared statement issued by the connection pool, with the customer id as a
  value.
- One customer holds about 4 million of the rows; the median customer holds fourteen.
- Nobody kept a plan from Tuesday. That is the real finding.

Engine pins, because candidates blur these:

- The reuse-a-plan-compiled-for-someone-else's-value story is SQL Server's by default. PostgreSQL
  only reaches a generic plan for a *prepared* statement, and only after five executions, and
  `plan_cache_mode` can force either way.
- Refreshing the sample is `ANALYZE` in PostgreSQL, and autovacuum does it on a row-change
  threshold. A single large delete or load can move far more rows than the threshold expects
  before the daemon next looks.
- MySQL 8.0 has no SQL Server-style shared plan cache to blame; on that engine steer the candidate
  towards the table sample and the values instead.

Both causes — a stale sample and a plan reused across unlike values — produce exactly this
symptom, and a good candidate says they cannot choose between them without the captured plan.
