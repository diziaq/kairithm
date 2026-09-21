---
id: kafka-offsets-rewind-choice-01
schema_version: 2
title: Choosing how to put six bad hours through again
category: kafka
topic: offsets
level: lead
tags: [operations, correctness, failure-modes, idempotency]
time_estimate_min: 12
order: 84
links:
  related: [spring-web-layer-long-running-request-01]
---

## Ask

A bad deploy yesterday wrote wrong aggregates into a shared reporting table for six hours. The
fix is merged, every record is still in the topic, and now you have to decide how those six hours
get put through again. Twelve partitions, four pods in one group, finance reads that table all
day, and two other services write into it. Which way do you go, and what does the choice cost you
afterwards?

## Tests

Whether the candidate can put two or three ways back side by side, choose one against the
constraints they were given, and name what each one costs while it runs and every time somebody
has to do it again.

## Ideal minimal answer

Two routes: stop the four pods and move the group's stored position, which nothing outside the
group can do while they hold the partitions, or start a second deployment under a name the
cluster has never seen, with no downtime but every record handed over again. Pick one against
what finance can tolerate, and say who watches the second pass and how it is signed off.

## Listen for

- Offers more than one way back: moving the group's stored position, or bringing up a second
  deployment under a name the cluster has never seen before
- Knows nothing outside the group can move its stored position while the four pods still hold the
  partitions, so that route means stopping them, and says what piles up while they are down
- Turns "six hours" into a starting point for each of the twelve partitions, and asks which clock
  the records carry before trusting a lookup by time
- Says the second deployment costs no downtime but hands every record to the handler a second
  time, so the writes have to land on the same rows rather than beside them
- Asks whether six hours ago is still inside what the topic keeps
- Separates what the cluster will do — hold the records, let the position be moved — from what
  the handler has to do for a second pass to end up correct
- Names what each route leaves behind: a group nobody is watching and alerts aimed at a name that
  no longer runs, or a stopped consumer and one more step somebody has to remember

## Expected knowledge

- A group's position is kept for each partition, and whoever picks the partition up next carries
  on from it
- Records stay in the topic until they age out, so going back is only possible inside that window

## Strong signals

- Asks whether the wrong rows can be found and written over before arguing about how to move the
  position
- Plans how anyone will know the second pass finished, and what happens if it comes out wrong
  again
- Points out that whatever the consumer publishes onward gets published onward again, so other
  teams are inside the blast radius
- Asks finance what a few hours of numbers moving under them is worth, and schedules around the
  answer

## Weak signals

- Assumes the stored position can be rewritten from outside while the pods are running
- Reaches for deleting or recreating the topic
- Treats a second pass as free because the records are still there
- Cannot say what the table looks like halfway through

## Answer bands

### mid

- Names one way back and can carry it out from start to finish.
- Says the same records reach the handler a second time, and asks what that does to the table.

### senior

- Says the group has to be stopped before anything outside it can move its position, and what
  builds up meanwhile.
- Turns the six hours into a starting point per partition and says where that number comes from.
- Separates what the cluster does from what the handler has to do for the second pass to land on
  the same rows.

### lead

- Puts two or three routes beside each other and picks one against the constraints on the table,
  saying who is inconvenienced by each.
- Names what each route leaves behind to look after: an unwatched group, a flag in the code, one
  more entry in a runbook.
- Decides how the second pass is shown to be finished and correct, and who is watching while it
  runs.
- Says what they would change so the next bad deploy is cheaper to undo.

## Follow-ups

- The quickest route needs those four pods down for twenty minutes, and the topic keeps taking a
  thousand new events a second the whole time. Describe the first ten minutes after they come
  back up.
  probes: the backlog built while the group was stopped, the rate it comes back at, and whether
  the table and the services around it can absorb that
- Someone suggests leaving the live consumer alone and starting a second copy of the service
  under a name of its own to work through yesterday. What do you want to know about the table
  before you agree?
  probes: whether a repeat pass lands on the same rows, and what finance sees while both copies
  are writing
- Finance opens their dashboard while that second pass is halfway through. What are they looking
  at?
  probes: half-rewritten aggregates, and whether anyone thought to tell them
- Three months from now the same thing happens to a different team's consumer. What do you want
  to already be true by then?
  probes: whether they leave a repeatable procedure behind rather than a one-off rescue

## Sources

- https://kafka.apache.org/documentation/#basic_ops_consumer_group
- https://cwiki.apache.org/confluence/display/KAFKA/KIP-122%3A+Add+Reset+Consumer+Group+Offsets+tooling
- https://kafka.apache.org/documentation/#consumerconfigs_auto.offset.reset

## Notes

Two claims worth being exact about. The reset tooling and the admin API move a group's committed
offsets only while that group has no active members, so rewinding in place always implies
stopping the consumer first (KIP-122). And a reset to a point in time resolves to the first offset
whose record timestamp is at or after it, which depends on whether the topic stamps records when
they are created or when they are appended — so the six-hour boundary is an approximation unless
the candidate checks that.
