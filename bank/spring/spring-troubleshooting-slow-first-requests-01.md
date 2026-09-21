---
id: spring-troubleshooting-slow-first-requests-01
schema_version: 2
title: Ninety bad seconds after every deploy
category: spring
topic: troubleshooting
level: lead
tags: [operations, observability, failure-modes, configuration]
time_estimate_min: 11
order: 101
links:
  related: [spring-bean-lifecycle-graceful-shutdown-01]
---

## Ask

Every rolling deploy, roughly a third of requests fail or time out for about ninety seconds,
then the service is perfect until the next deploy. The pods report healthy the whole time and
the platform team says the rollout is textbook. Product has started scheduling releases for
3 a.m., which is the actual reason this landed on your desk. What is going on, and what do you
change?

## Tests

Whether the candidate can reason about the window between a process starting and a process
being genuinely able to serve, distinguish the two signals the platform consumes, and treat
"deploy at night" as a symptom rather than a mitigation.

## Ideal minimal answer

The pod reports that it is alive and traffic is routed on the strength of that, while whether it
can serve — pools not filled, caches empty, code not yet optimised — is a separate signal. Route
on that second one, warm the hot path before declaring it able to serve, make the rollout and
application settings agree, refuse the 3 a.m. workaround, and leave a per-deploy measurement.

## Listen for

- The pod is reporting that it is alive, and traffic is being sent on the strength of that; the
  question of whether it is ready to serve is a different signal
- Names what is still not finished after the process starts: pools not filled, connections not
  opened, code not yet optimised by the runtime, caches empty
- Knows the framework distinguishes being alive from being able to take traffic, and that the
  platform must be pointed at the second one for routing
- Considers that the old pods may be cut off before they finish their in-flight work, so some
  of the failures are on the way out rather than on the way in
- Asks whether anything defers work until the first request, because that moves the cost into
  the first caller
- Says what would prove which of these it is, rather than changing all of them

## Expected knowledge

- The two distinct signals a platform asks a process for, and what each one causes it to do
- That connection pools and the runtime both warm up over the first requests
- Draining in-flight work before a process exits

## Strong signals

- Splits the failures by direction before proposing anything: are they on the new pod or the
  old one
- Points out that scheduling at 3 a.m. hides the defect from the business and from the metrics,
  and argues to reverse that decision once fixed
- Names a warm-up that runs before the process declares itself able to serve, and says what it
  must exercise
- Ties the rollout's surge and grace settings to the application's own settings, and says what
  happens when the two disagree
- Asks what the error budget says, and whether a smaller step size buys more than a code change

## Weak signals

- Increases the readiness delay to a fixed number of seconds and calls it fixed
- Blames the runtime warming up and proposes nothing measurable
- Accepts night deploys as the answer
- Cannot distinguish the signal that restarts a pod from the signal that routes traffic to it

## Answer bands

### mid

- Knows the pod takes traffic before it is genuinely able to serve.
- Names at least one thing still warming up after startup.

### senior

- Separates the two signals the platform consumes and says which one governs routing.
- Attributes part of the failures to the pods being removed, not only to the ones arriving.
- Fills the pool and exercises the hot path before declaring the process able to serve.
- Says which measurement would tell them which cause dominates.

### lead

- Refuses the 3 a.m. workaround and says what it costs the organisation to hide this.
- Makes the rollout settings and the application's own settings consistent, and names the
  failure when they are not.
- Defines what "ready" means for this service as a decision, not a timeout.
- Leaves a per-deploy measurement so the next regression is visible on the release, not in a
  support ticket.

## Follow-ups

- Half the failures turn out to be on the pods going away, not the ones arriving. Does that
  change your fix?
  probes: whether they were treating the deploy as one-directional
- Someone proposes a fixed delay before the pod takes traffic. What is wrong with a number?
  probes: a timeout standing in for a real signal; what happens on a slower day
- The service defers most of its setup until it is first needed, to start faster. Good trade?
  probes: moving cost onto the first caller; who pays for a fast start
- What would you put on the release dashboard so nobody has to deploy at night again?
  probes: per-deploy error rate as the artefact of the fix

## Sources

- https://docs.spring.io/spring-boot/reference/actuator/endpoints.html#actuator.endpoints.kubernetes-probes
- https://docs.spring.io/spring-boot/reference/features/spring-application.html#features.spring-application.application-availability

## Notes

Boot exposes liveness and readiness groups on the health endpoint, enabled automatically when it
detects Kubernetes or via `management.endpoint.health.probes.enabled`; readiness moves to
accepting traffic after `ApplicationReadyEvent`, and `AvailabilityChangeEvent` lets the
application push itself out of rotation. Hikari's `minimum-idle` defaults to the maximum pool
size, but connections are opened on demand rather than up front, so the pool is nowhere near full
at the moment the process reports itself started. `spring.main.lazy-initialization=true` is the setting
behind the last follow-up.
