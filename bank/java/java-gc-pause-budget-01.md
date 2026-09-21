---
id: java-gc-pause-budget-01
schema_version: 2
title: A blog post's flags against a latency budget
category: java
topic: garbage-collection
level: lead
tags: [performance, operations, observability, memory]
time_estimate_min: 10
order: 410
links:
  related: [java-performance-local-cache-proposal-01]
---

## Ask

A latency-sensitive service sits inside its 200ms budget on average but shows 1.5-second spikes a
few times an hour, and the collector log lines up with them. The team's plan is to switch collectors
and add half a dozen flags they found in a blog post. What do you want to see before that goes
anywhere near production?

## Tests

Whether the candidate treats collector behaviour as something measured against a stated budget and
changed with a way back, rather than as a set of flags to copy.

## Ideal minimal answer

Wants the budget stated, the collector log read and a way back in place before any flag is
changed, and one change at a time against a production-shaped load test. Asks who is actually
harmed by the spikes, and says what would make them reject the proposal outright and go after
the code that allocates instead.

## Listen for

- Wants the log read first: how long the pauses are, what triggered each cycle, how much survives,
  and whether the live set is creeping up across days
- Separates a growing live set from a high rate of allocation; the treatment is not the same
- Knows that long pauses with a steady live set usually point at what the code allocates, and that
  producing less rubbish beats configuring its removal
- Names the trade the low-pause collectors make — pauses stop tracking the size of the heap, paid
  for in throughput and in footprint — and asks whether this service can afford it
- Asks about the container's memory limit against the heap plus everything outside it, and what the
  platform does when the process exceeds it
- Requires one change at a time, a load test shaped like production, and a documented way back

## Expected knowledge

- Generational collection: most objects die young, and an object that survives costs more
- A pause figure quoted anywhere says nothing without the heap size, the live set and the allocation
  rate that produced it

## Strong signals

- Asks whether the collector is the cause or a victim — a page fault, swap, or a CPU quota being
  throttled will show up in the same log
- Wants the budget stated per endpoint, and asks who is actually harmed by 1.5 seconds
- Raises the operational cost: who will understand this configuration in six months, and how a
  regression would be noticed

## Weak signals

- Recites collector names and their marketing
- Sets a very large heap so collections happen less often, without discussing what each one then
  costs
- Applies the whole list of flags at once and declares victory from one afternoon of graphs

## Answer bands

### mid

- Asks to see the log and the heap configuration before changing anything.
- Knows young collections and old collections cost differently and looks at which is spiking.
- Suggests one change at a time.

### senior

- Distinguishes retention growth from allocation pressure and says which evidence tells them apart.
- Explains what the newer collectors buy and what they charge for it.
- Looks for the code path that produces the spike rather than tuning around it.
- Checks the heap against the container limit and what happens at the boundary.

### lead

- Puts the budget, the measurement and the rollback plan in place before touching the flags.
- Asks whether the spikes matter to anyone, and lets that size the work.
- Weighs who maintains the configuration afterwards against the improvement it buys.
- Says what would make them reject the whole proposal and fix the allocating code instead.

## Follow-ups

- The log shows the spikes only happen while one particular report runs. What now?
  probes: one code path's allocation shape; large objects; fixing the code not the collector
- The platform caps memory and it cannot be raised. Which of your options survive?
  probes: reasoning under a fixed constraint; the footprint cost of the low-pause options
- Suppose the change goes in and the spikes stop. What would still worry you?
  probes: throughput regression, cost per request, and growth that is now hidden rather than gone

## Notes

Both a leak and a high allocation rate can show as long pauses; the distinguishing evidence is
whether the live set after a full cycle trends upwards over days. Ask for that number specifically.

## Sources

- https://docs.oracle.com/en/java/javase/21/gctuning/
