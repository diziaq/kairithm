---
id: spring-bean-lifecycle-graceful-shutdown-01
schema_version: 2
title: A deploy that drops in-flight work
category: spring
topic: bean-lifecycle
level: mid
tags: [operations, failure-modes, consistency]
time_estimate_min: 8
order: 21
---

## Ask

Every deploy, support sees a handful of failed payments. The logs from the old pod show a worker
still pulling jobs off a queue, and then a stack trace saying the connection pool is closed. The
worker was started with `new Thread(...)` from a bean's startup callback. Take me through what
happens between the signal arriving and the process exiting, and how you would make this clean.

## Tests

Whether the candidate can reason about an ordered teardown of a running system rather than
"add a shutdown hook", and whether they notice that a thread the container did not start is not
part of that order at all.

## Ideal minimal answer

The container tears beans down in the reverse of the order it built them, so the pool is closed
while the hand-started thread is still pulling jobs. That thread sits outside the ordering
entirely: nothing tells it to stop and nothing waits for it. Put the worker under the container
so it is stopped before the pool, and turn on graceful shutdown, which is bounded by a timeout.

## Listen for

- The container tears beans down in the reverse of the order it built them, so a bean's
  collaborators are still usable while it is being destroyed
- The hand-rolled thread is invisible to that ordering, so nothing waits for it and nothing
  tells it to stop
- A bean's destroy callback, and that it is only called for beans the container owns
- Separating "stop accepting new work" from "finish what is in flight", and that the HTTP layer
  needs the same treatment as the worker
- There is a bounded wait, after which the process exits anyway, so the work must be safe to cut

## Expected knowledge

- Destroy callbacks and the reverse teardown order
- Graceful HTTP shutdown, and that it has a timeout
- That a container kill is a signal followed by a grace period and then a hard kill

## Strong signals

- Says the queue work must be safe to interrupt regardless, because the grace period can always
  run out or the process can be killed outright
- Mentions taking the pod out of the load balancer before the process starts closing anything,
  and that the two are not the same event
- Brings up ordered start-up and shutdown phases for components that must stop before others

## Weak signals

- Adds a sleep before exit
- Believes a daemon thread will be waited for
- Thinks catching the signal is enough, with no account of what is still holding work

## Answer bands

### weak

- Suggests waiting a while before exiting, or catching the signal and calling exit.
- Cannot say which parts of the system the container is responsible for stopping.

### junior

- Knows there is a destroy callback and that the container calls it.
- Says the worker should be told to stop, without saying who tells it or what waits for it.

### mid

- Explains the reverse teardown order and places the pool close on that timeline.
- Points out that a thread created by hand is outside that order entirely.
- Puts the worker under the container, or registers it so it is stopped before the pool.
- Turns on graceful HTTP shutdown and knows it is bounded by a timeout.

### senior

- Splits refusing new work from draining in-flight work, and orders the two.
- Designs the queue work so that being cut mid-flight is recoverable, rather than relying on a
  clean exit.
- Ties the grace period in the deployment to the timeout in the application, and says what
  happens when they disagree.

## Follow-ups

- The platform kills the pod six seconds after the signal, no matter what. Does your answer
  still hold?
  probes: whether the design survives being cut, or only works when the drain completes
- Two of your components must stop in a fixed order relative to each other. How do you express
  that?
  probes: ordered phases rather than luck or the wiring graph
- During the drain the pod is still in the load balancer for a second or two. What does a
  request that arrives then get?
  probes: readiness versus liveness, and the gap between the two events

## Sources

- https://docs.spring.io/spring-boot/reference/web/graceful-shutdown.html
- https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html

## Notes

`server.shutdown=graceful` plus `spring.lifecycle.timeout-per-shutdown-phase` (30s by default)
is the Boot answer for the HTTP side. `SmartLifecycle` phases are the answer for ordering among
components. A thread started with `new Thread` is owned by nobody; a `TaskExecutor` bean is
stopped by the container.
