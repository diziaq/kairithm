---
id: microservices-scalability-one-tenant-dominates-01
schema_version: 2
title: One customer's monthly job starves nine hundred others
category: microservices
topic: scalability
level: lead
tags: [performance, operations, failure-modes, ownership]
time_estimate_min: 10
order: 220
---

## Ask

One customer is forty per cent of your traffic. On the first of every month they fire a bulk job
that saturates your service, and your other nine hundred customers get timeouts for two hours.
What do you do?

## Tests

Whether the candidate treats fairness between tenants as a design property to be enforced, and
can weigh isolation against the cost of running it.

## Ideal minimal answer

One tenant's bulk job lands in the same capacity as everyone else's, so per-tenant limits and a
separate lane for bulk work are the mechanism; what each class of customer is entitled to is a
commercial decision made with whoever owns the account. Price a dedicated stack in on-call terms
before offering it, and answer the case where nine hundred small tenants all do this at once.

## Listen for

- The problem is one tenant's work landing in the same capacity as everyone else's; more capacity
  alone just raises the level at which it happens again
- A per-tenant limit, and a clear statement of what the service does when one is exceeded — a
  slower lane, a queue, or a refusal the client can act on
- Separates bulk work from interactive work so a batch cannot starve a page load
- Considers giving the large tenant their own capacity, and prices what that costs to run and to
  operate
- Goes and talks to the customer: a scheduled window, an endpoint designed for bulk, a paid tier
- Notices that with forty per cent of traffic this customer is also most of the revenue, so the
  answer is not purely technical

## Expected knowledge

- Shared capacity with no per-tenant bound means the loudest tenant sets everyone's experience
- Rejecting work is a legitimate response when the alternative is failing everybody

## Strong signals

- Distinguishes the limit that protects the service from the limit that defines what the customer
  bought
- Asks what the bulk job is actually for, because there may be an offline answer that removes the
  traffic entirely
- Thinks about the aggregate case, not only the one big tenant

## Weak signals

- Scales up for the first of the month and calls it solved
- Rate-limits everyone equally and does not notice the large tenant still wins
- Proposes throttling the customer without anyone speaking to them

## Answer bands

### mid

- Identifies the need for a per-tenant cap.
- Suggests more capacity for the peak and can say roughly how much.
- Does not separate bulk traffic from interactive traffic.

### senior

- Puts bulk work on a different path with its own capacity and its own limits.
- Says precisely what a client sees when it exceeds its allowance, and what it should do then.
- Weighs dedicated capacity for the big tenant against the cost of running two of everything.

### lead

- Treats the allowance as a commercial decision and involves the people who own the relationship.
- Sets what each class of customer is entitled to and makes that visible rather than emergent.
- Accounts for the operational cost of whatever isolation they choose, in on-call terms.
- Handles the aggregate version of the problem, not only this one customer.

## Follow-ups

- They are sixty per cent of revenue as well as forty per cent of traffic. Does your answer change?
  probes: whether fairness is treated as a business decision rather than a purely technical one
- You give them a stack of their own to run on. What have you just signed the night rota up for?
  probes: the running cost of per-tenant deployments and configuration drift
- Nine hundred small customers all run the same nightly script at midnight. Same problem?
  probes: whether they see the aggregate pattern and not only the large tenant

## Sources

- https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/
