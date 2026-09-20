---
id: java-api-design-shared-record-change-01
schema_version: 1
title: Adding a field to a record forty services compile against
category: java
topic: api-design
level: lead
tags: [api-design, operations, consistency]
time_estimate_min: 10
order: 810
links:
  related: [kafka-delivery-acks-min-isr-01]
---

## Ask

`record Money(BigDecimal amount, String currency)` lives in a shared library that forty services
compile against. Finance now needs every amount to carry the rounding rule it was calculated with.
Someone has opened a pull request adding a third component. Walk me through what happens next.

## Tests

Whether the candidate can reason about compatibility for consumers they do not control, and choose a
change that can actually be rolled out.

## Listen for

- Adding a component changes the generated constructor, the accessors, equality and any pattern that
  takes the value apart, so code compiled against the old shape breaks when it meets the new jar
- Distinguishes what fails at build time from what fails at run time, and which is worse for a
  service that is only rebuilt once a quarter
- Asks whether the new information belongs on this type at all, or on the operation that produced it
- Proposes a route: a separate type, or a factory alongside the old shape, or a version bump with a
  stated window and named owners across the forty
- Says what equality now means — two amounts that are numerically the same but carry different rules
  stop matching, which changes behaviour anywhere they are used as keys
- Asks who is the source of truth for the rounding rule before it is copied into forty places

## Expected knowledge

- Which members a record generates, and that they are part of the published surface
- Version numbers as a promise to consumers rather than a field in a build file

## Strong signals

- Asks how the library is released and how a consumer even finds out a new version exists
- Names the consumers who cannot move and designs around their timeline instead of wishing it away
- Points out that a value type in a shared library is the hardest thing in the estate to change, and
  treats that as a reason to keep it small

## Weak signals

- "Records are immutable, so changing one is safe"
- Adds the component and asks everybody to rebuild on the same day
- Gives the new component a default value and assumes nothing else is affected

## Answer bands

### mid

- Knows the change breaks callers and that they will have to be rebuilt.
- Suggests a version bump and a note to the other teams.
- Does not distinguish a build failure from a runtime one, or raise equality.

### senior

- Enumerates what the change does to the generated members and to anything compiled earlier.
- Separates consumers that rebuild often from those that do not, and says which failure each sees.
- Offers a route that lets both shapes exist during a window.
- Raises that equality changes meaning, and looks for where these values are compared or keyed.

### lead

- Asks first whether the information belongs on this type, and is willing to reject the pull request
  on design grounds.
- Plans the rollout across forty consumers with owners, a window and a fallback for stragglers.
- Names who owns the rounding rule, so it is not duplicated into forty codebases.
- Says what this episode says about the shared library itself, and what they would change about how
  it is versioned and released.

## Follow-ups

- Two of the forty are built from a branch nobody maintains any more. What does that do to the plan?
  probes: consumers who cannot move; coexistence rather than a single cut-over day
- These values are used as keys in a lookup built earlier in the pipeline. What breaks quietly?
  probes: equality changing under a map; a wrong result with no exception anywhere
- Six months later Finance asks for a fourth thing to travel with every amount. What do you wish
  you had done now?
  probes: whether the design leaves room; factories and a type that can grow without breaking

## Notes

The binary contract point is the one people miss: a caller compiled against the two-component
constructor does not recompile magically, and the old constructor no longer exists in the new jar.
