---
id: kafka-delivery-exactly-once-claim-01
schema_version: 1
title: A team claims their pipeline is exactly once
category: kafka
topic: delivery-semantics
level: senior
tags: [transactions, correctness, idempotency, consistency]
time_estimate_min: 8
order: 30
links:
  related: [java-concurrency-visibility-flag-01]
---

## Ask

A team tells you their Kafka pipeline is exactly once, end to end, and lands every event in a
Postgres table. What do you ask them before you believe it?

## Tests

Whether the candidate treats a delivery guarantee as a property of a specific boundary that
somebody has to implement, rather than a setting that can be switched on for a whole system.

## Listen for

- Asks where the consumer records its progress relative to the database write, and what the
  window between them looks like
- Knows a Kafka transaction spans the read, the processing output and the offset, and stops at
  the edge of the cluster
- Names the two shapes that actually work: one commit covering both stores, or a repeatable write
  keyed on something the producer already had
- Asks what a repeat would look like in the table, and whether anyone would notice
- Separates the producer's deduplication from anything the consumer does

## Expected knowledge

- Offset commits, and that the committed position is what a new owner resumes from
- Two-phase commit and why nobody wants it here
- The difference between a retry that is safe to repeat and one that is not

## Strong signals

- Has seen the failure in production and can describe the shape of the damage
- Asks about the schema of the target table before asking about configuration
- Points out that "end to end" spans several boundaries and asks which one they mean

## Weak signals

- Accepts the claim because a configuration property is set
- Believes a producer setting alone covers a write into another system
- Cannot describe what a repeat would look like in the data
- Says the guarantee holds because the team has never seen a repeat

## Answer bands

### weak

- Repeats the claim back, or names a configuration property as the whole answer.
- Cannot say what happens if the process dies partway through handling a record.
- Treats the database as part of the cluster.

### mid

- Asks about the ordering of the database write and the offset commit.
- Describes what happens when the process dies in the window between them.
- Knows that making the write repeatable is one way out.

### senior

- Puts the boundary in the right place and says what the guarantee covers on each side of it.
- Describes both workable shapes and what each demands of the target schema.
- Asks what the damage from a repeat actually is, and lets that set how much machinery is worth
  building.
- Treats the absence of reported incidents as weak evidence.

### lead

- Weighs the operational cost of transactions against a repeatable write, in terms of throughput,
  rebalance behaviour and who gets paged.
- Names what the team would have to be able to show for the claim to be auditable rather than
  believed.
- Chooses a position for the boundary based on which team owns the downstream store.

## Follow-ups

- The consumer dies after the row is in Postgres but before it reports its position. What does the
  table look like after it comes back?
  probes: at-least-once behaviour, and whether they reach for a repeatable write
- Suppose a repeat costs almost nothing to the business. Does your answer change?
  probes: whether they let the cost of the damage drive how much machinery is justified
- They want the same claim for an HTTP call to a third party instead of Postgres. What is
  different?
  probes: that the guarantee stops where the cluster stops

## Sources

- https://kafka.apache.org/documentation/#semantics

## Notes

Non-obvious claim worth getting right: a Kafka transaction covers the records produced and the
offsets committed within the cluster. It does not extend to an external store.
