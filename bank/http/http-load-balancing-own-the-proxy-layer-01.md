---
id: http-load-balancing-own-the-proxy-layer-01
schema_version: 2
title: Signing off a proxy tier in front of everything
category: http
topic: load-balancing
level: lead
tags: [operations, failure-modes, observability, scalability]
time_estimate_min: 12
order: 115
links:
  related: [microservices-observability-dashboards-green-users-angry-01]
---

## Ask

The platform team wants to put its own proxy tier in front of every internal service — timeouts,
retries, per-route limits, mutual authentication, traffic shifting — replacing what each team
does in its own client today. You have to approve it or turn it down. What do you want settled
before you decide?

## Tests

Whether the candidate can price a shared component on the critical path of every request — in
blast radius, in who carries it, and against the alternative — rather than judging it on the
feature list.

## Ideal minimal answer

It sits on every request in the estate, so settle who is paged for it, how one configuration
change is rolled out and reversed, and what happens everywhere when that change is wrong. Fix
the timeout and retry policy in one place so the tier and the clients do not multiply each
other. Then say what this buys that a shared library could not.

## Listen for

- Names it as a dependency of every request: its own bad minute is everyone's bad minute, and one
  configuration change has estate-wide reach
- Asks who carries the pager for it, and what happens at 03:00 when a team's service is fine and
  the tier is not
- Retries in the tier multiply with retries already in the clients; wants one budget, set once,
  and the other side switched off deliberately
- Timeouts have to nest: whoever gives up first decides what the caller sees, and a tier timeout
  longer than the caller's is worse than none
- Asks how a change ships — per route, canaried, and how quickly it can be taken back
- Weighs it against the alternative rather than against nothing: a shared client library trades
  blast radius for having to redeploy every service to fix anything
- Notices the tier becomes where latency and error rates are measured, and that its numbers will
  disagree with each team's — and decides in advance which is authoritative

## Expected knowledge

- A proxy that parses requests can act per route; one that does not can only act per connection
- Anything on every request path is also a capacity and a cost line

## Strong signals

- Asks what problem this is solving today, and for evidence it is the biggest one
- Wants the tier to be able to get out of the way — a bypass, or a mode where it forwards and
  decides nothing
- Asks about the upgrade path: how a version rolls across the estate and what happens when one
  team cannot take it
- Names the migration as the hard part, not the steady state, and wants the first service on it
  to be one whose failure nobody notices
- Separates what should be centrally enforced from what a team should still be free to set, and
  says who arbitrates

## Weak signals

- Judges it on the feature list
- Approves it because the pattern is common
- Refuses it on principle without naming what teams get wrong today
- Treats the tier as free because somebody else operates it
- Sets out the case for the tier and the case against it and never says whether they would
  approve it

## Answer bands

### mid

- Lists the capabilities and says it would reduce duplicated code.
- Raises that the tier must be highly available.

### senior

- Names the blast radius of a configuration change and asks how it is rolled back.
- Raises the interaction between the tier's retries and the clients' own.
- Asks who is paged and how a caller-versus-tier argument gets settled at 03:00.

### lead

- Decides, and states the conditions the approval is contingent on.
- Compares it against a shared library on who bears the upgrade cost and who bears the outage.
- Plans the migration and names the first service and the way back.
- Says which numbers become authoritative and what stops teams measuring two different things.

## Follow-ups

- A team asks that requests from one user keep landing on the same instance. Do you allow it, and
  what do you want in return?
  probes: affinity as a judgement call — what it buys, what it costs at deploy and under
  autoscaling, and whether they set an expiry and a fallback instead of quoting a rule
- Both the tier and the calling services try again on failure. One backend gets slow. Count the
  requests that arrive at it.
  probes: multiplication, and whether they set one budget rather than two policies
- A one-line change to a shared configuration file goes out at 14:00 and the estate starts
  failing. Describe the next ten minutes.
  probes: detection, who reverts, how fast, and whether anyone can revert without the platform
  team
- A team says they can do all of this in their own client and want to opt out. What do you tell
  them?
  probes: weighing per-team freedom against a fleet-wide upgrade problem, and who decides

## Sources

- https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/http/http_routing
- https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/router_filter#config-http-filters-router-x-envoy-retry-on
- https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/circuit_breaking
- https://github.com/grpc/proposal/blob/master/A6-client-retries.md
- https://sre.google/sre-book/handling-overload/

## Notes

Figures to release if asked: about 120 services, six teams, roughly 40,000 requests a second at
peak; today each team sets its own timeouts in a client library that is four major versions
behind in a third of the estate; the platform team is four people and does not currently carry a
pager.

There is no correct verdict here. Approve and refuse are both defensible; what separates the
bands is whether the conditions attached are the ones that matter. Push hardest on rollback and
on who is paged, because those are the two that teams discover the expensive way.

The affinity follow-up is deliberately open. Pinning a user to an instance buys a warm local
cache and continuity for anything held in memory; it costs even load, it loses whatever was held
when that instance goes, and it weakens autoscaling because new instances only take new users.
Both "yes, with an expiry and a fallback" and "no, put the state somewhere shared" are good
answers. An answer that quotes it as a rule in either direction is not.
