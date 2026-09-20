---
id: database-query-performance-what-the-team-maintains-01
schema_version: 1
title: Eleven rescues in a year, and you own the next one
category: database
topic: query-performance
level: lead
tags: [performance, operations, observability]
time_estimate_min: 14
order: 202
links:
  related: [database-consistency-quorum-dashboard-disagrees-01, java-gc-pause-budget-01]
---

## Ask

You take over a service where, every few weeks, a page gets slow, somebody spends two days on the
query that week, ships a fix, and closes the ticket. It has happened eleven times this year. Your
team owns this for the next year. What do you put in place, and what do you deliberately not do?

## Tests

Whether the candidate treats speed as a capability with a signal, a budget and an owner, rather
than a series of rescues — and can name what they will refuse to take on.

## Listen for

- Asks which pages actually matter and what is promised for each, as a number per endpoint rather
  than "fast"
- Wants the shape of the load first: which handful of queries account for most of the total time
  spent, and how flat the rest of the curve is
- Separates the query that is slow once from the one that is quick and runs constantly, and knows
  the second often costs more in total

- Says the recurring failure is not being detected, only reported by users, and makes detection
  the first thing they build
- Names what the team will keep running afterwards, and is honest that each such thing has an
  owner, a cost and a way of rotting
- States what they will stop doing: chasing the long tail, hand-tuning a report nobody opens,
  keeping overrides that nobody can justify
- Ties the effort to money or to risk, so the checkout page and the quarterly export do not get
  the same week

## Expected knowledge

- Total time for a query is how often it is called multiplied by the time each call takes, and
  the ranking by total rarely matches the ranking by worst single run
- A database keeps running per-query figures that can be sampled and compared over time
- A hint or an override written into a query outlives the condition it was written for, and the
  person who wrote it

## Strong signals

- Asks to read the last eleven fixes before designing anything, and looks for what they have in
  common
- Requires a before and after figure on every change made for speed, so a later reader can tell
  what actually moved
- Talks about the work the team will not have room for, and says what happens to it
- Notices that some of the eleven were never query problems: a page asking for ten times the data
  it renders, a report that should not be computed live, a job scheduled at the worst hour

## Weak signals

- Answers with a list of tuning techniques
- Proposes a dashboard without saying what decision it supports or who looks at it
- Commits the team to reviewing every query before every release, with no estimate of the cost
- Treats faster as always better, with no target to stop at

## Answer bands

### mid

- Suggests measuring before changing, and says where the figures would come from.
- Points at the repeat rate as the problem, rather than at the eleven queries one by one.

### senior

- Ranks the work by total time spent and by which page a user is waiting on, not by the worst
  single run.
- Makes the signal arrive before the complaint does, and says who receives it and what they do.
- Attaches a before and after figure to each change so the next person can tell what moved.
- Names the few queries worth real effort and says the tail is being left alone on purpose.

### lead

- States the running cost of every mechanism they propose and who carries it after they move on.
- Says out loud what the team will not do, and where that work goes instead.
- Ties the budget to a business figure and names the point at which the answer becomes fewer
  features rather than a faster query.
- Plans for whoever inherits an override: how it is recorded, what triggers a review, when it goes.

## Follow-ups

- Six months in, the graph is flat and nobody has been paged. Your manager asks what the two
  engineers were for.
  probes: whether they can show the value of prevention, and whether they planned for that day
- One of the eleven fixes was a note in the query telling the database what to do. The author has
  left the company. What now?
  probes: the long-term cost of an override nobody can justify, and how they retire one safely
- The busiest statement in the service takes nine milliseconds and runs forty thousand times a
  minute. Where does it sit on your list?
  probes: total time against worst case, and whether they rank by the right number
- A product manager wants the whole quarter for a new feature. What do you give up?
  probes: a forced trade, and whether the thing they designed survives contact with the roadmap

## Sources

- https://www.postgresql.org/docs/current/pgstatstatements.html
- https://dev.mysql.com/doc/refman/8.0/en/performance-schema-statement-summary-tables.html
- https://learn.microsoft.com/en-us/sql/relational-databases/performance/monitoring-performance-by-using-the-query-store

## Notes

This card is about where effort goes and what the team signs up to keep running. If the candidate
starts designing an index or rewriting a query, let them finish the thought and then ask the
manager follow-up — the interesting answer is the one about the twelfth time, not the eleventh.

Figures to release when asked:

- Eight of the eleven were on three pages; the other three were one-off reports.
- Nothing records per-statement timings today; the only signal is a support ticket.
- The team is four engineers and already carries an on-call rota.
- Checkout is 60% of revenue and its p95 is 1.9 seconds against a 1-second target.

The per-statement figures exist on every mainstream engine but under different names:
`pg_stat_statements` (an extension that has to be enabled) in PostgreSQL, the
`events_statements_summary_by_digest` table in the MySQL performance schema, Query Store in SQL
Server. Credit a candidate who knows theirs has to be turned on and has a cost.
