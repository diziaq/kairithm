---
id: microservices-failure-handling-cascade-slow-dependency-01
schema_version: 2
title: A slow dependency takes down services that cannot reach it
category: microservices
topic: failure-handling
level: senior
tags: [failure-modes, performance, operations, scalability]
time_estimate_min: 9
order: 20
links:
  related: [microservices-scalability-autoscaled-into-database-01]
---

## Ask

One dependency gets slow. Not down — it goes from forty milliseconds a call to four seconds.
Within two minutes your service is returning 503 on every endpoint, including several that never
touch that dependency. Ten minutes later the three services that call *you* are failing too, and
one of those three has no route to the slow dependency at all. Walk me outwards from the slow
dependency: at each service, what fills up, and where would you put something that stops it
travelling further?

## Tests

Whether the candidate can follow the saturation of a bounded resource outward from one dependency
to services several hops away, and can say where the boundary that halts it belongs and who has
to build it.

## Ideal minimal answer

Each in-flight call holds a worker or connection from one shared allocation, so a hundredfold
longer call means a hundredfold more held at once and the allocation empties, and then endpoints
that never touch the dependency queue behind ones that do. The same argument repeats one hop
out, so cap per dependency at every hop and reject quickly instead of queueing work nobody is
still waiting for.

## Listen for

- Each in-flight call occupies a unit of a service's finite capacity — a worker, a connection, a
  slot — and the whole service draws that from one allocation
- A hundredfold increase in how long each call is held is a hundredfold increase in how many are
  held at once, and the allocation runs out
- Once it is empty, requests that need nothing from that dependency queue behind ones that do
- Carries the same argument one hop out: calls into your service now take seconds instead of
  milliseconds, so the callers' own capacity fills for exactly the same reason
- The failure travels as latency, not as errors — each hop looks healthy to an error-rate check
  right up to the moment it has nothing left
- Explains the third caller, which cannot reach the dependency at all: it shares caller-side
  capacity with a sibling call that can
- Puts a ceiling on how much of a service any one downstream is allowed to occupy, so the
  saturation has somewhere to stop
- A call deadline shorter than the caller's own patience, at every hop, so work is abandoned
  rather than accumulated
- Turning calls away quickly beats queueing work nobody is still waiting for, and it is the thing
  that keeps the next hop out from filling

## Expected knowledge

- A service can only be doing a bounded number of things at once, and an occupied slot serves
  nobody else
- Concurrency in use equals arrival rate times how long each call is held
- A dependency that is slow but still answering produces no errors to alert on

## Strong signals

- Sketches the call graph, separates the services that can reach the dependency from those that
  cannot, and then explains why some of the second group failed anyway
- Splits the incident into two faults: the dependency got slow, and no service in the chain had a
  limit
- Notices that the queue itself becomes the problem, and asks how deep each hop lets it get
- Asks what each hop's own deadline was before choosing a value for anything

## Weak signals

- Blames the dependency and stops there
- Adds retries as the fix
- Proposes scaling out, with no account of why more instances each fill up the same way
- Fixes only the service that touches the dependency and has nothing to say about its callers
- Recounts a cascade at a previous employer and never gets to the call graph in front of them

## Answer bands

### mid

- Connects the slowdown to calls piling up and capacity running out in the service that makes them.
- Suggests a shorter call deadline and can say roughly what it should be based on.
- Does not yet explain why unrelated endpoints, or services further out, went down with it.

### senior

- Traces held capacity to an exhausted allocation to unrelated traffic failing, then carries the
  argument one hop out themselves and shows it still holds.
- Bounds the blast radius with a per-dependency ceiling at each hop, and says what happens to the
  calls above it.
- Chooses to reject quickly under overload and justifies it specifically as what stops the failure
  crossing the next boundary.
- Asks how the whole chain behaves when the dependency comes back, not only while it is slow.

### lead

- Decides which services and which endpoints keep working when there is not enough capacity for
  all of them, from what the traffic is worth.
- Names what would have to exist for anyone to see this coming — a saturation signal per
  dependency, not an error count.
- Weighs the running cost and the operational complexity of isolation at every hop against how
  often this happens, and is willing to leave some hops unprotected and say which.
- Says which other teams have to change something for the fix to hold, because the failure crosses
  boundaries they own.

## Follow-ups

- Somebody doubles the pool in the service that calls the slow dependency. What do you expect at
  the next spike, and what do its callers see?
  probes: whether a bigger buffer only delays collapse, and that it delays it for the next hop too
- One of the three services calling you has no route at all to the slow dependency. Explain how it
  ended up failing.
  probes: whether they can carry the argument across a hop rather than repeat it about one service
- The dependency recovers at full speed. Does the whole chain come back on its own?
  probes: backlog drain at each hop, the pile of abandoned work, a second wave from callers
- You can keep exactly one endpoint alive across the whole chain and must drop the rest. Which,
  and who decides?
  probes: prioritisation and load shedding by class of traffic across a team boundary

## Sources

- https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/

## Notes

The distinguishing move is carrying the argument across a hop. A candidate who explains one
service's exhaustion perfectly and stops has answered a smaller question; push them to the callers
and the caller's callers.
