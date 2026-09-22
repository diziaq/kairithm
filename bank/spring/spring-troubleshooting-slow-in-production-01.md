---
id: spring-troubleshooting-slow-in-production-01
schema_version: 2
title: Forty milliseconds in staging, four seconds in production
category: spring
topic: troubleshooting
level: senior
tags: [observability, performance, operations, failure-modes]
time_estimate_min: 10
order: 100
links:
  deeper: [spring-troubleshooting-slow-first-requests-01]
---

## Ask

The same artefact, the same tag, the same container image. In staging one endpoint answers in
40ms; in production it takes four seconds, consistently, with no errors and no alerts firing.
You have the logs, the actuator endpoints and the ability to take a thread dump. You do not have
a debugger and you cannot deploy a change today. Talk me through the first thirty minutes.

## Tests

Whether the candidate narrows a problem by listing what differs between two environments and
then collecting evidence for each, rather than by guessing at causes and trying fixes.

## Ideal minimal answer

Start from what differs when the artefact is identical — data volume, settings, neighbours,
traffic — and take the cheapest checks first: the settings the running process resolved, then
split the four seconds into time in the database, time waiting for a connection and time
downstream. Pending connection acquisitions separate a starved pool from a slow query. Say what
would falsify each guess.

## Listen for

- Starts from what is different when the artefact is identical: the data, the settings, the
  neighbours, the hardware, the traffic
- Asks whether it is all requests or a subset, and whether it was ever fast there
- Splits the four seconds before proposing anything: time in the database, time waiting for a
  connection, time in a downstream call, time waiting for a thread
- Names concrete evidence for each split rather than a general intention to look at metrics
- Checks what settings the running process actually resolved, and what the framework decided to
  switch on, rather than reading the repository
- States a hypothesis and what observation would kill it

## Expected knowledge

- That the actuator exposes resolved settings, conditions, health and metrics
- That a thread dump tells you where threads are waiting, and that one dump is a sample
- That different data volume alone can change a query plan

## Strong signals

- Asks whether staging has a hundredth of the rows, and treats the plan as data-dependent
- Distinguishes waiting for a connection from waiting for the database, and says which number
  separates them
- Takes several dumps rather than one, and says why
- Says what they would leave behind so the next occurrence does not need thirty minutes

## Weak signals

- Starts changing settings to see what helps
- Blames garbage collection or the network with no measurement
- Asks for a profiler on production as the first step and stops when told no
- Cannot say what they would look at first, only what might be wrong
- Tells the story of a slow query they once found at another company, without saying what they
  would check here

## Answer bands

### weak

- Lists possible causes with no way of telling which one is true.
- Proposes changing something to see if it helps.

### mid

- Enumerates real differences between the two places rather than guessing at causes.
- Checks the resolved settings on the running process.
- Splits the latency into database, downstream and waiting, and knows roughly where to look.

### senior

- Orders the checks by how cheap they are and how much they would rule out.
- Names the specific number that separates waiting for a connection from a slow query.
- Treats the data volume difference as a first-class hypothesis before the row counts are put in
  front of them, not as an afterthought.
- Says what each observation would prove and what would falsify it.

### lead

- Says what should have been in place so this was answered from a dashboard, and makes that
  the outcome of the incident.
- Decides how long to keep investigating before mitigating, and what mitigation is available
  without a deploy.

## Follow-ups

- The dump shows almost everything idle and the endpoint still slow. What does that rule out?
  probes: whether they can reason from an absence of evidence, not only a presence
- Staging has 200 rows in that table and production has 40 million. Does that change your first
  check?
  probes: data volume as a first-class difference rather than an excuse
- You are told the platform team changed nothing. Do you believe it, and how would you check?
  probes: verifying against the running process rather than against what people remember
- After you find it, what do you leave behind?
  probes: turning a thirty-minute investigation into a dashboard panel or an alert

## Sources

- https://docs.spring.io/spring-boot/reference/actuator/endpoints.html
- https://docs.spring.io/spring-boot/reference/actuator/metrics.html

## Notes

Useful concrete answers: `/actuator/env` for what was resolved, `/actuator/conditions` for what
the framework switched on, `http.server.requests` percentiles for where the time is,
`hikaricp.connections.pending` and `hikaricp.connections.acquire` for connection starvation
versus slow queries. Grade the method, not the list — a candidate who reaches the same places by
reasoning is stronger than one who recites endpoint names.
