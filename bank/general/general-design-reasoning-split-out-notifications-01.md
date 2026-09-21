---
id: general-design-reasoning-split-out-notifications-01
schema_version: 2
title: A teammate wants to split out notifications
category: general
topic: design-reasoning
level: mid
tags: [api-design, operations, failure-modes, data-modelling]
time_estimate_min: 8
order: 110
links:
  deeper: [general-design-reasoning-two-teams-one-table-01]
---

## Ask

A teammate proposes pulling the part of your application that sends notifications out into its
own separately deployed service. How do you work out whether that is a good idea, and what would
make you say no?

## Tests

Whether the candidate judges a boundary by what it decouples and what it costs to run, instead
of by whether splitting things up is the accepted style.

## Ideal minimal answer

Asks what problem the split is meant to solve and whether it is the cheapest fix for that, names
what crosses the interface and where the data lives afterwards, says what a user sees when the
far side is unavailable, and offers a module with a narrow interface inside the current codebase
as the intermediate step.

## Listen for

- Asks what problem the split is meant to solve: deploy independence, a different scaling shape,
  team ownership, blast radius
- Asks what data crosses the line, and whether the two sides would end up reading each other's
  tables anyway
- Notes that a call that used to be a function call now fails, retries, arrives twice, or arrives
  late
- Asks who runs it, who is paged for it, and what happens to a notification if it is down
- Considers getting most of the benefit inside the current codebase first — a module with a
  narrow interface
- Asks whether the boundary is stable, or whether every feature will need a change on both sides

## Strong signals

- Asks what the interface would be and tries to name a change that would force both sides to
  deploy together
- Points out that the split turns a transaction into two steps with a gap in the middle, and asks
  what the gap does to correctness
- Treats the operational cost — another deployment, another alert, another on-call surface — as
  a real number, not an afterthought

## Weak signals

- Argues from a style — services good, monolith bad — with no reference to this system
- Cannot name anything that gets harder after the split
- Assumes a network call behaves like a local one
- Says it will scale better without asking what is under load

## Answer bands

### weak

- Answers from a general preference for one architecture over the other.
- Lists only benefits, or only drawbacks, with no connection to this application.
- Cannot say what data or behaviour would cross the boundary.

### junior

- Asks what the split is supposed to achieve.
- Notices it means more to deploy and to monitor.
- Mentions that the call between the two parts could fail.

### mid

- Ties the decision to a specific problem and asks whether the split is the cheapest fix for it.
- Names what the interface would carry and where the data lives afterwards.
- Describes what the user sees when one side is unavailable.
- Offers the in-process version of the same separation as an intermediate step.

### senior

- Uses the shape of expected change to test the boundary: which features touch one side only.
- Points out where a single unit of work becomes two, and what has to happen when the second
  half does not.
- Prices the ongoing cost in people and paging, and says who is signing up for it.
- States the conditions under which they would revisit the decision either way.

## Follow-ups

- Sending a notification is currently part of the same unit of work as saving the order. After
  the split, the order is saved and the send fails. What should happen?
  probes: whether they see the atomic step become two, and what they put in the gap
- Your teammate's real motivation turns out to be that deploys are slow and scary. Does the split
  solve that?
  probes: treating the stated design as a symptom of a delivery problem
- Every new feature for the last year would have needed a change on both sides of this line. What
  does that tell you?
  probes: whether they can read a boundary's quality from the history of change
