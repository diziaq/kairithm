---
id: java-api-design-absent-value-01
schema_version: 1
title: Three callers, three null pointer exceptions
category: java
topic: api-design
level: senior
tags: [api-design, correctness, failure-modes]
time_estimate_min: 8
order: 800
links:
  related: [spring-di-circular-dependency-01]
  deeper: [java-api-design-shared-record-change-01]
---

## Ask

`CustomerService.findByEmail` returns `null` when there is no such customer, and throws when the
lookup itself fails. Three new callers have each shipped a null pointer exception to production in
the last month. The team wants to change the return type to `Optional`. Is that the fix?

## Tests

Whether the candidate treats the shape of a return value as a contract decision with a cost to
consumers, rather than as a matter of style.

## Listen for

- The real problem is that absence is not expressed in the signature, so every caller has to
  remember; wrapping it makes it impossible to ignore by accident
- Asks whether "no such customer" is an ordinary outcome here or a broken precondition, because that
  decides between an empty result and a thrown failure
- Says what changes for consumers: the change breaks every one of them at compile time, which is the
  point, but it still has to be sequenced
- Notes the wrapper is meant for returning, and that putting it in fields, parameters or collections
  buys nothing
- Points out it does not tell anyone what to do; each of the three still has to decide, and two of
  them may want different things

## Expected knowledge

- Where an empty result is idiomatic, and where a distinct outcome type or a thrown failure suits
  better
- A published signature has consumers whose build stops when it changes

## Strong signals

- Asks to see what the three did with the customer once they had it, to find out whether they wanted
  a default, a failure or a branch
- Suggests the boundary be hostile to missing values in one direction, and says where validation
  belongs
- Considers a result type carrying a reason, when "not found" is one of several ordinary outcomes

## Weak signals

- "Wrap everything" as a policy
- Returns an empty object instead, so the caller cannot tell the difference
- Changes the signature and updates every caller to unwrap immediately, restoring the original bug

## Answer bands

### mid

- Says the current signature hides the missing case and that the change makes it visible.
- Knows the wrapper does not belong in fields or parameters.
- Updates the callers without asking what each of them wanted.

### senior

- Separates expressing absence from deciding what to do about it, and says only the first is being
  fixed.
- Asks whether the missing customer is ordinary or exceptional here, and lets that choose the shape.
- Reads the three call sites before changing the signature.
- Plans the change for consumers rather than assuming one repository.

### lead

- Uses the three incidents as evidence about the contract, and asks what else in this interface has
  the same defect.
- Decides with the people who own the domain whether a missing customer is an error at all.
- Weighs the disruption to consumers against the failure it prevents, and says how it is sequenced.

## Follow-ups

- One of the three creates the customer when the lookup comes back empty; another shows an error
  page. Does one method serve both?
  probes: whether absence is an outcome or a fault, and who gets to decide
- The method sits in a library that other teams compile against. How does this land for them?
  probes: sequencing, deprecating alongside rather than replacing, teams that cannot move yet
- Two of the three call sites now repeat the same three lines. What does that tell you?
  probes: a missing operation on the service; pushing the decision to where the knowledge lives
