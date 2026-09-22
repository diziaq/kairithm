---
id: http-rate-limiting-counter-per-instance-01
schema_version: 2
title: The limit that loosened when the traffic rose
category: http
topic: rate-limiting
level: senior
tags: [scalability, operations, correctness, failure-modes]
time_estimate_min: 10
order: 125
links:
  deeper: [http-rate-limiting-lifting-the-limit-01]
  related: [microservices-scalability-autoscaled-into-database-01]
---

## Ask

Your limit is 600 requests a minute per customer, counted in memory inside each instance.
Yesterday, during a spike, the autoscaler took you from twelve instances to thirty and one
customer pushed eighteen thousand requests a minute through without a single refusal. This
morning you are back to eight instances and that same customer is being refused. Explain both.

## Tests

Whether the candidate can see that an enforced limit is a property of the whole fleet, and price
the alternatives — a shared counter, a divided allowance — in latency, failure and cost.

## Ideal minimal answer

Each instance counts only what it sees, so what the customer actually meets is 600 times the
number of instances — and that number moves with the autoscaler, loosening exactly when the
service is under load. Either hold one count somewhere shared, or divide the allowance by the
current fleet size and accept the error that introduces.

## Listen for

- The effective limit is the per-instance number multiplied by the instance count, and the
  instance count is not a constant
- Says out loud that this is backwards: the protection weakens precisely when load is highest
- Traffic is not spread perfectly, so dividing the allowance by the instance count refuses some
  callers well before their real allowance
- A shared count puts a network call on the path of every request: names the added latency and
  the extra failure mode
- Decides what happens when that shared store is unreachable, and says who is hurt by each
  choice
- Offers the middle ground: each instance leases a block of allowance and only goes back for
  more occasionally, so the hot path rarely touches the store
- Notes where the limit is enforced matters — pushing it to a single edge tier means one counter
  and no fan-out at all

## Expected knowledge

- An in-memory count belongs to one process and dies with it
- A rolling deploy replaces every process, and every count with it

## Strong signals

- Asks what the limit is protecting — a downstream store, a partner's own quota, a bill — because
  that decides how exact it has to be
- Prices the shared store honestly: its request rate equals the API's request rate, so it becomes
  as hot as the thing it protects
- Points out a deploy resets all the counters mid-window, and asks whether anyone would notice
- Separates a limit used for fairness, where approximate is fine, from a contractual number a
  customer will check against their own logs
- Asks whether the two symptoms are even the same customer's problem, or whether the morning
  refusals are a different fault

## Weak signals

- "Put it in Redis" with no mention of the extra hop, its failure, or its cost
- Divides by the instance count and calls the result exact
- Treats the per-instance number as if it were the customer's limit
- Proposes pinning each customer to one instance without saying what that costs
- Sets out a shared count, a divided allowance and leased blocks with fair trade-offs and picks
  none of them

## Answer bands

### mid

- Works out that the enforced limit is the per-instance number times the instance count.
- Suggests moving the count somewhere shared.

### senior

- Explains why the limit loosens under load and calls that the real defect.
- Names the cost of a shared count — a round trip per request, and a new thing that can be down.
- Chooses what happens when the store cannot be reached before being asked, and says who pays for
  that choice.
- Raises uneven traffic as the reason a simple division is not equivalent.

### lead

- Decides between exactness and availability from what the limit is for, and states which.
- Proposes leasing allowance in blocks and says what accuracy that gives up.
- Says where the enforcement belongs across the estate, not only in this service.
- Names what he would measure to know the limit is doing what the contract says.

## Follow-ups

- The store holding the count stops answering at peak. What does the very next request do?
  probes: open or closed, and which side of the business absorbs that decision
- Every instance is restarted inside ninety seconds during a release. What does a customer
  sitting at the edge of their allowance see?
  probes: state lost on restart; windows reset in the middle
- Your busiest endpoint does eight thousand requests a second. What does that mean for whatever
  holds the count?
  probes: the counter becomes as hot as the API; batching, leasing, local aggregation
- Sales has promised a customer exactly 600, in writing, and they read their own logs. Is
  approximate still acceptable?
  probes: protection versus a contractual quota, and whether they change the answer

## Sources

- https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/other_features/global_rate_limiting
- https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/local_rate_limit_filter
- https://redis.io/docs/latest/commands/incr/
- https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-ratelimit-headers

## Notes

Figures to release if asked: twelve instances normally, thirty at yesterday's peak, eight this
morning; the customer sustains about 6,000 requests a minute all day; median response 12 ms; a
round trip to an in-region shared store is about 0.4 ms; a rolling deploy replaces the fleet in
about 90 seconds.

The arithmetic: thirty instances at 600 each is 18,000, which is why nothing was refused. Eight
instances at 600 each is 4,800, which is below the customer's 6,000, which is why they are
refused today. Nothing changed about the customer.

Envoy's documentation draws the same distinction the candidate needs: a local rate limit filter
applied per instance, against a global rate limit service consulted by all of them, recommended
where "a large number of hosts are forwarding to a small number of hosts and the average request
latency is low". What its documentation does not settle — and what this card is really about —
is what your service does when the shared service cannot be reached. There is no right answer,
only a decision and a reason for it.
