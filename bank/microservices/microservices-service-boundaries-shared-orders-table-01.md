---
id: microservices-service-boundaries-shared-orders-table-01
schema_version: 1
title: Two services, one orders table, and a split marked done
category: microservices
topic: service-boundaries
level: lead
tags: [ownership, consistency, operations, correctness]
time_estimate_min: 11
order: 200
---

## Ask

You inherit two services that were carved out of a monolith a year ago. Both still read and write
the same `orders` table directly. The split is marked done on the roadmap and nothing is currently
on fire. Walk me through how you finish it — or make the case for leaving it as it is.

## Tests

Whether the candidate can price an existing architectural compromise, choose deliberately between
finishing and stopping, and describe a live migration in steps.

## Listen for

- Names what the shared table actually costs: neither team can change the schema alone, a bad
  write from one appears as a bug in the other, and no rule about an order can be enforced in one
  place
- Decides who owns the table first, and makes the other side go through the owner rather than
  splitting the data
- A sequence that runs with the system live: move reads first, then writes, with both sides
  checkable at every step
- Is genuinely willing to say "leave it", and states the conditions under which the answer flips
- Wants evidence before spending quarters on it — how often the schema has blocked someone, how
  often a cross-service bug has come from it
- Notices that half-finished is the worst place to stop, and plans for the possibility of losing
  funding partway

## Expected knowledge

- Two writers to one table cannot be given different rules by the database alone
- A live migration needs both paths to coexist for a period

## Strong signals

- Proposes running the new path alongside the old and comparing results before switching
- Says what happens to reporting, batch jobs and anything else quietly reading that table
- Names the organisational consequence of the ownership decision and how they would handle it

## Weak signals

- Reaches straight for a cutover weekend
- Proposes a distributed lock so both services can keep writing safely
- Declares it must be fixed because sharing a database is against the rules

## Answer bands

### mid

- Lists the problems the shared table causes.
- Wants to give one service ownership and put an API in front of it.
- Describes the end state but not how to get there while the system runs.

### senior

- Sequences the migration so each step is reversible and observable.
- Separates the read path from the write path and knows which is harder.
- Asks who else reads the table before assuming there are two consumers.

### lead

- Prices the problem before solving it, and can articulate the cost of doing nothing.
- Will decide not to finish it, with the conditions that would change that decision written down.
- Makes the ownership call and says what they tell the team that loses.
- Plans for the migration being interrupted, because it will be.

## Follow-ups

- Which of the two teams gets it, and what do you say to the other one?
  probes: making an ownership call and handling the organisational fallout
- Halfway through, one side goes through the new path and one still writes directly. What can go
  wrong in that window?
  probes: reasoning about a live migration rather than describing a diagram
- A year later the roadmap has other things on it and you are 70% through. What has that cost you?
  probes: awareness that a partly-finished split is often worse than either end state
