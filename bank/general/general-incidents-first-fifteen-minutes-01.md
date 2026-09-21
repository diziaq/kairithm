---
id: general-incidents-first-fifteen-minutes-01
schema_version: 2
title: You are paged, checkout is failing for one user in five
category: general
topic: incidents
level: mid
tags: [operations, observability, failure-modes]
time_estimate_min: 7
order: 90
links:
  related: [kafka-consumer-groups-flapping-member-01]
  deeper: [general-incidents-roll-back-or-forward-01]
---

## Ask

You are on call. Checkout has been failing for roughly one user in five for the last eleven
minutes. Nothing was deployed today. Take me through what you actually do, in order, from the
moment your phone goes off.

## Tests

Whether the candidate can run a live incident — restoring service, gathering facts and keeping
people informed — and whether they have an order for those things rather than a list.

## Ideal minimal answer

Gives an order: confirm the scale, restore service, tell people, then find the cause. Uses the
one-in-five figure to hunt for what separates the failing fifth — one machine, one region, one
partner — does not read no deploy as nothing changed, and keeps a timeline while it is
happening.

## Listen for

- Confirms the failure is real and measures how bad it is before touching anything
- Puts restoring service ahead of finding the cause, and says so explicitly
- Tells someone: a channel, a status update, the people who will be asked by customers
- Asks what changed, and does not accept "nothing was deployed" as "nothing changed" —
  configuration, feature flags, certificates, a dependency, traffic, data volume
- Notes that one in five smells like a subset: one instance, one region, one shard, one partner
- Keeps a record of what was tried and when, while it is happening

## Strong signals

- Separates the roles out loud — someone drives, someone communicates — even when it is a team
  of two
- Says what they would not do under time pressure: no speculative config edits with no way back
- Mentions knowing beforehand who can authorise a customer-visible action

## Weak signals

- Opens the code and starts reading before looking at any signal
- Restarts everything first and cannot say what that would have told them
- Never mentions telling anybody
- Treats "no deploy" as proof the system did not change

## Answer bands

### weak

- Starts guessing at causes with no measurement of the impact.
- Restarts or scales things at random and hopes.
- Says nothing about informing anyone outside the call.

### junior

- Checks a dashboard and the error logs to confirm the scale.
- Says they would escalate and ask for help.
- Looks for a recent change as the first suspect.

### mid

- Orders the work: confirm, contain, communicate, then investigate.
- Uses the one-in-five figure to hunt for what distinguishes the failing fifth.
- Widens "what changed" past deploys to configuration, data and dependencies.
- Keeps a timeline as they go instead of reconstructing it afterwards.

### senior

- Sets an explicit decision point — if this is not better by a given time, we do X.
- Names what evidence they want to preserve before an action destroys it.
- Talks about the cost of the outage in customer terms and lets that drive how aggressive the
  mitigation is.

## Follow-ups

- Ten minutes in you find that restarting one machine clears it for that machine. Do you restart
  the rest?
  probes: mitigation versus destroying the evidence, and whether they capture state first
- Your manager and two account managers are now messaging you directly for updates while you
  work. How do you handle that?
  probes: splitting the driving and the communicating; a single channel for updates
- It stops on its own after twenty-five minutes and you never found out why. Is the incident
  over?
  probes: whether a self-resolving fault counts as resolved, and what they leave behind
