---
id: kafka-retries-blocking-loop-01
schema_version: 1
title: The consumer sleeps and tries again, forever
category: kafka
topic: retries
level: junior
tags: [retries, failure-modes, operations]
time_estimate_min: 7
order: 20
links:
  deeper: [kafka-retries-delay-topic-ordering-01]
---

## Ask

A consumer calls an HTTP service for every record it reads. That service goes down for an hour.
The consumer is written to catch the error, sleep a second, and try the same record again until it
works. What does that do to the topic and to the group while the service is down?

## Tests

Whether the candidate can follow a blocked handler outward to the partition behind it, the group
it belongs to, and the records that were never going to fail.

## Listen for

- Says the partition stops dead: everything behind that record waits, including records that would
  have gone through fine
- Connects an hour spent inside the handler to the member being treated as dead and its work being
  handed to somebody else
- Says the same record then blocks whoever picks that partition up next, so nothing improves
- Asks whether the error was worth trying again at all, since a malformed body will never succeed
- Suggests a limit on attempts, and somewhere for the record to go once they run out

## Expected knowledge

- A consumer has to come back for more records regularly or the group treats it as gone
- Records behind an unhandled one on the same partition are not skipped

## Strong signals

- Separates a failure that will pass on its own from one that never will, and handles them
  differently
- Points out that sleeping inside the handler holds up the whole batch, not just the one record
- Suggests widening the wait between attempts rather than a flat second forever

## Weak signals

- Says only that one record is delayed
- Adds a loop with no limit and no way out
- Cannot say what the group does about a member stuck inside a handler

## Answer bands

### weak

- Thinks the consumer moves on and comes back to the record later.
- Sees no effect beyond the single record.
- Calls the loop correct because nothing is lost.

### junior

- Says the partition stops behind the failing record and lag grows.
- Notes that a handler stuck for an hour will be treated as gone by the group.
- Suggests a limited number of attempts rather than an endless loop.

### mid

- Points out the same record blocks the next owner of that partition too.
- Splits errors into ones worth trying again and ones that never will succeed.
- Proposes widening the wait between attempts, and a place for a record that exhausts them.

## Follow-ups

- One record in that batch has a body the parser will never accept. How long should the consumer
  keep trying it?
  probes: whether a permanent failure is separated from a temporary one
- The pod is dropped from the group while it is asleep. Does another pod get any further?
  probes: that moving the work does not move the problem
- The HTTP service is up, but rejecting one call in ten at random. Does your answer change?
  probes: proportional handling, backing off rather than simply bounding attempts

## Sources

- https://kafka.apache.org/documentation/#consumerconfigs_max.poll.interval.ms
- https://kafka.apache.org/documentation/#intro_consumers
