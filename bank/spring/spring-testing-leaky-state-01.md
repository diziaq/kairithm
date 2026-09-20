---
id: spring-testing-leaky-state-01
schema_version: 1
title: Passes alone, fails in the suite
category: spring
topic: testing
level: junior
tags: [testing, correctness, failure-modes]
time_estimate_min: 6
order: 90
links:
  deeper: [spring-testing-rollback-never-commits-01]
  related: [spring-configuration-property-precedence-01]
---

## Ask

A `@SpringBootTest` inserts a customer, calls the service, and asserts on the result. It passes
when you run it on its own and fails when the whole suite runs. A colleague has opened a pull
request adding `@DirtiesContext` to it, which makes the suite green. What do you say in review?

## Tests

Whether the candidate can distinguish a test that is isolated from a test that happens to run
first, and whether they diagnose the shared state rather than accepting a fix that works.

## Listen for

- The tests share something across the suite — most likely rows left in the database by an
  earlier test
- Order dependence means the suite is only green for the order it happened to run in
- Knows a test can roll back what it wrote automatically, and what that requires
- Says why the proposed annotation appeared to help: it changed the ordering or the state, not
  the cause
- Would find the culprit by running the two tests together, not by guessing

## Expected knowledge

- That a test annotated to run in a transaction is rolled back at the end
- That tests should not depend on each other's order

## Strong signals

- Points out the proposed fix makes the suite slower for everyone and hides the defect for the
  next person
- Notices that the automatic rollback does not apply when the test drives the service over HTTP
  against a running server, because that work happens on another thread
- Prefers each test to create the data it needs with values nobody else uses

## Weak signals

- Accepts the pull request because the suite is green
- Suggests forcing an execution order
- Blames flakiness in general with no attempt to find the shared state

## Answer bands

### weak

- Approves the change because the build passes.
- Cannot name anything the two tests could be sharing.

### junior

- Says the tests are sharing state, most likely rows in the database.
- Knows a test can be made to roll back its writes.

### mid

- Explains that the suite is only green for one ordering and that is not isolation.
- Reproduces by running the pair together and names the actual leak.
- Points out what the proposed annotation costs the whole suite, and that it treats a symptom.

## Follow-ups

- The rollback trick does not work for one of their tests: it drives the endpoint over a real
  port. Why not?
  probes: work happening on the server thread, outside the test's own unit of work
- Suppose the shared thing is not the database but a cache, or a static field. Does your
  approach change?
  probes: whether they are hunting shared state in general or just remembered one trick
- How would you prove the suite is order-independent rather than believe it?
  probes: running in a shuffled order in the pipeline

## Sources

- https://docs.spring.io/spring-framework/reference/testing/testcontext-framework/tx.html
- https://docs.spring.io/spring-boot/reference/testing/spring-boot-applications.html

## Notes

`@Transactional` on a test rolls back by default, but not for work done by a server thread — a
`@SpringBootTest` with a real port calling over HTTP writes outside the test's transaction.
`@DirtiesContext` here is a genuine anti-pattern: it makes the suite slower and hides the
ordering dependency, which is the setup for the harder card on the same topic.
