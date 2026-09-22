---
id: java-concurrency-lock-ordering-transfer-01
schema_version: 2
title: Threads that stop without failing
category: java
topic: concurrency
level: mid
tags: [failure-modes, operations, observability]
time_estimate_min: 7
order: 15
links:
  deeper: [java-concurrency-visibility-flag-01]
---

## Ask

A transfer method takes the lock on the account money is leaving, then the lock on the account it
is going to, and moves the balance. Twice this month a handful of request threads have gone quiet
in production — no CPU, no errors, nothing in the log — and the pool filled up until the service
answered nothing at all. What happened, and what would you change?

## Tests

Whether the candidate can construct the interleaving that leaves two threads waiting on each other
for good, and weigh the available fixes against each other rather than reaching for the coarsest
one.

## Ideal minimal answer

Builds the pair of opposite transfers between the same two accounts, each holding one lock and
waiting for the one the other holds, and says the wait never expires, so nothing failed and
nothing was logged. Asks for a dump while it is stuck, and weighs a fixed order against one
coarse lock and a bounded attempt, naming what each costs.

## Listen for

- Two transfers between the same pair of accounts in opposite directions each take one lock and
  then wait for the one the other is holding
- Nothing gives up: an intrinsic lock has no timeout, so those threads sit there for the life of
  the process, which is why nothing was logged and nothing failed
- Wants a dump of the running process while it is stuck, and knows the JVM points at the cycle
  itself rather than making you read the stacks
- Names a fix and what it costs: taking the two locks in an order fixed by something stable on the
  accounts, or one coarse lock over all transfers, or a bounded attempt that abandons the transfer
  and retries
- A single coarse lock removes the cycle and serialises every transfer in the service, whether or
  not the accounts have anything to do with each other
- A bounded attempt turns a hang into a failure somebody has to handle, so the caller's answer
  becomes part of the decision

## Expected knowledge

- A lock taken with `synchronized` is held until the block exits and cannot be abandoned
- `ReentrantLock` can be told to give up after a period
- A thread dump shows what each thread holds and what it is waiting for

## Strong signals

- Asks where else in the codebase those two locks are taken, since the cycle only needs one other
  path that takes them the other way round
- Puts the ordering rule in the one place every caller has to go through instead of writing it in
  a comment
- Raises what happens when the two accounts order equal, or when the value being ordered on can
  change
- Asks whether anything slow — a network call, a query — happens while one of the locks is held

## Weak signals

- Adds a timeout without saying what the caller is told when it expires
- Restarts the service and closes the ticket, because there is nothing in the log to chase
- Concludes that the method needs more locking, or wraps a wider block
- Describes the ordering rule, the coarse lock and the bounded attempt fairly and will not say
  which one goes in
- Tells the story of two threads freezing at a previous job and never comes back to these accounts

## Answer bands

### weak

- Describes the threads as slow or stuck and goes looking at the database.
- Asks for a bigger pool or a restart schedule.
- Cannot say what each of the two threads is waiting for.

### junior

- Says two threads are each holding something the other one needs.
- Suggests taking the two locks in the same sequence every time.
- Cannot say how to confirm it from a process that is doing it right now.

### mid

- Builds the pair of concurrent transfers that produces the cycle and walks both threads through it.
- Asks for a dump from the stuck process and says what it expects to see in it.
- Weighs an ordering rule against one coarse lock and against a bounded attempt, and, when pushed,
  says what each costs in throughput or in a failure the caller now sees.
- Points out that the absence of errors is a property of this fault, so an alarm on errors will
  never fire for it.

### senior

- Puts the rule behind a single entry point so a new caller cannot reintroduce the cycle.
- Asks before anybody raises it what else is held, or acquired, inside the region, and treats a
  slow call in there as the same class of problem.
- Decides what the caller is told when an attempt gives up, and treats that as a product question
  rather than a default.

## Follow-ups

- Same two accounts, but one of the threads is only reading both balances to print a statement.
  Does that change anything?
  probes: whether a read path taking the same pair can join the cycle

- Your change goes in, the freezes stop, and the p99 on transfers doubles under load. What did you
  trade away?
  probes: how wide the lock they chose is; unrelated accounts waiting on each other

- It happens again at three in the morning and you are not the one on call. What do you want in
  place so that whoever is can tell in five minutes?
  probes: capturing a dump on the symptom, and watching for work that stops finishing rather than
  for errors

## Notes

The junior card on this ladder is about two threads corrupting a value; this one is about two
threads making no progress at all. A candidate who names the situation in the first sentence but
cannot produce the interleaving, or who cannot say what a coarse lock costs, has not answered it.

## Sources

- https://docs.oracle.com/en/java/javase/21/docs/specs/man/jstack.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html
