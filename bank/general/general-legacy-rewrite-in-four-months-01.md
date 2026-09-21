---
id: general-legacy-rewrite-in-four-months-01
schema_version: 2
title: The team wants to rewrite it, and says four months
category: general
topic: legacy
level: lead
tags: [operations, maintainability, failure-modes, estimation]
time_estimate_min: 9
order: 230
---

## Ask

Your team wants to rewrite a ten-year-old service from scratch. They are confident it will take
four months. What do you ask them, and under what conditions would you say yes?

## Tests

Whether the candidate can evaluate a rewrite against incremental alternatives, and knows what a
rewrite costs beyond writing the code.

## Ideal minimal answer

Makes replacing it a piece at a time behind the existing interface the default, and asks the
team to argue the rewrite past that. Names the conditions for yes: the interface holds still, a
working slice in weeks, output compared against the old system, and an agreed stop rule. Prices
the pause in feature work for whoever owns the roadmap.

## Listen for

- Asks what problem the rewrite solves, and whether every part of the pain comes from the code
- Asks how they arrived at four months, and what the estimate assumes about behaviour nobody has
  catalogued
- Points out that the old system encodes years of cases nobody remembers, and asks how those will
  be found
- Asks what happens to feature work and bug fixes during the rewrite, and who serves customers
  meanwhile
- Wants a path where the two run together and traffic moves gradually, rather than a date when
  everything switches
- Asks who the callers are and whether the interface can stay still
- Asks how they will know the new one is right — comparison against the old, not just tests

## Strong signals

- Proposes replacing it a piece at a time behind the existing interface, and says what the first
  piece would be
- Asks what would be done differently this time, and is unconvinced by "we know better now"
  alone
- Requires a demonstrable increment inside a few weeks rather than a result in four months
- Considers the possibility that the team is telling them about morale, and addresses that too

## Weak signals

- Says no to rewrites as a rule
- Approves it because the team is enthusiastic and the old code is bad
- Accepts the four months without asking what it is built on
- Plans a single switchover at the end with no way back

## Answer bands

### mid

- Asks what is wrong with the current service and whether it can be fixed in place.
- Notes that four months is likely optimistic.
- Wants the old one kept running until the new one is proven.

### senior

- Separates the complaints into ones the rewrite fixes and ones it does not.
- Challenges the estimate by asking what behaviour has not been inventoried yet.
- Asks what happens to the roadmap for those four months and who absorbs it.
- Requires a gradual move of traffic with a way back at every step.

### lead

- Offers incremental replacement behind the existing interface as the default, and makes the
  team argue the rewrite past it.
- Names the conditions for yes: a stable interface, a first slice in weeks, a comparison against
  the old system, and an agreed stop rule.
- Prices the pause in feature delivery and takes that decision to whoever owns the roadmap.
- Handles the morale underneath the proposal without letting it decide the engineering.

## Follow-ups

- Three months in, the new one handles the normal cases and the team is discovering rules in the
  old code every week. What do you do?
  probes: whether there is a stop rule, and whether they can kill or contain their own project
- They tell you the old service cannot be changed incrementally because everything is connected
  to everything. How do you test that claim?
  probes: whether they look for seams, or accept an assertion that justifies the answer the team
  wants
- Halfway through, the business asks for a feature that customers are waiting for. Where does it
  go?
  probes: the cost of maintaining two systems, and who decides
