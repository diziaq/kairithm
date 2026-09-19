---
id: kafka-rebalancing-rolling-deploy-01
schema_version: 1
title: A rolling deploy costs the group four minutes
category: kafka
topic: rebalancing
level: mid
tags: [operations, performance, failure-modes]
time_estimate_min: 8
order: 44
links:
  deeper: [kafka-rebalancing-stateful-restore-01]
  related: [kafka-consumer-groups-flapping-member-01]
---

## Ask

A twelve-pod consumer group is deployed one pod at a time. Each pod on its own restarts in fifteen
seconds, but for about four minutes during every deploy almost nothing is consumed and lag spikes.
Why does a rolling deploy cost the group four minutes?

## Tests

Whether the candidate knows what happens to the other members when one of them leaves, and can
account for the total cost of a rolling restart.

## Listen for

- Says every member stops reading while the work is divided up again, not only the pod that
  restarted
- Counts it out: twelve restarts, two group-wide pauses each, plus however long the group waits
  before deciding a missing member is gone
- Says a member that shuts down cleanly announces itself, while one that is killed is only noticed
  after a timeout
- Knows the cooperative protocol only takes away the partitions that actually move, so the rest
  keep reading throughout
- Asks whether the pods get enough shutdown grace to leave cleanly

## Expected knowledge

- The classic protocol takes every partition away from every member before handing them out again
- A member that is killed is not missed until its session times out

## Strong signals

- Points out each pod restart is two events, a departure and an arrival, so the group pauses twice
  per pod
- Asks which client version and which assignor are in use before assuming the behaviour
- Separates the pause itself from whether anyone actually cares about a four-minute delay

## Weak signals

- Thinks only the pod being replaced stops reading
- Blames the broker
- Cannot say what the other eleven pods are doing during the pause

## Answer bands

### weak

- Assumes only the pod being replaced stops reading.
- Has no account of why the pause outlasts the restart.
- Suggests deploying faster without saying what that changes.

### mid

- Says the whole group stops while ownership is worked out, not only the restarting pod.
- Multiplies the pause by the number of pods and shows where four minutes comes from.
- Knows a pod that is killed outright is not missed straight away.

### senior

- Counts two pauses per pod and says what triggers each one.
- Contrasts taking everything away with taking away only what moves, and says what the second
  buys here.
- Asks about shutdown grace, and whether the departure is announced rather than timed out.

## Follow-ups

- If the pods were killed outright with no grace period, would it get better or worse?
  probes: whether the group has to wait for a member to be declared missing
- What could you change so that the nine pods which keep their own work never stop reading?
  probes: the cooperative protocol, without handing over the name
- The deploy still takes four minutes but the team says lag recovers within seconds. Does that
  change your answer?
  probes: whether a pause matters in itself or only through its effect

## Sources

- https://cwiki.apache.org/confluence/display/KAFKA/KIP-429%3A+Kafka+Consumer+Incremental+Rebalance+Protocol
- https://cwiki.apache.org/confluence/display/KAFKA/KIP-848%3A+The+Next+Generation+of+the+Consumer+Rebalance+Protocol

## Notes

Which behaviour a team actually gets depends on the client version and the assignor configured;
the classic stop-the-world behaviour is what most long-lived deployments still see, and newer
Kafka versions ship a different protocol again. A candidate who answers in terms of the newer
protocol and says so is answering well, not wrongly — the point is whether they know one member
leaving affects all of them.
