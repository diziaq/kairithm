---
id: spring-testing-rollback-never-commits-01
schema_version: 2
title: Green because it never committed
category: spring
topic: testing
level: mid
tags: [testing, transactions, correctness, failure-modes]
time_estimate_min: 8
order: 91
links:
  deeper: [spring-testing-context-cache-01]
  related: [spring-transactions-self-invocation-01]
---

## Ask

A service test class is annotated `@Transactional`, so every test rolls back at the end. One test
saves an order, calls `service.close(id)`, reads it back and asserts. It has been green for a
year. In production that same call fails on a unique constraint, and a listener that is supposed
to run once the order is stored has never fired in a test. Why does the test see neither?

## Tests

Whether the candidate knows that a test which rolls back never reaches the moment the database
and the framework do their end-of-transaction work, can name which defects that hides, and can
decide which tests should keep rolling back anyway.

## Ideal minimal answer

The test never commits, and the writes are held until something pushes them out, so the
constraint is never judged and the read is answered from what the test already holds. Push the
pending writes out and clear them before asserting. The listener is attached to the successful
end of a unit of work, which this test is built never to reach.

## Listen for

- The test never commits, so nothing that only happens at commit happens here
- Writes are held until something pushes them to the database; a read that is served from what
  the test already has in hand pushes nothing
- Says the assertion may be handing back the very object the test put there a moment ago, rather
  than anything the database was asked for
- Pushes the pending writes out and empties what is held before asserting, so the check has to go
  to the database and the constraint is evaluated
- The listener is attached to the end of a successful unit of work, and that is precisely the
  moment this test is built never to reach
- Knows a test can be made to commit for real, and that the price is cleaning up afterwards —
  which is the problem the rollback was solving in the first place
- Code under test that asks for a separate unit of work of its own does commit, and survives the
  rollback, so a rolled-back test is not a faithful model in either direction

## Expected knowledge

- A test that runs inside a transaction is rolled back when it ends, by default
- Changes made through the persistence layer reach the database when they are pushed out, not
  when the method that made them returns
- Behaviour can be attached to the successful end of a unit of work

## Strong signals

- Points out that an assertion written as a query against the same table pushes the writes out on
  its own, so the identical defect is caught in one test and missed in the next
- Would rather have a small number of tests that commit for real and clean up after themselves
  than remove the rollback from everything
- Notices that a rolled-back test also never exercises what the database does at the end of a
  unit of work — deferred checks, anything fired by a completed write
- Asks whether that listener is covered anywhere at all, instead of only repairing this one test

## Weak signals

- Concludes the test is correct and the production code is at fault
- Removes the rollback from the whole class so everything commits, with nothing said about what
  the suite looks like the next morning
- Adds a pause or a second read until it goes red
- Believes the row is in the database as soon as the save call returns

## Answer bands

### weak

- Says the database behaves differently under test, with no account of what differs.
- Believes the row has reached the database the instant the save call returns.
- Removes the rollback from the whole class and stops there.

### junior

- Says the test rolls back, so nothing it wrote was ever made permanent.
- Suggests letting this one test commit so it does what production does.

### mid

- Explains that the statements are held back until something pushes them, and that the database
  only judges them at that point.
- Pushes them out before the assertion and clears what is held, so the read goes to the database.
- Ties the silent listener to a successful ending that this test never gets to.

### senior

- Separates the two symptoms and says which tests should keep rolling back and which need a real
  commit, rather than changing the rule for everybody.
- Says what a committing test costs the suite and how its rows get removed afterwards.
- Points out, without being asked, that an assertion which happens to issue a query pushes the
  writes out by itself, which is why the same mistake is caught in one place and missed in
  another.
- Names what else a rolled-back test silently skips, beyond the two symptoms in front of them.

## Follow-ups

- The same test is rewritten to fetch the order with a query over the table instead of by its id,
  and it immediately goes red. What did that change?
  probes: whether they know a query forces the held writes out, and that the first version was
  reading its own copy

- A colleague reacts by taking the rollback off the whole class so the tests behave like the real
  thing. What does the next person to run the suite find?
  probes: whether they connect this straight back to rows left behind and order-dependent tests

- Which of these tests would you let commit for real, and what does that one owe the suite in
  return?
  probes: a deliberate split rather than a blanket rule, and who removes the rows

- Part of the code under test asks for a unit of work of its very own, separate from the caller's.
  What is in the table after your test finishes?
  probes: the ceiling — that such a write commits and outlives the rollback

## Sources

- https://docs.spring.io/spring-framework/reference/testing/testcontext-framework/tx.html
- https://docs.spring.io/spring-framework/reference/data-access/transaction/event.html
- https://docs.spring.io/spring-boot/reference/testing/spring-boot-applications.html

## Notes

Verified: the TestContext framework rolls a test-managed transaction back by default;
`@Commit` reverses that for a class or a method, and `TestTransaction` lets a single test end and
start one mid-way.

Verified: Hibernate's default flush mode is `AUTO`, which flushes before a query whose tables
overlap the pending writes. A `findById` answered out of the persistence context issues no query
and so flushes nothing — which is exactly why the same missing-flush defect is caught by one
assertion style and sails past another. `TestEntityManager.flush()`, or `flush()` plus `clear()`,
is the usual repair.

Verified: `@TransactionalEventListener` runs in the `AFTER_COMMIT` phase unless told otherwise, so
under a rolled-back test it never fires at all.

`Propagation.REQUIRES_NEW` inside the code under test suspends the test's transaction and commits
its own, so those rows survive the rollback and are left behind. It is the mirror image of the
main defect and is what the last follow-up is for.

This card sits between the leaky-state card, whose fix is the rollback, and the context-cache
card. Do not let the answer drift into suite runtime; that belongs to the harder card.
