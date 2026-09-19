---
id: microservices-failure-handling-cascade-slow-dependency-01
schema_version: 1
title: A slow dependency takes down endpoints that never call it
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
touch that dependency at all. How did a slow dependency take out unrelated endpoints, and what
would you change?

## Tests

Whether the candidate can explain saturation of a shared, finite resource and then bound it,
instead of treating the incident as "the dependency broke".

## Listen for

- Every in-flight call is holding a worker, a thread or a connection from one pool that the whole
  service shares
- A hundredfold increase in how long each call is held means a hundredfold increase in how many
  are held at once, and the pool runs out
- Once the pool is empty, requests that need nothing from that dependency queue behind ones that
  do
- Puts a ceiling on how much of the service one dependency may occupy — separate pools, or a cap
  on calls in flight to it
- A call deadline shorter than the caller's own patience, so work is abandoned instead of
  accumulating
- Turning calls away quickly beats queueing work that nobody is still waiting for

## Expected knowledge

- A server has a bounded number of workers, and an occupied worker serves nobody else
- Concurrency needed equals arrival rate times how long each call is held

## Strong signals

- Notices that the queue itself becomes the problem, and asks how deep it is allowed to get
- Separates the incident into two faults: the dependency got slow, and the service had no limit
- Asks what the caller's own deadline was before choosing a value for anything

## Weak signals

- Blames the dependency and stops there
- Adds retries as the fix
- Proposes scaling out, with no account of why more instances would each fill up the same way

## Answer bands

### mid

- Connects the slowdown to requests piling up and resources running out.
- Suggests a shorter call deadline and can say roughly what it should be based on.
- Does not yet explain why unrelated endpoints went down with it.

### senior

- Traces the path from held connections to an exhausted shared pool to unrelated traffic failing.
- Bounds the blast radius with a per-dependency limit, and says what happens to calls over it.
- Chooses to reject quickly under overload and can justify that over queueing.
- Asks how the service behaves when the dependency comes back, not only while it is slow.

### lead

- Decides which endpoints keep working when there is not enough capacity for all of them, from
  what the traffic is worth.
- Names what would have to exist for the team to see this coming — a saturation signal, not an
  error count.
- Weighs the running cost and the operational complexity of isolation against how often this
  happens.

## Follow-ups

- Somebody doubles the pool size. What do you expect at the next spike?
  probes: whether a bigger buffer only delays collapse; queueing and latency growth
- The dependency recovers at full speed. Does your service come back on its own?
  probes: backlog drain, the pile of abandoned work, a second wave from callers
- You can keep exactly one endpoint alive and must drop the rest. Which, and how does the service
  decide?
  probes: prioritisation, load shedding by class of traffic, knowing their own traffic mix

## Sources

- https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/
