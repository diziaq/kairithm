---
id: general-collaboration-two-engineers-stuck-01
schema_version: 1
title: A week of argument, and the work has stopped
category: general
topic: collaboration
level: lead
tags: [collaboration, delivery, maintainability]
time_estimate_min: 8
order: 250
---

## Ask

Two engineers on your team have spent a week arguing about how a new module should be structured.
The work has stopped. Both of them are competent and both positions are defensible. How do you
end it?

## Tests

Whether the candidate can convert a stalled disagreement into a decision — with criteria, an
owner and a way back — without either steamrolling it or letting it run.

## Listen for

- Gets the two positions stated in terms of what they optimise for, so the disagreement becomes
  comparable
- Asks what evidence would settle it, and whether it is cheap to get — a prototype, a spike, a
  look at how the code changed last year
- Notices when it has become about winning rather than about the module, and addresses that
  privately
- Sets a deadline for the decision and says who makes it if the two do not converge
- Asks how expensive the wrong choice is, and matches the time spent deciding to that cost
- Commits both of them to the outcome afterwards, in public

## Strong signals

- Says that a week is itself the finding, and asks why nobody stopped it on day two
- Distinguishes decisions worth an hour from decisions worth a week, and says which this is
- Writes down what was decided and why, so it is not reopened by the next person
- Is willing to decide it themselves and own the consequences, rather than forcing a false
  consensus

## Weak signals

- Lets it run because the team should resolve things itself
- Picks the more senior person's side to end it quickly
- Splits the difference into a design neither of them would defend
- Calls a long meeting with the whole team to vote

## Answer bands

### mid

- Sits down with both and hears each position.
- Makes the call, or asks them to agree on one, so the work can start.
- Checks afterwards that both are actually working to the decision.

### senior

- Reframes the argument into the criteria each choice serves, and compares against what this
  module actually has to do.
- Looks for the cheapest evidence that would make the answer obvious, and timeboxes it.
- Sets a decision deadline and names who decides if it is not reached.
- Separates the technical disagreement from whatever else is going on between the two.

### lead

- Prices the delay against the cost of being wrong and decides how much more time the question
  deserves.
- Makes it clear that disagree-and-commit is expected, and follows up on whether it happened.
- Records the decision with its reasoning and the conditions for revisiting it.
- Changes something so the next disagreement does not take a week, rather than only settling
  this one.

## Follow-ups

- You make the call. A month later it is clearly the wrong one and the engineer who lost says so
  in a meeting. What do you do?
  probes: whether being wrong is survivable, and whether they revisit without defensiveness
- One of them has quietly started building their version anyway. How do you handle that?
  probes: the difference between a disagreement and a refusal, and where the line is
- Both of them ask you to decide, immediately, without hearing the detail. Do you?
  probes: whether they take a decision away from the people closest to it too readily
