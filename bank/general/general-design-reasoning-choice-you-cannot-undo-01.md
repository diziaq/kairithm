---
id: general-design-reasoning-choice-you-cannot-undo-01
schema_version: 2
title: Picking a store next week, with a third of the requirements
category: general
topic: design-reasoning
level: lead
tags: [data-modelling, operations, api-design]
time_estimate_min: 9
order: 220
links:
  related: [database-choosing-a-store-second-cluster-for-six-people-01]
---

## Ask

You have to choose where a new product area keeps its data, and the decision has to be made next
week. Maybe a third of the requirements are known and the rest will arrive over the next year.
How do you make a choice like that, and how do you stop it becoming something nobody is allowed
to revisit in two years?

## Tests

Whether the candidate can decide under acknowledged ignorance — separating what is cheap to
change later from what is not — rather than either stalling for certainty or picking by
familiarity.

## Ideal minimal answer

Decides from the access patterns and the shape of the data, separating the parts that are cheap
to change from the data written in the first year, which is the real commitment. Writes the
decision down with its reasons and the conditions that expire it, and sets a review point with a
trigger and a named owner.

## Listen for

- Asks which parts of the decision are expensive to reverse and concentrates the effort there
- Works from the access patterns and the shape of the data rather than from a product comparison
- Names the one or two unknowns that would actually flip the answer, and finds the cheapest way
  to learn them this week
- Keeps the choice behind an internal boundary so the rest of the code does not encode it
- Says what would have to be true for them to change their mind, and where that is written down
- Weighs what the team already runs and can operate at three in the morning

## Strong signals

- Points out that the data written in the first year is the thing that is hard to move, not the
  code
- Proposes a spike with a real workload and a deadline, rather than a discussion
- Is explicit that being wrong is acceptable and being unable to find out is not
- Has a view on the cost of a second technology in the estate, beyond this project

## Weak signals

- Picks what they used last time without connecting it to this workload
- Asks for more requirements before deciding, with no plan for getting them
- Wraps everything in an abstraction layer so no choice is ever made
- Treats the choice as permanent and argues for the most general option

## Answer bands

### mid

- Lists what the data looks like and how it will be read and written.
- Compares two options on concrete criteria rather than popularity.
- Says, when pushed on it, that the team's existing experience should count.

### senior

- Sorts the decision into the parts that are cheap to change and the parts that are not.
- Identifies the specific unknowns that would change the answer and how to reduce them quickly.
- Contains the choice behind a boundary so that changing it later touches a known amount of code.
- Brings up what the team can actually operate, not just what performs best on paper, without
  being asked to weigh that.

### lead

- Writes the decision down with its reasons and its expiry conditions, so revisiting it is a
  normal act rather than an admission of failure.
- Treats the accumulated data as the real commitment and plans for how it would be moved.
- Sets a review point with a trigger, and says who owns it.
- Balances the cost of a second technology against the fit of the better one, and decides.

## Follow-ups

- A year in, one of the unknowns lands and it is the one that would have changed your mind. What
  happens next?
  probes: whether the exit was designed, or only promised
- Someone proposes wrapping everything so that swapping later is trivial. What do you say?
  probes: recognising that premature indirection has its own cost and rarely delivers the swap
- The team knows one option well and the other fits the data better. How do you weigh that?
  probes: operability and staffing against theoretical fit
