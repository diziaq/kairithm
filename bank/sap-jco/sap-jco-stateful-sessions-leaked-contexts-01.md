---
id: sap-jco-stateful-sessions-leaked-contexts-01
schema_version: 2
title: Hundreds of sessions your service never gave back
category: sap-jco
topic: stateful-sessions
level: lead
tags: [operations, observability, failure-modes, resource-leaks]
time_estimate_min: 10
order: 210
links:
  related: [general-incidents-third-time-same-outage-01]
---

## Ask

Two weeks after a release, SAP complains that your service is holding hundreds of open sessions,
some for days, and your own pool has stopped handing anything out. Restarting clears it for a
while. How do you run this down, and how do you stop it coming back?

## Tests

Whether the candidate can diagnose a reserved-resource leak on an error path, and then replace
the restart habit with a control the team can see and enforce.

## Ideal minimal answer

The sequence holds its connection reserved and counted as allocated until it is released, so an
exception path that skips the release leaks it, and the reclaim only fires when the thread that
opened it dies, which on a thread pool never happens. Own the bracket in one place, keep
stateless the default, and replace the nightly restart with a gauge of open sequences, a
threshold and an owner.

## Listen for

- A stateful sequence reserves its connection for its exclusive use until it is explicitly
  released; if the release is skipped on an exception path, the reservation survives the request
  that created it
- The clean-up that does exist is tied to the thread that opened the sequence, so on a thread
  pool — where the threads outlive every request — nothing ever reclaims it
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
- A reserved connection still counts against the pool's limit, which is how the leak becomes an
  exhausted pool rather than just wasted memory
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
- Describes a connection leak they once chased at another company, and never says how they would
  run this one down

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

Verified in the decompiled JCo 3.1.14: failing to close a stateful sequence leaves that connection
reserved, open and **still counted as allocated**. `com.sap.conn.jco.rt.Context.releaseConnection`
skips `releaseClient` while the destination entry exists, and
`com.sap.conn.jco.rt.PoolTimeoutChecker` never touches an allocated connection —
`com.sap.conn.jco.rt.ClientFactory.isTimedOut` requires `getNumUsed() == 0`. So the leak shows up
as an exhausted pool, exactly as in the Ask.

Correction to what this card previously said, and the sharpest thing in it. There *is* a reclaim
path in the default setup, but it only fires when the thread that opened the sequence has died.
`com.sap.conn.jco.rt.SessionTimeoutChecker.run` releases a context when it has been idle longer
than the timeout **and** the session reference provider reports the session dead; the stock
`com.sap.conn.jco.ext.DefaultSessionReferenceProvider.isSessionAlive` answers that from a
`WeakReference` to the originating thread, via `Thread.isAlive()`. In a servlet container or any
thread pool the worker threads outlive every request, so the answer is permanently "alive" and
the context is never released. That is the real reason a restart is the only thing that clears
it — not "nothing reclaims it", but "the condition for reclaiming it never becomes true". A
candidate who gets to "it is tied to the thread, and our threads never die" has found the
mechanism.

Correction, same paragraph: registering a `SessionReferenceProvider` does not switch the check on.
The checker runs either way; a custom provider only changes what counts as a live session — for
example a request or transaction scope that really does end. `Environment` allows exactly one per
JVM (`com.sap.conn.jco.rt.RuntimeEnvironment` throws `IllegalStateException` on a second
registration), so this is an application-wide decision and usually the framework's. Still a
ceiling probe; do not expect it.

Verified, for the "what number goes on the dashboard" follow-up: when the pool is exhausted JCo
names the culprits. `com.sap.conn.jco.rt.ClientFactory.describeAllocatedClients` appends
`[stateful session id: ...]` to every allocated connection that has one and `[stateless]` to the
rest, and that listing goes into the exhaustion message thrown by
`com.sap.conn.jco.rt.PoolingFactory.getClient`. A team that reads the whole exception instead of
its first line gets the leak handed to them.

Verified, and worth knowing before anyone tunes it: the JCo-side timeout is `jco.session_timeout`,
default 600000 ms, checked every `jco.session_timeout.check_interval`, default 300000 ms — both in
`com.sap.conn.jco.rt.SessionTimeoutChecker`. Both are parsed by `JCoRuntime.parseTimeValue` with a
factor of 60000, so **a bare number is read as minutes**, not milliseconds; a suffix such as `s`
or `ms` is needed to mean anything else. When a context is finally released, `Context.reset()`
calls `closeConnections()`, which routes in-flight connections through
`ConnectionManager.releaseWithCancel` and cancels them — so the calls belonging to a dead session
are actively cancelled, not merely abandoned.

NEEDS-REVIEW — one sentence, genuinely unverifiable from the client jar. Whether the SAP
application server itself times out an idle *stateful* RFC session held open by an external
client, and which profile parameter would govern that, is a property of the ABAP side and cannot
be settled here. A candidate who assumes SAP tidies up after them is making an unsupported
assumption and should be pushed on it; do not assert the opposite either. Confirm with Basis per
system.

## Sources

- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
- https://github.com/cemeng/sap-integration/blob/master/sapjco3-darwinintel64-3.0.14/javadoc/com/sap/conn/jco/JCoContext.html
