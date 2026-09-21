---
id: microservices-observability-dashboards-green-users-angry-01
schema_version: 2
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
queue has been filling up all morning with people saying checkout is broken. Your observability
bill has doubled this year and the platform team have said no to any new dimension unless
something else comes out. What is your monitoring not telling you, what do you add, and what do
you take away to pay for it?

## Tests

Whether the candidate can distinguish measuring the machinery from measuring what the user is
trying to do, and then buy the second inside a fixed budget rather than asking for more of
everything.

## Ideal minimal answer

The average hides a slow tail and 0.2% is not spread evenly, so nothing here measures whether
checkout completed. I would add completed orders against what this hour normally looks like, and
one slice by tenant, paid for by switching off dashboards nobody has opened in a year; each
signal gets an owner, a rule for who is woken, and a date to check it still fires.

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
- Every new slice has a price, so it has to be chosen: which dimension earns its keep, and which
  existing metric or dashboard nobody has looked at in a year pays for it

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
- Asks for the new signals without saying what is given up to pay for them.

### senior

- Frames the gap as component health against journey health, and names one concrete signal for the
  second — completed checkouts against what this hour normally looks like.
- Uses the 0.2% as a lead and describes how they would find what those requests have in common.
- Notices that a request can succeed on every hop and still not do what the user wanted.
- Handles today's incident and the measurement gap as two separate pieces of work.
- Names one dimension worth its cost and one that is not.

### lead

- Decides what the team will be woken for and what it will not, and says what happens to the rest.
- Makes the trade explicit: names what is switched off, sampled or shortened to fund the slices
  that matter, and who has to agree to that.
- Defines the small number of signals the business would recognise, and who owns each one.
- Says how the team finds out that a new signal has itself gone stale or stopped reporting.
- Accounts for what the new signals cost the on-call rota, not only the bill.

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
