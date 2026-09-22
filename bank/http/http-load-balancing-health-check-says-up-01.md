---
id: http-load-balancing-health-check-says-up-01
schema_version: 2
title: Eight instances, all healthy, every request failing
category: http
topic: load-balancing
level: junior
tags: [failure-modes, operations, observability]
time_estimate_min: 6
order: 100
links:
  deeper: [http-load-balancing-deploy-drops-in-flight-01]
---

## Ask

Eight instances sit behind a load balancer. Overnight the database password was rotated and none
of them can open a connection, so every request comes back as a 500. All eight still pass their
health check and the balancer keeps sending traffic to all eight. The check is a handler that
returns 200. Why did nothing get taken out?

## Tests

Whether the candidate can say what a health check actually asserts, and choose what belongs
inside one rather than treating its presence as the safeguard.

## Ideal minimal answer

The check returns 200 without touching the database, so it proves the process is listening and
can answer, not that it can serve a request. It has to exercise something the request path
actually depends on — at minimum, getting a connection from the pool — before the balancer has
anything to act on.

## Listen for

- The check only proves the process is up and the web layer answers; the broken thing is never
  touched by it
- A balancer removes an instance on the signal it is given and has no other way to find out
- Make the check exercise what a real request needs, starting with the store the handler uses
- Notices that if all eight fail at once there is nothing left to send traffic to, and asks what
  should happen then
- A check that calls every downstream in turn converts one slow neighbour into a total outage
- Separates "stop sending me traffic" from "this process is stuck, restart it" — two different
  questions with two different answers

## Expected knowledge

- A balancer polls each instance on an interval and needs some number of failures before acting
- Returning 200 is the cheapest possible thing a web framework can do

## Strong signals

- Asks for the interval and how many consecutive failures cause removal, and works out how long
  the fleet served errors before anyone could have noticed
- Points out that with every instance failing, some balancers deliberately ignore health rather
  than serve nothing at all
- Wants the condition in a metric and an alert, not only in the balancer's view of the pool
- Asks who is allowed to make the check fail, because anyone who adds a line to it can take the
  fleet down

## Weak signals

- Answers "add a health check" when there already is one
- Proposes the check call every service the instance talks to, with no thought about shared
  failure
- Believes a failing check restarts the instance
- Blames the balancer's configuration without saying what it was told
- Recounts a past outage where the check kept saying up and never says what this one should
  cover

## Answer bands

### weak

- Says the check "must be broken" without saying what it does or does not cover.
- Suggests restarting the instances and stops there.
- Cannot say what the balancer knows about an instance.

### junior

- Says the check answers without touching the database, so it cannot detect this.
- Proposes the check do something the real request path does, and names the database.
- Says the balancer only acts on what the check tells it.

### mid

- Raises it themselves that all eight would fail together, and asks what the balancer should do
  with an empty pool.
- Draws a line around what the check should cover: what this instance owns, not everything it
  calls.
- Wants the failure surfaced as an alert as well, because a healthy-looking pool serving errors
  is invisible otherwise.

## Follow-ups

- Someone changes the check so it calls every service the instance talks to. One of those has a
  bad ten seconds. What happens across the fleet?
  probes: correlated removal, and whether they separate what the instance owns from what it calls
- All eight fail the check at the same moment. What do you want the thing in front of them to do?
  probes: nowhere left to send traffic; that some balancers ignore health below a threshold
- The instance is answering fine, but a background worker inside it died an hour ago. Should it
  keep getting traffic?
  probes: whether the check is a claim about serving requests, and what else needs its own signal

## Sources

- https://nginx.org/en/docs/http/ngx_http_upstream_module.html#max_fails
- https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/health_checking
- https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/panic_threshold
- https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/

## Notes

Figures to release if asked: eight instances, the check is `GET /health` returning a literal 200,
polled every five seconds, three consecutive failures to remove; the password rotated at 02:00
and the first customer complaint arrived at 07:40.

Two facts worth holding a candidate to. Open-source nginx has no active health checking at all —
it infers a server is down from failed real requests (`max_fails` within `fail_timeout`, default
one failure in ten seconds); active `health_check` is a commercial feature. And Envoy's panic
threshold defaults to 50%: when fewer than half the hosts in a cluster are healthy it disregards
health status and balances across all of them, on the grounds that half a broken fleet beats
nothing. Either behaviour is a reasonable thing for a candidate to discover out loud; neither is
required to pass.
