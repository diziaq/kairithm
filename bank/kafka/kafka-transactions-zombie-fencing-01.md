---
id: kafka-transactions-zombie-fencing-01
schema_version: 1
title: Two instances think they own the same input partitions
category: kafka
topic: transactions
level: lead
tags: [transactions, idempotency, correctness, operations]
time_estimate_min: 12
order: 88
---

## Ask

A transactional producer instance freezes on a long garbage collection pause, the orchestrator
declares it dead and starts a replacement, and then the original wakes up and carries on writing.
Both are now producing for the same input partitions. What stops the duplicates, and what do you
have to get right for that to actually work?

## Tests

Whether the candidate understands how a producer is identified across restarts, what displaces an
older one, and the operational constraints that identity scheme imposes.

## Listen for

- Says the transactional id is what makes the two processes one logical producer, and the newer
  one raises an epoch that locks the older one out
- Knows the locked-out instance has its writes rejected and fails, rather than corrupting the
  output
- Points out the id must be stable and derived from the work being handled, not generated per
  process, or nothing is ever locked out
- Says an id made up fresh at every start gives two live writers and no defence at all
- Asks how the id is chosen when the work moves to a different instance

## Expected knowledge

- A producer with such an id finishes or rolls back its predecessor's transaction when it starts
- Only the most recent holder of an id is permitted to write

## Strong signals

- Notices that an id tied to the process breaks as soon as the work is handed to a different
  instance
- Says what the frozen instance experiences, and that it must be allowed to die rather than keep
  trying
- Asks how many such identities exist across the estate and what that costs the brokers

## Weak signals

- Says transactions make it safe, with no account of what identifies a producer
- Builds the id from the hostname or a random value and sees no problem
- Believes the orchestrator's decision is enough to stop the old process writing

## Answer bands

### mid

- Says both instances would otherwise write, and something has to lock one of them out.
- Knows the producer carries a name that outlives a single process.

### senior

- Names raising the epoch as the mechanism, and says what the older instance gets back when it
  writes.
- States that the name has to come from the work, not from the process.
- Describes what the locked-out process should do instead of trying again.

### lead

- Sets a rule for how the name is derived across the estate, and says what it costs when work
  moves between instances.
- Says how the team would discover this was misconfigured before an incident rather than after.
- Decides which pipelines justify the machinery at all.

## Follow-ups

- The name is generated fresh at every start-up from a random value. Does anything still stop the
  older process writing?
  probes: whether they see that a new name is simply a second producer, not a replacement
- The work an instance handles moves to a different instance after a restart. Does the naming
  scheme survive that?
  probes: the identity has to follow the input partitions, not the process
- How would you find out today whether any of your twenty pipelines has this wrong?
  probes: auditing and observability rather than trusting the original design

## Sources

- https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging
- https://cwiki.apache.org/confluence/display/KAFKA/KIP-447%3A+Producer+scalability+for+exactly+once+semantics

## Notes

The classic guidance is to derive the transactional id from the input partitions an instance
handles, so that the identity follows the work. Kafka Streams no longer needs one identity per
partition — since KIP-447 it fences through the consumer group's generation instead — so a
candidate who answers in those terms is also right. What matters is that they see a random or
per-process name defeats the whole mechanism.
