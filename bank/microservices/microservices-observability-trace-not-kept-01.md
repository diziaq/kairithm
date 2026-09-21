---
id: microservices-observability-trace-not-kept-01
schema_version: 2
title: The one request you need is the one that was thrown away
category: microservices
topic: observability
level: senior
tags: [observability, operations, failure-modes, cost]
time_estimate_min: 8
order: 65
links:
  deeper: [microservices-observability-dashboards-green-users-angry-01]
  related: [microservices-scalability-one-tenant-dominates-01]
---

## Ask

A customer sends you the reference printed on the error page for a checkout that failed yesterday
at 14:32. Tracing is switched on in every service, and the platform team keeps one request in a
hundred, picked at the gateway. The reference is not there. What do you do for this customer, and
what do you change?

## Tests

Whether the candidate sees that the choice to keep a request's data is normally made before
anybody knows how that request ended, and can buy back the ones that went wrong without paying to
keep everything.

## Ideal minimal answer

One in a hundred was chosen at the gateway before anything was known about how the request
ended, and a fair sample was never going to contain one named order. Decide after the outcome is
known instead, keeping the errors and the slow ones, apply the same decision at every hop, and
for this customer fall back to what each service logged against that reference.

## Listen for

- The keep-or-drop choice was made at the front door, at the start, when nothing was yet known
  about how this request would end
- Wants the interesting ones kept whatever the rate says — anything that ended in an error,
  anything unusually slow — and says where in the pipeline that can be judged
- Says the same choice has to apply to every hop of one request, or what survives is a fragment
  that does not join up
- Keeping everything is a price, not a plan; asks what the volume and the bill actually are before
  proposing it
- A kept fraction is a fair picture of the population, which is exactly what it was never going to
  be for one named order
- Says what still exists for this customer: what each service logged at its own edge, searchable
  by the reference the customer has
- Wants a way to collect everything for one customer, one endpoint or one window without shipping
  a release
- Treats how long data is kept as a separate dial from how much of it is kept

## Expected knowledge

- The choice can be made when a request starts or after it has finished, and the two cost
  different things in storage and in machinery
- What was dropped cannot be got back, and the gap only becomes visible when somebody goes looking

## Strong signals

- Asks what the trace was going to be used for — where it failed, or how slow it was — before
  rebuilding anything
- Accepts that some requests will always be missing and says plainly what the fallback is
- Checks that whatever is kept can actually be found by the reference the customer was given
- Names who pays for the change and in what unit, rather than asking the platform team for more

## Weak signals

- Turns collection up to everything, everywhere, with nothing said about the cost
- Asks the customer to make it happen again
- Lines up timestamps across four services and treats the result as the request
- Treats it as the platform team's problem and stops there

## Answer bands

### weak

- Proposes collecting everything with no account of what it costs.
- Asks the customer to reproduce the failure.
- Concludes nothing can be done and closes the ticket.

### mid

- Says the request was discarded at the start, before anything was known about its outcome.
- Wants the failures kept even when a request like this one would normally be discarded.
- Falls back to what each service logged for that reference.

### senior

- Moves the choice to a point where the outcome of the request is already known, and says where
  that runs and what it has to hold on to in the meantime.
- Says the choice has to be consistent across every hop, or the parts that survive do not make a
  whole.
- Prices the options against each other instead of asserting one: a bigger fraction kept for a
  shorter time, failures kept longer than successes, everything kept for one customer on request.
- Points out that a fair fraction answers questions about traffic as a whole and was never going
  to answer a question about one order.
- Says what the fallback is when the request really is gone, and what has to be true of the logs
  for it to work.

## Follow-ups

- A month of this, and the reference the customer quotes is always in the logs and never in the
  traces. Is anything actually broken?
  probes: a gap in evidence versus a fault; what each store is for and what it costs
- The platform team agree to keep every failure and the bill barely moves. Why?
  probes: failures as a tiny share of traffic; where the spend actually sits
- One service in the middle of the chain applies its own rule about what to hang on to. What do
  you end up with?
  probes: inconsistent choices producing partial evidence that cannot be joined
- The same customer calls back about an order from this morning and you want everything they did.
  What do you switch on?
  probes: targeted collection for one subject without a release

## Sources

- https://www.w3.org/TR/trace-context/
- https://opentelemetry.io/docs/concepts/sampling/

## Notes

The lead card on this topic is about what the metrics do not tell you and what gets switched off
to pay for better ones. This card stays on the evidence for one request: why it is missing, what
is kept instead, and what the customer gets today.
