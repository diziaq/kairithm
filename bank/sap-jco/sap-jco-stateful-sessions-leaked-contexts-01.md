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

- A stateful sequence reserves its connection for its exclusive use until it is explicitly
  released; if the release is skipped on an exception path, nothing in the default setup ever
  takes it back, so it is gone until the process dies
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

Verified: failing to close a stateful sequence leaves that connection reserved and open. In the
default, thread-bound setup nothing reclaims it, so it is held until the process ends — which is
why a restart appears to fix the problem.

Verified, and worth having in your pocket as a ceiling probe: a leaked sequence is not
irrecoverable by design. If the application registers a `SessionReferenceProvider`, JCo checks
periodically whether the session is still alive and releases the context and cancels its calls
when it is not. That is a second, structural answer to this card beyond the `finally` block, and
a candidate who reaches it is well above the bar. Do not expect it.

NEEDS-REVIEW — genuinely unverifiable rather than merely unchecked. Whether the SAP application
server itself times out an idle *stateful* RFC session held open by an external client, and which
profile parameter would govern that, could not be confirmed from any public SAP documentation;
the SAP notes that discuss the symptom are behind a login wall. The gateway parameters that do
exist govern registered-program and CPIC connections, which is a different layer, and
`jco.session_timeout` is a client-side setting, not a server one. So: a candidate who assumes SAP
tidies up after them is making an unsupported assumption and should be pushed on it — but do not
assert the opposite either. Confirm with Basis per system.

## Sources

- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
- https://github.com/cemeng/sap-integration/blob/master/sapjco3-darwinintel64-3.0.14/javadoc/com/sap/conn/jco/JCoContext.html
