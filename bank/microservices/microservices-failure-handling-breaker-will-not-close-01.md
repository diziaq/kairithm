---
id: microservices-failure-handling-breaker-will-not-close-01
schema_version: 2
title: It opened at two in the morning and it is still open
category: microservices
topic: failure-handling
level: senior
tags: [failure-modes, operations, performance, correctness]
time_estimate_min: 9
order: 605
links:
  related:
    [
      microservices-retries-storm-after-outage-01,
      microservices-failure-handling-cascade-slow-dependency-01,
    ]
---

## Ask

A dependency failed for twenty minutes at two this morning and has been healthy since three. It
is now half past nine, one of your endpoints still fails instantly for every user, and nothing
has reached that dependency since 02:14. On-call want to redeploy to clear it. What is happening,
and what would let it come back on its own?

## Tests

Whether the candidate understands that a service which has stopped calling a dependency has to
send something through to find out it recovered, and can say what a trial call proves and what it
does not.

## Ideal minimal answer

It is not a latch someone clears: after its wait it lets a few trial calls through and goes
straight back to failing if they fail. So the trial calls are still failing — the dependency is
healthy but this client's path to it is not, and a redeploy would hide that. I would find out
what those calls return before touching any setting.

## Listen for

- Knows the middle state exists and what it is for: after a wait, a small number of real calls are
  let through, and their outcome decides whether normal traffic resumes
- Something has to be allowed to fail for it to recover — with every call refused locally, no
  evidence about the dependency can ever arrive
- Asks what the trial calls actually returned, rather than assuming the state is stale
- Reaches the point that the dependency being healthy and this client's path being healthy are
  two different claims — connections held from before the restart, a cached address, credentials
  that expired during the outage
- Notices that a redeploy makes the symptom go away by rebuilding the client, which is why nobody
  has ever found the cause
- Says what has to be true for recovery without human help: traffic on that path, or synthetic
  calls that stand in for it when there is almost none
- Treats the state as per-process: forty copies of the service each hold their own, and a
  dashboard showing one figure is hiding thirty-nine
- Asks what counted as a failure — a refusal from the dependency, a slow call, or a fallback of
  the client's own that throws

## Expected knowledge

- A service that refuses calls locally learns nothing new about the thing it refuses to call
- Trial traffic after a wait is how the state advances; without calls it does not advance
- Connections, resolved addresses and tokens obtained before an outage can be invalid after it

## Strong signals

- Asks the request rate on that endpoint before reasoning about how long recovery should take
- Separates "the dependency is up" from "our client can reach the dependency" and says how to
  test each
- Asks whether the fallback path is counted as a success, and notices that it would mask the
  failure rate entirely
- Wants the state and the trial outcomes visible per instance, not as one number across the fleet

## Weak signals

- Redeploys or restarts to clear it and calls that the fix
- Cuts the wait to five seconds, or raises the failure threshold so it stops tripping
- Wires recovery to the dependency's own health page instead of to real calls
- Removes the whole mechanism because it caused an outage
- Tells the story of a past incident with the same shape without saying what to do here

## Answer bands

### mid

- Says the thing needs a call to go through before it can know the dependency is back, once
  prompted.
- Wants to look at the failure rate and the wait setting, and can explain what each does.
- Does not yet ask what the trial calls returned or consider that they are still failing.

### senior

- Explains the middle state without waiting to be asked, and says that a small number of calls
  must be permitted to reach the dependency and their outcome is the deciding evidence.
- Concludes the trial calls are failing and goes looking for a cause on the client's side of the
  wire rather than blaming stale state.
- Rejects the redeploy as a diagnosis, and says what it would destroy.
- Asks the request rate and the number of instances before estimating how long this takes to
  clear by itself.

### lead

- Decides what happens on low-traffic paths: calls generated for the purpose, shared state, or an
  accepted manual step with an owner.
- Says what a dependency that fails for one tenant in ten does to a single service-wide figure,
  and puts the boundary per dependency, per endpoint or per key instead.
- Weighs the protection against the outages it causes, and is willing to name paths that should
  not have it at all.
- Names what the interviewer's team would have to run to see the state per instance and what the
  trial calls returned.

## Follow-ups

- On-call redeploy, the endpoint works again, and everyone goes back to bed. What has the team
  learned?
  probes: the restart rebuilds the client's own broken path and hides the cause for next time
- Someone suggests resuming from the dependency's own status page rather than from your own calls.
  What could go wrong?
  probes: the dependency being up is not this client being able to reach it
- Different day: one tenant in ten gets errors from that dependency and everyone else is fine.
  What does the thing do, and is that what you want?
  probes: one aggregate rate versus isolation per key; all-or-nothing tripping
- That endpoint gets two calls a minute and you run forty copies of the service. How long until
  it clears by itself?
  probes: per-process state, traffic starvation, and calls made for the purpose of probing

## Sources

- https://resilience4j.readme.io/docs/circuitbreaker
- https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker
- https://sre.google/sre-book/handling-overload/

## Notes

Figures to release when asked, for the scene as written: it opens at a 50% failure rate over the
last hundred calls, waits sixty seconds, then permits ten calls before resuming normal traffic,
and any failure among those ten sends it back. The automatic move into the trial state is off in
Resilience4j by default, so the state only advances when a call arrives. The endpoint takes about
two calls a minute across forty instances, each holding its own state.

The cause in the scene: the dependency was restarted behind its load balancer during the outage
and answers on a new address; this client resolved once at start-up and its pooled connections
point at the old one. Every trial call fails, so the state returns to failing for another sixty
seconds, for ever. The redeploy fixes it by accident.
