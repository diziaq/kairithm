---
id: microservices-scalability-throughput-falls-with-more-workers-01
schema_version: 2
title: Forty workers finish less work than eight did
category: microservices
topic: scalability
level: lead
tags: [performance, capacity, operations, failure-modes]
time_estimate_min: 10
order: 620
links:
  shallower: [microservices-scalability-autoscaled-into-database-01]
  related: [java-performance-parallel-stream-sweep-01]
---

## Ask

A batch job runs on eight workers and clears forty thousand records a minute. To hit a date the
team took it to forty workers, and the total dropped to twenty-six thousand a minute. Same code,
same database, same records. Where do you look, and what would you have them measure?

## Tests

Whether the candidate can tell a shared bottleneck apart from a cost that grows with every worker
added, and will measure the shape of the curve instead of arguing about the number.

## Ideal minimal answer

Falling rather than flattening means the workers are paying a cost that grows as they are added —
waiting on the same rows, rolling back and redoing finished work, invalidating each other. I would
run it at two, four, eight and sixteen, plot what comes out, and take the peak, and measure where
a worker's time actually goes rather than guessing which of those it is.

## Listen for

- Distinguishes the two shapes and says what each means: work that stops rising has hit something
  shared, work that falls is being spent on the workers dealing with each other
- Refuses to guess at forty: runs it at two, four, eight, sixteen and thirty-two and looks at the
  curve, because the peak is a measurement and not an opinion
- Wants a worker's time broken down — running, waiting on a row, waiting for a connection, redoing
  something it already did — before proposing a change
- Names candidate mechanisms that get worse with each worker: contention on the same rows, lock
  waits that grow with the number of waiters, rollbacks that discard completed work, cross-node
  invalidation, one claim table every worker polls
- Notices that a rollback is worse than a wait: the time is not just lost, the work is undone
- Asks how work is handed out, and whether two workers can ever be given records that touch the
  same rows
- Proposes removing the coupling rather than tuning the count — partition the input so no two
  workers meet — and says what that costs to build
- Says what to do about the date: the honest answer may be that this job has a ceiling and the
  work has to be split differently or start earlier

## Expected knowledge

- More workers raises the offered load, not the amount of work the shared parts can absorb
- Two writers that update the same rows serialise, and one of them may be rolled back and rerun
- Throughput and the time each unit takes are different measurements and can move in opposite
  directions

## Strong signals

- Asks for the figure at sixteen before saying anything about forty
- Points out that the eight-worker figure is also not necessarily the peak, and wants the curve
  either side of it
- Separates the arithmetic that has to be serial from the arithmetic that could be partitioned,
  and says which part of this job is which
- Has a view on what the team should do with the result: the number of workers they run on Monday
  and what they tell whoever asked for forty

## Weak signals

- Adds more workers, or bigger workers, on the grounds that forty was not enough
- Blames the network without measuring anything
- Raises the batch size and calls it tuning
- Concludes the database needs a larger instance from the shape of the curve alone
- Recounts a past job that behaved like this and never says what to do about this one
- Lists the possible causes accurately and will not say how to tell them apart

## Answer bands

### mid

- Says the workers are getting in each other's way and points at the shared database.
- Suggests reducing the worker count, and can pick a figure once asked how they would choose it.
- Treats a plateau and a decline as the same thing.

### senior

- Separates the two shapes unprompted and says what a decline implies that a plateau does not.
- Asks for the curve at several worker counts rather than reasoning from two points.
- Names a mechanism whose cost grows with each worker and says which measurement would confirm it.
- Asks how records are handed out and whether two workers can touch the same rows.

### lead

- Picks the number to run from the measured peak and says what happens to the date, to whoever
  asked for forty.
- Decides between living with the ceiling and repartitioning the work so workers never meet, and
  prices the second one.
- Says what a job should be required to show before anyone is allowed to scale it out again.
- Names what should be recorded per run so nobody has to rediscover this next quarter.

## Follow-ups

- At sixteen it clears fifty-two thousand a minute. What do you run on Monday, and what do you say
  to the team that asked for forty?
  probes: choosing from the measured peak, and handling the expectation that came with the date
- Every worker takes its next records from one shared table before it starts. What is that doing
  at forty?
  probes: one shared claim point; waiting that grows with the number of waiters
- Same forty workers, but each one owns a set of customers nobody else touches. What do you expect?
  probes: whether they remove the coupling rather than tune the count
- Suppose it had gone flat at eight instead of falling. Same problem?
  probes: a plateau points at something shared and finite; a decline points at a per-worker cost

## Sources

- https://arxiv.org/abs/0808.1431
- https://www.postgresql.org/docs/current/monitoring-stats.html#WAIT-EVENT-TABLE
- https://sre.google/sre-book/addressing-cascading-failures/

## Notes

The two shapes are the whole card. Work that flattens has hit something shared and finite; work
that falls is being spent on coordination between the workers themselves, and the second is the
only one that explains twenty-six thousand from forty workers. Gunther's model has a term for
each, but the candidate does not need the name — only the distinction and the measurement that
tells them apart.

Figures to release when asked: eight workers give forty thousand a minute, sixteen give
fifty-two, thirty-two give thirty-four, forty give twenty-six; the job updates a shared summary
row per customer and deadlock rollbacks are a hundred times higher at forty than at eight.
