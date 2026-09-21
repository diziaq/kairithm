---
id: general-incidents-third-time-same-outage-01
schema_version: 2
title: The same outage, three times in six months
category: general
topic: incidents
level: lead
tags: [operations, failure-modes, testing, observability]
time_estimate_min: 9
order: 200
links:
  related: [spring-troubleshooting-slow-first-requests-01]
---

## Ask

The same kind of outage has now taken your product down three times in six months. Each time the
team wrote up what happened, agreed on actions, and closed them. What do you change?

## Tests

Whether the candidate treats a repeating outage as evidence about the system and the way the
team works, rather than as three unlucky events, and whether they can name a change that would
actually bind.

## Ideal minimal answer

Says the closed actions were the wrong kind — they added care rather than removing the
possibility — and takes the repeat to whoever sets priorities as evidence about ownership, not
luck. Gives the work an owner, a date and a visible measure reported against, and names what the
team stops doing to make room.

## Listen for

- Asks what the three write-ups concluded, and whether they blamed people or conditions
- Notices that closed actions that do not prevent a repeat were the wrong actions
- Distinguishes actions that add vigilance — be careful, add a checklist, review harder — from
  actions that remove the possibility
- Asks whether anyone measured the time from the fault starting to somebody knowing
- Wants the fix prioritised against feature work explicitly, by someone who can actually make
  that trade
- Considers that the three may share a cause nobody has named, and the write-ups stopped one
  level too early

## Strong signals

- Says that an action item without an owner, a date and a way to tell it worked is a wish
- Proposes proving the fix: reproduce the failure deliberately, or run the failure mode on
  purpose, and see the system survive
- Looks at whether the team had the authority and the time to do the earlier actions, and treats
  the answer as the finding
- Separates reducing how often it happens from reducing how long it lasts, and says which is
  cheaper here

## Weak signals

- More process: another review gate, a longer checklist, a stricter change policy
- Concludes the team needs to be more careful
- Proposes a rewrite as the answer without costing it
- Treats the write-ups as the deliverable and never asks whether anything changed

## Answer bands

### mid

- Reads the three write-ups and looks for what they have in common.
- Proposes a concrete technical fix for the shared mechanism.
- Adds monitoring so the next one is noticed sooner.

### senior

- Points out that the actions were closed but the failure was not prevented, and asks what kind
  of action was chosen each time.
- Separates prevention from detection and recovery, and picks where the money goes.
- Wants the fix demonstrated against the failure, not asserted.
- Asks who decided the follow-up work was less important than the next feature.

### lead

- Treats the repeat as a signal about priorities and ownership, and takes that conversation to
  whoever sets them.
- Gives the work an owner, a date and a visible measure, and reports against it.
- Changes the write-up practice so it stops at a mechanism that can be removed rather than at a
  person who can be careful.
- Names what the team will stop doing to make room, and accepts the cost of that publicly.

## Follow-ups

- Your product manager says the team cannot afford the two weeks and asks for a dashboard and a
  written recovery procedure instead. What do you say?
  probes: whether they can price an outage, and whether they can hold a line or trade
  deliberately
- All three of those documents end with the sentence "an engineer made a mistake during the
  release". What do you do with that?
  probes: whether they push past the person to the conditions that made the mistake possible
- Six weeks after your change, how would you know it worked?
  probes: whether they define a measurable outcome instead of declaring victory on delivery
