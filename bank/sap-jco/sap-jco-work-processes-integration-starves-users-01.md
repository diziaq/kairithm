---
id: sap-jco-work-processes-integration-starves-users-01
schema_version: 2
title: Basis want a meeting about your afternoon load
category: sap-jco
topic: work-processes
level: lead
tags: [capacity, performance, operations]
time_estimate_min: 10
order: 230
links:
  related: [kafka-performance-mixed-workloads-01]
---

## Ask

Basis have asked for a meeting: every afternoon your integration takes the whole application
server and their interactive users sit watching hourglasses. They want you to move it to the
night. What do you bring to that meeting?

## Tests

Whether the candidate treats SAP capacity as a shared budget to be negotiated with evidence, and
knows the levers that exist on both sides before agreeing to a schedule change.

## Ideal minimal answer

Bring measurements: how many calls run in parallel, how long each holds a work process, when,
and what share of the instance that is, since the load lands in the dialog processes the users
need. Then negotiate a monitored allocation with an owner on each side, starting from how fresh
the data must be rather than from the load graph, and say what is delayed when the cap bites.

## Listen for

- Comes with measurements: how many calls in parallel, how long each holds a work process, at
  what times, and what share of the instance that is
- Knows the load lands in the same dialog work processes the interactive users need, which is
  why they feel it
- Knows the SAP side has controls of its own — a minimum number of dialog processes kept free of
  RFC load, and quotas on what one caller may occupy — so the system can protect itself rather
  than relying on your good behaviour
- Options beyond moving to the night: cap concurrency on the client side, spread the work across
  the hour instead of a burst, send the long units to background processing, put the RFC load on
  its own application server or logon group
- Pushes back where the business needs it: state how fresh the data must be before accepting a
  schedule that makes it stale
- Offers a limit they will enforce and that both sides can monitor, not a promise

## Expected knowledge

- Dialog work processes are a shared, finite resource on an instance
- Background processing has different limits and a different queue

## Strong signals

- Arrives with a number for the business cost of the interface being slower, so the trade is
  explicit on both sides
- Proposes a shared dashboard rather than each side measuring its own version of the truth
- Says who gets paged when the cap is enforced and work runs late
- Treats Basis as a partner allocating a budget, not as an obstacle

## Weak signals

- Agrees to move it to the night without asking what depends on the data during the day
- Argues the integration is more important than the users
- Has no measurements and negotiates on impressions
- Brings every lever to the meeting with fair trade-offs, and will not say which one they are
  offering Basis

## Answer bands

### mid

- Accepts there is a shared limit and offers to reduce parallelism.
- Can describe roughly where the load lands inside SAP.

### senior

- Brings measurements and can say what share of the instance the interface takes and when.
- Offers several levers and picks between them against the freshness requirement.
- Knows the SAP side can protect itself and asks for that as a safety net.

### lead

- Turns it into an agreed, monitored allocation with a named owner on each side.
- States the business requirement the schedule has to satisfy, and negotiates from it rather
  than from the load graph alone.
- Decides what happens when the cap is hit — what is delayed, who is told — before it happens.
- Proposes where this load belongs in the landscape over the next year, not only this quarter.

## Follow-ups

- Basis suggest they will simply reserve capacity so you can never take the last one. What does
  that do to your interface?
  probes: whether they can see the effect of the safety net on their own throughput
- The business says the data must be current within fifteen minutes. Does the night still work?
  probes: whether requirements drive the schedule rather than convenience
- Both of you have numbers and they disagree. How do you settle it?
  probes: a shared measurement everyone trusts
- What do you commit to in the meeting, and what do you refuse to commit to?
  probes: whether they can make an enforceable promise instead of a vague one

## Notes

Verified, as interviewer background and never as a recall test: `rdisp/rfc_min_wait_dia_wp`
reserves a number of dialog work processes that RFC load may not take, and the dispatcher only
hands an RFC request to a dialog work process if that many would still be free afterwards. A
quota family exists alongside it — `rdisp/rfc_use_quotas` switches it on, and
`rdisp/rfc_max_own_used_wp`, `rdisp/rfc_max_login` and `rdisp/rfc_max_own_login` cap, as
percentages, how much one caller may occupy. The point for the card is that the system can
protect itself rather than depending on the integration team behaving, so "we promise to be
careful" is the weaker half of the answer.

This card is about negotiating a share of a shared SAP instance with evidence, and about the
levers that exist on the SAP side and in the landscape. The connection-pooling capacity card
looks similar and is not: that one is about where a client-side limit can be enforced at all
once the instance count is dynamic. Do not run both in the same interview.

## Sources

- https://help.sap.com/doc/saphelp_ewm900/9.0/en-US/08/0b6835b2334756a1e9e1abb86dcf61/content.htm
- https://help.sap.com/doc/abapdocu_751_index_htm/7.51/en-us/abenapp_server_resources.htm
