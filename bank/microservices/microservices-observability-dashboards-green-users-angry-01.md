---
id: microservices-observability-dashboards-green-users-angry-01
schema_version: 1
title: Every dashboard is green and checkout is broken
category: microservices
topic: observability
level: lead
tags: [observability, operations, performance, correctness]
time_estimate_min: 10
order: 70
links:
  related: [microservices-scalability-one-tenant-dominates-01]
---

## Ask

Every dashboard is green: CPU at 30%, error rate 0.2%, average response time 40ms. The support
queue has been filling up all morning with people saying checkout is broken. What is your
monitoring not telling you, and what do you change?

## Tests

Whether the candidate can distinguish measuring the machinery from measuring what the user is
trying to do, and can turn that into what a team would actually build.

## Listen for

- An average hides the tail; a small fraction of very slow requests is invisible next to a healthy
  middle
- 0.2% is not evenly spread: it can be one endpoint, one region, one tenant, one card type, and
  the aggregate is the wrong unit
- Every component being up does not mean the end-to-end journey works, and nothing here measures
  the journey
- Wants a signal on the outcome — completed orders against what this hour normally looks like
- Treats the support queue arriving first as the failure: the monitoring should have beaten it
- Asks what changed this morning before redesigning anything

## Expected knowledge

- Aggregates over all traffic conceal a minority that is entirely broken
- A slice by tenant, endpoint or region costs storage and query time, so it is a choice

## Strong signals

- Separates the incident response from the durable change and does both
- Names who gets woken and for what, so a new signal does not become noise
- Knows that some journeys fail without producing any error at all on any service

## Weak signals

- Adds more dashboards
- Blames the users or the support team's description
- Alerts on every metric they can think of

## Answer bands

### mid

- Points at the average and asks to see the distribution instead.
- Wants the failing requests sliced to find what they share.
- Suggests a check that exercises the whole flow rather than one service.

### senior

- Frames the gap as component health versus journey health and gives a concrete signal for the
  second.
- Uses the 0.2% as a lead and describes how they would find what those requests have in common.
- Notices that a request can succeed on every hop and still not do what the user wanted.
- Handles today's incident and the measurement gap as two separate pieces of work.

### lead

- Decides what the team will be woken for and what it will not, and says what happens to the rest.
- Accepts an explicit cost — cardinality, retention, sampling — to get the slices that matter.
- Defines the small number of signals the business would recognise, and who owns each one.
- Says how the team finds out that a new signal has itself gone stale or stopped reporting.

## Follow-ups

- Someone proposes alerting on the slowest one in a hundred requests, everywhere, on everything.
  What does your week on the pager look like?
  probes: alert volume versus actionability; symptom-based alerting on user journeys
- The failing fraction turns out to be one large customer. Does that change what you build?
  probes: per-tenant slicing, cardinality cost, who the signal is for
- How would you have known before a single ticket was filed?
  probes: business-level signals compared against an expected curve
- Six months on, the new signal has been green through two real incidents. What do you do?
  probes: whether they verify that a signal still detects anything

## Sources

- https://sre.google/sre-book/service-level-objectives/
