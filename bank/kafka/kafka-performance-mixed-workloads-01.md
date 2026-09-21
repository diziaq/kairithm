---
id: kafka-performance-mixed-workloads-01
schema_version: 2
title: Trade alerts and the nightly load on one cluster
category: kafka
topic: performance
level: lead
tags: [performance, operations, api-design]
time_estimate_min: 12
order: 90
links:
  related: [microservices-scalability-one-tenant-dominates-01]
---

## Ask

You inherit a platform where one Kafka cluster carries both a trade alert flow with a fifty
millisecond budget and an overnight load of two billion rows. Both go through the same topics and
the same shared producer library with its defaults. The alert budget is missed every night at
eleven. What do you do about it?

## Tests

Whether the candidate can recognise two workloads with opposing goals on shared infrastructure,
and choose what to separate, what to cap and what to measure first.

## Ideal minimal answer

The two loads want opposite things: one wants records held back until a batch fills, the other
wants them on the wire at once. Give each its own topics and producer settings, cap the nightly
load, and state the condition under which it gets its own resources. Put the alert budget in
writing with an owner, and measure where the fifty milliseconds goes before changing anything.

## Listen for

- Says the two loads want opposite things: one wants records held back until a batch fills, the
  other wants them on the wire immediately
- Proposes separating them — their own topics, their own producer settings, ideally their own
  resources — rather than finding one number that suits both
- Asks how the fifty milliseconds is spent across the writer, the network, the broker and the
  reader, before touching anything
- Mentions the nightly load competing for the same disks and the same page cache the alert flow
  relies on
- Knows client quotas exist to stop one workload starving another

## Expected knowledge

- A producer accumulates records per partition before sending, trading latency for size
- Brokers serve a reader that is close to the end of a partition from the page cache

## Strong signals

- Asks for the ninety-ninth percentile rather than the mean, and where exactly the budget is
  measured from
- Points out that putting both on one cluster was a decision somebody made and can be revisited
- Prices a second cluster against the cost of missing the budget

## Weak signals

- Changes one setting in the shared library and declares it solved
- Treats the fifty milliseconds as a single number with no breakdown
- Never considers that the two loads compete for the same hardware

## Answer bands

### mid

- Says the two loads want different things and should not share one set of settings.
- Suggests splitting the topics so each can be configured for its own goal.

### senior

- Breaks the budget into the stages it is spent in, and says which they would measure first.
- Explains why holding records back to fill a batch helps one load and hurts the other.
- Notices the nightly load competes for broker resources the alert flow depends on.

### lead

- Chooses between separating the topics, capping the nightly load and separating the hardware,
  with a stated condition for each.
- Says what the alert flow's promise is in writing, and who is accountable when it is missed.
- Sets out what would be measured to prove the change worked, before making it.

## Follow-ups

- The team's first move is to change one setting in the shared library. What is likely to happen
  to the nightly job?
  probes: that the two goals are opposed, and one dial cannot serve both
- You measure, and forty of the fifty milliseconds are spent after the record has left the
  cluster. Now what?
  probes: whether they follow the evidence rather than the first suspect
- The business insists both workloads stay on one cluster. What is your plan?
  probes: capping one client, and whether they can state the risk that remains

## Sources

- https://kafka.apache.org/documentation/#design_quotas
- https://kafka.apache.org/documentation/#producerconfigs_linger.ms
- https://kafka.apache.org/documentation/#maximizingefficiency
