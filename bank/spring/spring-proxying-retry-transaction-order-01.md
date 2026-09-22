---
id: spring-proxying-retry-transaction-order-01
schema_version: 2
title: Retry and transaction on the same method
category: spring
topic: proxying
level: lead
tags: [retries, transactions, failure-modes, correctness]
time_estimate_min: 10
order: 52
links:
  related: [spring-transactions-remote-call-inside-01]
---

## Ask

To survive database deadlocks, a team puts `@Retryable` and `@Transactional` on the same service
method, with a `@Recover` method that returns a fallback so the caller still gets an answer. It
works in their integration tests. In production every deadlock produces three attempts that all
fail, the fallback runs — and the caller still gets an exception, one that is not the deadlock,
thrown on the way out, by code that never appears in their stack trace. You are the tech lead
reviewing this. What is wrong, and what do you require before it ships?

## Tests

Whether the candidate understands that two annotations on one method become two wrappers in an
order, can reason about what each attempt sees when the order is wrong, and can make the correct
order structural rather than incidental.

## Ideal minimal answer

Both behaviours are applied by wrappers around the same method and the retry ended up inside, so
every attempt ran in the unit of work the first failure had already doomed; the recovery returned
normally and the commit threw. Put the retry outside by splitting across two beans rather than
trusting an ordering number, ask whether the work is safe to repeat, and say what the caller is
told.

## Listen for

- Both annotations are applied by wrappers around the same method, and one of them is on the
  outside of the other
- With retry on the inside, every attempt runs inside the one unit of work that the first
  failure already doomed, so the retries cannot succeed
- The recovery returned normally, so the boundary tried to commit a unit of work that the first
  failure had already marked as unable to commit — that is where the unfamiliar exception is
  thrown, and it is why the fallback made things worse rather than better
- The retry has to be outside, so each attempt gets a fresh unit of work
- Making the order explicit: two beans, or driving the unit of work in code inside the retried
  block, rather than relying on relative ordering of the wrappers
- Whether the retried work is safe to repeat at all

## Expected knowledge

- That the relative position of two wrappers on one bean is configurable, and that nothing
  fixes it by default
- What a failed participating unit of work does to the one that contains it

## Strong signals

- Says the integration test passed because it never failed twice, and specifies the test that
  would have caught it: force a deadlock, assert two separate attempts against the database
- Refuses to rely on a numeric ordering setting, because nothing in the code shows it and the
  next upgrade can move it
- Asks whether a deadlock is worth retrying here at all, or whether the write order should be
  fixed so deadlocks stop happening
- Adds a bound and a delay, and asks what the caller is told after the last attempt

## Weak signals

- Sets an ordering number and calls it done, with no test
- Believes the two annotations are independent
- Cannot say why retrying inside the same unit of work cannot work
- Sets out the ordering number, the two-bean split and driving the boundary in code, and will not
  say which one they would require

## Answer bands

### mid

- Recognises the two behaviours are applied by wrappers and that one wraps the other.
- Says the retries are running inside the same unit of work and cannot succeed.

### senior

- Explains why the final exception comes from the commit and not from the deadlock, and why
  returning a fallback from inside the boundary could not rescue it.
- Puts the retry outside by splitting the method across two beans, or by driving the unit of
  work explicitly inside the retried block.
- Specifies the test before being asked for it: provoke the failure twice, assert separate
  attempts reached the database.

### lead

- Rejects relying on a relative ordering setting because nothing at the call site shows it, and
  makes the boundary visible in the code.
- Asks whether the retried work is safe to repeat before allowing any retry at all.
- Questions whether the deadlock should be removed instead of survived, and says how to find out
  which writes collide.
- States what the caller sees after the final attempt, and what gets recorded for operations.

## Follow-ups

- The team offers to set a number that fixes the ordering. Would you accept that?
  probes: whether they distinguish a working configuration from a design the next reader can see
- Their test passes today. What would you ask them to add?
  probes: provoking the failure more than once and asserting on separate attempts
- The method also sends a confirmation email. Three attempts now — what does the customer get?
  probes: whether repeating the work is safe at all, and what should sit outside the retry
- What should the caller see after the last attempt fails?
  probes: the contract at the boundary, and what operations needs recorded

## Sources

- https://docs.spring.io/spring-framework/reference/core/aop/api/advisor.html
- https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html

## Notes

`@EnableTransactionManagement` and `@EnableCaching` both expose an `order` attribute defaulting to
`Ordered.LOWEST_PRECEDENCE`, and Spring Retry's `@EnableRetry` exposes the same attribute; when two
advisors share an order, their relative position is not determined by anything the author wrote.

The failure described is `UnexpectedRollbackException`. The chain matters: the repository call that
deadlocked ran in a participating transaction, whose failure marks the shared transaction
rollback-only; the recovery method then returns normally, and the commit at the outer boundary
throws. Without the recovery the caller would simply see the deadlock exception after three useless
attempts — it is the fallback returning normally that turns it into the unfamiliar one.
