---
id: spring-transactions-self-invocation-01
schema_version: 1
title: An audit row that disappears with the rest
category: spring
topic: transactions
level: mid
tags: [transactions, correctness, failure-modes, observability]
time_estimate_min: 7
order: 40
links:
  deeper: [spring-transactions-checked-exception-01]
  related: [spring-proxying-final-method-01]
---

## Ask

`OrderService.place()` is annotated `@Transactional`. Inside it, it calls
`this.recordAttempt(order)`, a public method on the same class annotated
`@Transactional(propagation = REQUIRES_NEW)`, so that the attempt is recorded even when the order
fails. When the order fails, the attempt row is gone too. The annotation is definitely there.
Why does it not take effect, and what would you do about it?

## Tests

Whether the candidate knows that the annotation is implemented by something wrapped around the
bean, and can therefore predict exactly which calls it applies to and which it silently does not.

## Listen for

- The annotation is applied by a wrapper the container puts in front of the bean; a call through
  `this` never leaves the object, so nothing intercepts it
- Predicts the observable result: the inner method runs in the caller's transaction, and rolls
  back with it
- Names a fix that makes the call leave the object: moving the method to another bean, or
  driving the second unit of work explicitly in code
- Knows that a separate unit of work here means a second database connection held at the same
  time, and that this has a cost

## Expected knowledge

- What the requested propagation mode is supposed to do at the boundary
- That only calls arriving from outside the object are advised

## Strong signals

- Says the audit row may be a bad fit for the database at all, and asks whether it should be a
  log line or an event emitted after commit
- Warns that self-wiring the bean into itself works but leaves a trap for the next reader, and
  prefers the structural fix
- Mentions that the pool must be sized for two connections per in-flight request once nesting
  is real

## Weak signals

- Says the annotation "only works on public methods" and stops, without connecting that to why
- Adds the annotation to more methods until something changes
- Cannot say what actually happened to the inner method — assumes it did not run at all

## Answer bands

### weak

- Claims the annotation was written wrong, or that the mode does not exist.
- Cannot say whether the inner method ran, or in what context.

### junior

- Knows something wraps the bean and that the internal call skips it.
- Cannot say what the inner method ended up doing, or name a fix beyond "move the code".

### mid

- Explains the wrapper, and that a call on `this` goes straight to the target.
- States the inner work joined the outer unit and rolled back with it.
- Moves the method to a separate bean, or runs the second unit explicitly in code.

### senior

- Reasons about the cost of the fix: a second connection held while the first is open, and what
  that does to the pool under load.
- Questions whether a durable audit record belongs inside the same store at all.
- Says how the team would notice the next occurrence: a test that fails the outer work and
  asserts the row survived.

## Follow-ups

- Someone fixes it by wiring the bean into itself and calling through that reference. Does that
  work, and would you merge it?
  probes: mechanically yes; whether they weigh the trap it leaves behind
- Once it really is a separate unit of work, what does that do to the pool when a hundred
  requests are in flight?
  probes: two connections per request, and pool sizing as a consequence of the design
- Write me the test that would have caught this. What does it assert?
  probes: asserting on state after a deliberate failure, not on the annotation being present

## Sources

- https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html
- https://docs.spring.io/spring-framework/reference/core/aop/proxying.html

## Notes

The interesting part is not "self-invocation does not work" but what the code actually did: the
inner method executed inside the caller's transaction and was rolled back with it. A candidate
who names the rule but cannot say what the audit row did has half the answer.
