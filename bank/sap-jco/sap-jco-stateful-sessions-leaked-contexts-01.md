---
id: sap-jco-stateful-sessions-leaked-contexts-01
schema_version: 1
title: Hundreds of sessions your service never gave back
category: sap-jco
topic: stateful-sessions
level: lead
tags: [operations, observability, failure-modes, resource-leaks]
time_estimate_min: 10
order: 210
---

## Ask

Two weeks after a release, SAP complains that your service is holding hundreds of open sessions,
some for days, and your own pool has stopped handing anything out. Restarting clears it for a
while. How do you run this down, and how do you stop it coming back?

## Tests

Whether the candidate can diagnose a reserved-resource leak on an error path, and then replace
the restart habit with a control the team can see and enforce.

## Listen for

- A stateful sequence reserves its connection until it is explicitly released; if the release is
  skipped on an exception path, that connection is gone for the life of the process
- Restarting clears it because the process dies, which is why it looks like a memory problem and
  is not
- Two weeks after a release, growing slowly, points at a rare error path rather than at traffic
- The code fix is the bracket in a `finally`, owned by one place rather than repeated at every
  call site
- The leaked sessions may still hold locks on business objects, so the damage is not only
  resource exhaustion
- To see it: a gauge of open sequences on their side, compared with what SAP reports, and an
  alert on it — "restart it" is not a control
- The structural answer is fewer and shorter stateful sequences, with a cap on how long one may
  live, and stateless as the default

## Expected knowledge

- A reserved connection is not returned to the pool until the sequence is closed
- The error path is the part of the code least likely to have been exercised in test

## Strong signals

- Asks what changed in that release and goes to the diff before the profiler
- Wants the leak reproducible: force the rare failure in a test and watch the gauge not come
  back down
- Asks whether the SAP side cleans up idle sessions on its own today, and refuses to rely on it
  either way
- Treats the recurring restart as an incident that has been normalised, and names who owns
  removing it

## Weak signals

- Schedules a nightly restart and closes the ticket
- Raises the pool limit to buy time with no plan behind it
- Cannot say which resource is being held or by whom

## Answer bands

### mid

- Connects the exhausted pool to connections that were never released.
- Puts the release in a `finally` and expects that to fix it.

### senior

- Explains why the leak tracks failures rather than load, and why a restart appears to fix it.
- Instruments the open sequences so the leak is visible before the pool empties.
- Reproduces the failure path deliberately instead of waiting for it.
- Mentions what the abandoned sessions still hold besides a connection.

### lead

- Removes the pattern rather than the instance: one owner for the bracket, stateless by default,
  a cap on sequence lifetime.
- Replaces the scheduled restart with an alert and a runbook, and says who is accountable.
- Gets an agreement with the SAP side on what they will report and when they will tell you.
- Says how a reviewer would catch the same mistake in the next pull request.

## Follow-ups

- The team's proposal is a nightly restart. Argue the other side.
  probes: whether they can distinguish a workaround with a cost from a fix
- Business users report a document they cannot edit and no one is in it. Connect that to this.
  probes: locks held by abandoned sessions, not just resource counts
- What number goes on the dashboard, and at what value does somebody get woken up?
  probes: turning the diagnosis into an operable control
- The same bug is written again in six months. What stops it reaching production this time?
  probes: making the pattern unwritable rather than relying on review

## Notes

Verified: failing to close a stateful sequence leaves that connection reserved and open for the
life of the process.

NEEDS-REVIEW — unverified claim about automatic cleanup on the SAP side: whether an idle stateful
RFC session is timed out, and which profile parameter governs it, should be confirmed with Basis
for the specific system. Do not let a candidate rely on it, and do not mark them wrong for
asking.
