---
id: microservices-service-boundaries-lockstep-deploys-01
schema_version: 2
title: Two services that can only be deployed together
category: microservices
topic: service-boundaries
level: mid
tags: [api-design, failure-modes, performance, ownership]
time_estimate_min: 8
order: 190
links:
  related: [general-design-reasoning-split-out-notifications-01]
  deeper: [microservices-service-boundaries-shared-orders-table-01]
---

## Ask

Rendering one checkout page takes four calls from Checkout into Pricing, and every Pricing release
has to go out the same afternoon as a Checkout release or the page starts erroring. What does that
tell you about the boundary between those two, and what would you actually change?

## Tests

Whether the candidate can read coupling from deployment and call patterns, and propose a change
with its costs, rather than restating that the services are coupled.

## Ideal minimal answer

Two costs, separately: they have to ship together, so they are one unit paying for the split and
getting no independent release back; and four calls per page add four chances to be slow or
down. Ask what each call fetches, then offer options — one coarser call, Checkout holding what
it needs, or merging the two — and say what each makes worse.

## Listen for

- Having to release the two together means they are one unit pretending to be two: they are paying
  for the split and getting nothing back
- Four calls per page multiplies both latency and the chance of failing: each one is another thing
  that can be slow or down
- Asks what the four calls actually fetch, and whether Checkout needs all of Pricing or one
  computed answer
- Offers real options with trade-offs — one coarser call, Checkout holding the data it needs, or
  merging the two services
- Points at what changes together: things that change for the same reason and at the same time
  belong on the same side of a boundary
- Asks whether either service is called by anybody else, because that changes the answer entirely

## Expected knowledge

- Independent deployability is the main thing a service boundary buys
- A synchronous call adds the callee's availability to the caller's

## Strong signals

- Notices that the lockstep is itself a symptom and asks what breaks when they are out of step
- Talks about team boundaries alongside code boundaries
- Says what evidence would change their recommendation

## Weak signals

- Proposes caching as the answer with nothing about staleness
- Recommends merging with no cost stated
- Says the API should be versioned and stops
- Puts three options up with honest costs and never says which one they would take to the two
  teams

## Answer bands

### weak

- Reports that the services are coupled without saying what that costs.
- Suggests adding a cache to fix the four calls and stops there.
- Treats the lockstep releases as a scheduling problem.

### junior

- Connects the joint releases to the boundary being in the wrong place.
- Notes that four calls per page is a lot and would try to reduce them.
- Offers one option without weighing it against another.

### mid

- Names both costs — the release coupling and the per-page call count — and keeps them separate.
- Asks what data each call is for and proposes a boundary based on what changes together.
- Puts two or three options on the table and says what each one makes worse.

### senior

- Argues from the change history: what has been released together and why.
- Recommends merging the two without waiting to be pushed, and makes the case in cost terms.
- Considers other callers, team ownership and the migration path, not just the end picture.

## Follow-ups

- Your fix is a single call that returns everything the page needs. What did you just make harder?
  probes: coupling moved rather than removed; payload growth, reuse by other callers
- Someone suggests Checkout keeps its own copy of the price list. What goes wrong now?
  probes: staleness on data that is money; who owns the number that the customer is charged
- Merging them means one team loses a service they own. How do you make that case?
  probes: whether they can argue from cost and evidence rather than taste
