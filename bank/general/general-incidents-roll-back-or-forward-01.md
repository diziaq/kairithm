---
id: general-incidents-roll-back-or-forward-01
schema_version: 2
title: Three in the morning, a one-line fix or a rollback
category: general
topic: incidents
level: senior
tags: [operations, failure-modes, consistency, data-modelling]
time_estimate_min: 8
order: 150
links:
  deeper: [general-incidents-third-time-same-outage-01]
  related: [database-cloud-databases-aurora-failover-four-hour-outage-01]
---

## Ask

Forty minutes into an outage you have a strong suspicion about the cause and a one-line change
you believe fixes it. You also have a rollback you know works, except that the release it would
undo already ran a schema migration against the live database. It is three in the morning. How
do you decide?

## Tests

Whether the candidate decides under time pressure from reversibility and blast radius rather
than from which option feels more like real engineering.

## Ideal minimal answer

Asks what the migration did and whether the old code can still run against the changed data,
then decides from the cost of being wrong on each path rather than which is more likely right.
Looks for a third option that stops the bleeding without either deploy, and fixes a time limit
and the next move before starting.

## Listen for

- Asks what the migration did, and whether the old code can run against the new shape of the
  data
- Treats a rollback across a migration as a data question, not a deployment question
- Weighs "I believe this fixes it" against "I have seen this work", and says how much that belief
  is worth at three in the morning
- Considers options beyond the two offered: disable the feature, shed the traffic, fail the
  affected path gracefully, put a flag over it
- Wants the fix verified somewhere before it goes to everyone, even if that costs minutes
- Names who else is awake and who decides if it goes wrong

## Strong signals

- Asks whether the migration was written so that the previous version still works — and says
  that whether it was is the real answer to the question
- Puts a time limit on the attempt and states the fallback before starting it
- Thinks about what a partly rolled-back fleet looks like while it is happening

## Weak signals

- Picks one option on instinct with no question about the migration
- Pushes the untested one-liner straight to production because it is small
- Insists on always rolling back, without asking what that does to data already written
- Wakes nobody and tells nobody, because it is the middle of the night
- Sets the rollback and the one-line change side by side and will not choose between them

## Answer bands

### weak

- Chooses immediately, with no question about what the migration changed.
- Argues the one-line change is safe because it is short.
- Has no plan for what happens if the chosen option makes things worse.

### mid

- Asks what the migration did and whether the previous version can still read the data.
- Prefers the reversible option and says why.
- Wants the change tested somewhere, or released to a slice of traffic, when asked what they
  would do before the whole fleet sees it.

### senior

- Frames the choice as the cost of being wrong on each path, not the probability of being right.
- Produces a third option that stops the bleeding without either deploy, before it is suggested
  to them.
- Sets a deadline and the next move before starting, so the decision is not remade under stress.
- Says what state the system is in if the attempt half-succeeds, and how they would tell.

### lead

- Says who owns the call, who is informed, and what is said to customers either way.
- Treats the fact that this rollback is blocked as the finding to fix afterwards, separately from
  tonight.
- Balances the hours of the people awake against the remaining damage and decides to stop.

## Follow-ups

- You take the one-line change, it goes out, and after ten minutes the error rate is unchanged.
  What now?
  probes: whether they set an exit condition in advance, and whether they can abandon a theory
- The migration added a column the new code fills in and the old code ignores. Does that change
  your answer?
  probes: whether they recognise a backwards-compatible change and what it buys them
- Someone suggests taking the checkout page down entirely for twenty minutes to get clean air to
  work in. Would you?
  probes: deliberate degradation as a tool, and who is allowed to authorise it
