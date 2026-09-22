---
id: spring-web-layer-thread-exhaustion-01
schema_version: 2
title: Two hundred threads, eight percent CPU
category: spring
topic: web-layer
level: senior
tags: [performance, failure-modes, operations, observability]
time_estimate_min: 10
order: 72
links:
  deeper: [spring-web-layer-long-running-request-01]
  related: [spring-troubleshooting-slow-in-production-01]
---

## Ask

A Boot 3 service that normally answers in 40ms starts taking twenty seconds for everything,
including its own health endpoint. CPU sits at eight percent, memory is flat, and a thread dump
shows almost every request-handling thread parked in a socket read against one downstream
service. Someone has already doubled the thread pool and it made no difference. What is
happening, and what do you do?

## Tests

Whether the candidate can reason about this one application's thread-per-request server as a
finite resource shared by every endpoint it serves, sees that a slow dependency converts directly
into occupied threads, and fixes it with bounds it can set in its own configuration rather than
with capacity.

## Ideal minimal answer

Each request in flight owns a thread for its whole duration, so the arrival rate times the
downstream latency has passed the two hundred threads; doubling the pool only doubles the time
to exhaustion. Every endpoint shares that pool, which is why a health check that calls nothing
queues behind. Set a read timeout, cap concurrent calls to that dependency, and fail fast past
the cap.

## Listen for

- Each in-flight request owns a thread for its whole duration, so a slow dependency converts
  directly into occupied threads
- Once every thread is occupied, requests that touch nothing at all queue behind them — which
  is why the health endpoint is affected
- Doubling the pool doubles the time to exhaustion and nothing else, because the arrival rate
  has not changed
- The first question is what timeout that downstream call has, and the common answer is none
- Bounds the damage: timeouts, a cap on concurrent calls to that dependency, and a fast failure
  once the cap is hit
- Says what the caller should get when the bound is hit, rather than waiting

## Expected knowledge

- How a request maps onto a thread in the servlet model
- That a client built with defaults may well have no read timeout at all
- That a queue in front of a saturated pool makes latency worse, not better

## Strong signals

- Does the arithmetic out loud: arrival rate times latency gives occupied threads
- Separates the health endpoint onto its own listener, or explains why it must not share the
  pool
- Asks whether the downstream call is on the critical path for this endpoint at all
- Knows that moving to a non-blocking stack removes the thread cost but not the dependency, and
  says what actually changes

## Weak signals

- Adds threads, then adds more threads
- Blames garbage collection with the CPU at eight percent
- Proposes rewriting on a reactive stack as the first move
- Suggests retrying the slow call
- Describes a thread-pool outage from a previous job, and never says what they would do about
  this dependency

## Answer bands

### weak

- Reaches for more threads or more pods with no model of why.
- Cannot explain why the health endpoint is slow when it calls nothing.

### mid

- Explains that a thread is held for the whole request and the slow dependency occupies them.
- Knows adding threads only delays the same outcome.
- Asks about timeouts on the downstream call.

### senior

- Relates arrival rate, latency and pool size, and shows where saturation starts.
- Sets a timeout, caps concurrency against that dependency, and fails fast past the cap.
- Explains that the shared pool is what spread one dependency's problem to every endpoint.
- Says what the caller is told when the bound is hit and what is recorded.

### lead

- Decides, endpoint by endpoint, what this service does while that dependency is slow — answer
  without the enriched part, refuse quickly, or keep waiting — and says which the business wants
  for each.
- Weighs isolating the pool against a non-blocking rewrite on cost and on who maintains it.
- Names the alert that should have fired before the pages did.

## Follow-ups

- That downstream call is only needed to enrich the response. Does the request have to wait for
  it at all?
  probes: whether they question the critical path rather than tuning it
- Nobody configured the outbound client at all. How long will it wait?
  probes: whether they know the default is to wait forever
- Health checks share the same pool. What does the platform do when they time out, and is that
  what you want mid-incident?
  probes: restarting a pod that was merely waiting; isolation of the probe path
- What single number, on a dashboard, would have shown this starting an hour earlier?
  probes: saturation of the pool as a leading signal rather than latency as a lagging one

## Sources

- https://docs.spring.io/spring-boot/reference/web/servlet.html
- https://docs.spring.io/spring-framework/reference/integration/rest-clients.html

## Notes

Tomcat's default maximum number of request-handling threads is 200 (`server.tomcat.threads.max`).
A plain `RestTemplate` uses `SimpleClientHttpRequestFactory`, which applies no connect or read
timeout unless one is configured, so the call can wait indefinitely. Spring Boot 3.4 added
`spring.http.client.*` properties for setting those centrally. The health endpoint being slow is
the detail that separates a candidate who has seen this from one who has read about it.
