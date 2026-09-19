---
id: spring-transactions-remote-call-inside-01
schema_version: 1
title: A payment call inside the database transaction
category: spring
topic: transactions
level: lead
tags: [transactions, consistency, failure-modes, performance]
time_estimate_min: 12
order: 42
links:
  related: [spring-persistence-optimistic-locking-01]
---

## Ask

`checkout()` is one `@Transactional` method: it writes the order, calls the payment provider over
HTTP, publishes an event to the broker, then updates the order to paid. Under Black Friday load
the service stops responding and the logs fill with timeouts waiting for a connection from the
pool. Finance also reports customers charged with no order in the system. You own the redesign —
what do you do, and what do you tell finance about the existing damage?

## Tests

Whether the candidate can see a transaction as a resource held for a duration, recognise that
two independent systems cannot be made atomic by wrapping them in one annotation, and choose a
design whose failure modes they can name.

## Listen for

- The database connection is taken at the first statement and held until the method returns, so
  the remote call's latency is added to how long every request holds a connection
- Pool exhaustion follows arithmetic: concurrent requests against pool size and hold time, and
  adding threads makes it worse rather than better
- Two systems, one rollback: whatever order the calls are in, there is a window where one has
  happened and the other has not
- Shrinks the boundary so only database work is inside it, and moves the remote call out
- Makes the effect recoverable rather than atomic: record the intent durably, act after commit,
  retry, and make the provider call safe to repeat
- Says what happens when the process dies between the two, and who or what finishes the job

## Expected knowledge

- That the broker publish inside the boundary can succeed while the transaction rolls back
- Publishing work after the commit point, and that it can itself fail
- Timeouts on every remote call, and that no timeout is the worst default

## Strong signals

- Asks for the pool size, the timeout, and the p99 of the provider before proposing anything
- Reaches for a durable record of the intent plus a worker that drains it, and can say why that
  is better than a distributed transaction here
- Insists on a stable key on the provider call so a repeat does not charge twice, and asks
  whether the provider supports one
- Treats the existing charges as a reconciliation job with a defined query, not as an apology

## Weak signals

- Raises the pool size and the timeout and declares it fixed
- Proposes a two-phase commit across HTTP and the database without any account of the cost
- Moves the remote call after the commit and stops, with no answer for a crash in between
- Says "make it async" with no statement of what is now guaranteed

## Answer bands

### weak

- Tunes pool size or timeouts and does not touch the structure.
- Cannot explain why holding the connection for the remote call matters.

### mid

- Identifies that the connection is held for the whole method, including the remote call.
- Moves the remote call outside the boundary and shortens what the transaction covers.
- Knows the charge and the order can disagree, without a concrete way to close the gap.

### senior

- Does the arithmetic on hold time, pool size and arrival rate, and shows where it breaks.
- Records the intent in the same transaction and acts on it after the commit point.
- Names the crash window and says which side is left inconsistent, then makes the repeat safe.
- Puts timeouts and a bound on retries on the provider call.

### lead

- Chooses the design from stated constraints — how bad a duplicate charge is, how late a
  confirmation may be — rather than by pattern.
- Defines the reconciliation for the damage already done, and who runs it.
- Says what is measured afterwards so the next regression is visible before finance finds it.
- Names the operational cost of the new machinery and who maintains the worker.

## Follow-ups

- The provider takes the money, and the process is killed one millisecond later. What does the
  next attempt do?
  probes: safe repeats and a stable key on the remote call, not just ordering
- The publish to the broker happens and then the commit fails. Who finds out?
  probes: effects inside the boundary that the rollback cannot undo
- Your design adds a background worker. What does the team have to watch, and what pages
  someone?
  probes: the operational cost they just bought
- Finance wants the list of affected customers by Monday. Where does it come from?
  probes: whether the data model lets them reconcile at all

## Sources

- https://docs.spring.io/spring-framework/reference/data-access/transaction/event.html
- https://docs.spring.io/spring-boot/reference/data/sql.html

## Notes

`@TransactionalEventListener(phase = AFTER_COMMIT)` is the Spring mechanism for acting after the
commit, and it is not durable: if the process dies after commit, the listener never runs. That is
exactly the window a durable record of the intent is for. A candidate who reaches for the
listener and can name its gap is stronger than one who reaches for an outbox by name and cannot.
