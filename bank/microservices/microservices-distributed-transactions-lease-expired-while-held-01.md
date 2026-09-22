---
id: microservices-distributed-transactions-lease-expired-while-held-01
schema_version: 2
title: Two workers both believed they held the lock
category: microservices
topic: distributed-transactions
level: senior
tags: [correctness, idempotency, failure-modes, operations]
time_estimate_min: 10
order: 615
links:
  deeper: [microservices-distributed-transactions-compensation-cannot-undo-01]
  related:
    [microservices-idempotency-key-scope-and-lifetime-01, kafka-transactions-zombie-fencing-01]
---

## Ask

A nightly settlement job takes a lock in Redis with a thirty-second expiry and renews it while it
works. One night the process stopped for forty seconds; a second worker took the lock and started
the same job, and both of them then wrote. The proposal on the table is to raise the expiry to
five minutes. What do you say?

## Tests

Whether the candidate sees that a holder cannot know its claim is still valid, and can put the
check somewhere that observes both writers rather than lengthening a timer.

## Ideal minimal answer

Nothing the paused worker could check would tell it the thirty seconds had gone, so five minutes
only makes the collision rarer and the stuck-job outage longer. The lock buys us not usually
running twice; the correctness has to come from the write — the job carries a number that only
ever increases and the store refuses a write carrying an older one.

## Listen for

- The expiry is what the store enforces; the worker's belief that it still holds the claim is a
  separate thing, and after a pause the two disagree with nobody to notice
- A pause long enough to lose it is also long enough to miss every renewal, so renewing faster
  does not close the hole
- Pauses are not bounded: collection, a hypervisor stealing the CPU, a swap storm, a network
  partition that looks identical from inside the process
- Raising the expiry trades one failure for another — while a dead holder's claim stands, nothing
  runs at all, and five minutes of nothing running has its own cost
- Puts the enforcement at the thing being written: each attempt carries a number that only goes
  up, the store keeps the highest it has seen, and a write arriving with a lower one is rejected
- Says explicitly that the second writer must be stopped by the store, because the loser cannot
  be relied on to notice it lost
- Alternatively makes the write safe to run twice, or conditional on the version it read, so two
  runs cannot both land
- Asks what the job writes, because a row can be made conditional and an outbound file or payment
  cannot
- Checks whether Redis itself is the right place to hold this: a single node loses the claim on
  failover, and the multi-node recipe does not remove the need for the check at the write

## Expected knowledge

- A claim with an expiry is granted for a period, not held until released
- A stop-the-world pause is invisible from inside the paused process; time simply moves
- A store can reject a write by comparing a value it already holds

## Strong signals

- Asks how long the job runs and what the longest pause on that box has been, before discussing
  any figure
- Notices that the renewal call itself can fail or be delayed and asks what the worker does then
- Separates efficiency from correctness out loud: the lock is there so two runs are rare, not so
  they are impossible
- Says what to do about the run that already happened twice — how to detect the double effect and
  what it did to the ledger

## Weak signals

- Raises the expiry and stops
- Renews more often and treats the problem as closed
- Adds a second lock, or a lock inside the first
- Says the worker should check it still holds the claim before writing, without noticing that the
  check and the write are two separate moments
- Proposes tuning the collector so the pause cannot happen
- Recounts an incident with the same shape and never says what to change here

## Answer bands

### mid

- Says the expiry passed while the worker was stopped, and that two jobs ran.
- Rejects the five-minute change once asked what it costs when a worker dies holding the claim.
- Reaches for faster renewal or a shorter job as the remedy.

### senior

- Raises it themselves that the holder cannot detect the loss, so no expiry and no renewal rate
  fixes it.
- Moves the enforcement to the write: an ever-increasing number carried with the work and checked
  by the store, which refuses the older one.
- Says which writer wins and why, and that the rejected one must fail loudly rather than
  continue.
- Distinguishes what can be made conditional from a side effect that cannot, and treats those
  differently.

### lead

- Decides whether the job needs exclusion at all, or can be made safe to run twice, and picks one
  with a reason.
- Prices the outage caused by a claim nobody can release against the damage of two writers, and
  says which the business can take.
- Says what the ledger looks like after last night and how the duplicate is found and undone.
- Names what the team would have to build for the check at the store to exist, and who owns it.

## Follow-ups

- The team renew every ten seconds instead of every fifteen. Is the problem gone?
  probes: a pause that spans the renewals, and that the worker cannot see it happen
- Five minutes goes in, and at 00:01 the box running the job is power-cycled. What does the 01:00
  run do?
  probes: the cost of a long expiry — nothing runs until it lapses, with no one to release it
- The job writes forty thousand rows and also sends one file to a partner. Where does the check
  that stops the second worker live for each of those?
  probes: the store enforcing it per row, versus an effect outside any store
- Both workers are inside the write and each believes it is the only one. Which should win, and
  how does the table know which is which?
  probes: an ever-increasing value kept by the resource, rejecting the lower one

## Sources

- https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html
- https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/
- https://research.google/pubs/the-chubby-lock-service-for-loosely-coupled-distributed-systems/

## Notes

The named separator is that a claim with an expiry is a lease, and the check that makes it safe is
a value the written-to resource compares, not a longer timer. Chubby calls it a sequencer and
Redis's own lock page carries the same warning; a candidate does not need either word, only the
mechanism and where it lives.

Figures to release when asked: the job normally runs four minutes, the box has had ten-second
pauses under load before, Redis is a single primary with a replica, and the job writes ledger rows
plus one file to a partner's endpoint.
