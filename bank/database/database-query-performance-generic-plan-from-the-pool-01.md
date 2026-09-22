---
id: database-query-performance-generic-plan-from-the-pool-01
schema_version: 2
title: Fast by hand, slow from the service, and only after an hour
category: database
topic: query-performance
level: senior
tags: [performance, failure-modes, observability, operations]
time_estimate_min: 11
order: 650
links:
  related: [database-query-performance-plan-flipped-overnight-01]
---

## Ask

One statement is quick for almost every tenant and a hundred times slower for one. Run by hand
against the same PostgreSQL database with that tenant's id, it is always quick. It only goes wrong
from the service, and only once an instance has been up for a while. The team wants to add an
index. What is happening?

## Tests

Whether the candidate can explain a difference between the same statement issued two ways, locate
the state that accumulates inside a long-lived connection, and pick a fix that does not involve
changing the query.

## Ideal minimal answer

The statement ends up run from a plan built without the tenant id. The driver promotes it to a
named statement on the server after a few runs; the server then builds one plan with no value,
compares its estimated cost against the average of the earlier ones, and keeps it. For the one
big tenant that plan is wrong, and running it by hand never gets there.

## Listen for

- Separates three ways the same text reaches the server — typed in a session, sent with values
  inline, sent as a named statement the server holds — and says only the third accumulates state
- Says the driver switches to the third form after a handful of executions on the same connection,
  which is why uptime matters and a fresh process does not show it
- Says the server then decides once whether to keep re-planning per value or settle on a plan
  built without one, and that the decision is made on estimated cost
- Explains the failure precisely: the settled plan looks reasonable on an average tenant's row
  count, and that is the number the comparison used, so the outlier is never considered
- Ties it to skew: one tenant holds a share of the table nothing like the median, so the shape
  that works for everyone else is wrong for them
- Notes that running it by hand is a different execution path, so "I cannot reproduce it" carries
  no information here
- Says adding an index may or may not help and cannot be decided until the plan from the slow
  path has been captured

## Expected knowledge

- A statement held by the server can be planned once and reused, or planned per call with the
  values known
- A pooled connection is long-lived, so per-connection state survives many requests and many
  tenants

## Strong signals

- Asks for the distribution of rows per tenant before anything else
- Says a fix exists on each of three layers — the driver's threshold, a server setting, the
  statement itself — and picks one with a reason
- Wants the plan captured automatically when the statement crosses a threshold, with the values
  recorded alongside it
- Points out that reverting the pool's statement caching would hide it and cost the planning it
  was buying, and prices that
- Says what the one big tenant costs everyone else if the fix is to plan every call afresh

## Weak signals

- Adds an index without having seen the slow plan
- Says the database picks a plan at random, or that it degrades over time
- Blames the pool, the network, or the tenant's data volume alone
- Concludes it is not reproducible and closes it
- Names three layers where it could be fixed and refuses to choose

## Answer bands

### mid

- Notices that by hand and from the service are different paths, and asks what the driver does.
- Connects the slow tenant to that tenant having far more rows than the rest.
- Suggests restarting or reconnecting as a workaround, without saying what it discards.

### senior

- Names the mechanism unprompted: the statement becomes one the server holds, and is eventually
  run from a plan built without the value.
- Explains why an hour of uptime is the trigger and a fresh process is not.
- Says the choice was made on an estimate taken over the average, which is why the outlier slips
  through.
- Asks for the slow plan and says how to capture it automatically next time.

### lead

- Picks between the driver setting, the server setting and a change to the statement, from who
  owns each and what it costs the other tenants.
- Decides what the service does for that one tenant while the proper fix is built.
- Says how the team would find the other statements already in this state before a customer does.
- Puts a limit on how skewed a tenant may get before the design, not the plan, is the problem.

## Follow-ups

- Bouncing the service makes it quick again for about an hour. What does that tell you, and what
  does it not?
  probes: that discarding connection state confirms state was held, and identifies nothing
- You cannot ship application changes this week, but you can change the database. What do you
  reach for?
  probes: a setting on the role or the database that forces the per-call choice
- A colleague says another engine they used decided the shape from the very first call it ever
  saw, and never revisited it. Is that the same thing?
  probes: whether they keep the engines apart rather than carrying one story across
- Nobody kept anything from a slow run. What do you switch on today?
  probes: automatic capture with the values attached, as the deliverable of this incident

## Sources

- https://www.postgresql.org/docs/current/sql-prepare.html
- https://www.postgresql.org/docs/current/runtime-config-query.html
- https://jdbc.postgresql.org/documentation/use/
- https://www.postgresql.org/docs/current/auto-explain.html
- https://www.postgresql.org/docs/current/planner-stats.html

## Notes

Two thresholds, both defaulting to five, and candidates who know one rarely know the other:

- pgjdbc's `prepareThreshold` is documented as "the number of PreparedStatement executions
  required before switching over to use server side prepared statements", default 5, with
  `preparedStatementCacheQueries` at 256 keeping them alive across close and reopen of the
  `PreparedStatement` object.
- PostgreSQL's own rule, from the `PREPARE` manual: with `plan_cache_mode` at `auto`, "the first
  five executions are done with custom plans and the average estimated cost of those plans is
  calculated. Then a generic plan is created and its estimated cost is compared to the average
  custom-plan cost. Subsequent executions use the generic plan if its cost is not so much higher
  than the average custom-plan cost as to make repeated replanning seem preferable."

Get the second one right. It is *not* "PostgreSQL switches to a generic plan after five
executions". It compares estimated costs and may keep re-planning forever. The failure here is
that the comparison is between two *estimates*, and the generic estimate is computed over the
average selectivity — which is fine, and is why the plan is kept, and is exactly why it is wrong
for the tenant nobody averaged.

Figures to release when asked, and credit the asking:

- 1,400 tenants; the median holds about 900 rows, one holds 31 million.
- A freshly deployed instance is quick for about an hour and then is not. The pool is HikariCP
  with a 30-minute maximum connection lifetime, which is the right order of magnitude for that.
- `plan_cache_mode` is at its default.

Where this sits against the overnight-flip card: that one is a whole-statement mystery with two
live hypotheses — a stale sample or a reused plan — and the deliverable is capture. This one has
the values and the timing already in the symptom, and the work is naming the mechanism precisely
and choosing a layer to fix it on. If the candidate has already done that card, the tell is
whether they reach past "cached plan" to the two thresholds and the cost comparison.

The fixes, roughly in order of how often they are right: set `plan_cache_mode` to
`force_custom_plan` for the role that runs it and measure the planning cost you just took on;
set the driver's threshold to zero for that statement; make the tenant id part of the statement
text where the number of distinct shapes is small; and, last, shard or partition the outlier.
