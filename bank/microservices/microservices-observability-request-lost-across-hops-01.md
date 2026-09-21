---
id: microservices-observability-request-lost-across-hops-01
schema_version: 2
title: Find one failed order across four services
category: microservices
topic: observability
level: junior
tags: [observability, operations, failure-modes]
time_estimate_min: 6
order: 60
links:
  related: [sap-jco-troubleshooting-3am-failure-triage-01]
  deeper: [microservices-observability-trace-not-kept-01]
---

## Ask

A customer says their order failed yesterday at 14:32. The request went through the gateway, then
checkout, then pricing, then payment. All four write logs. How do you find out what happened to
that one order?

## Tests

Whether the candidate knows a request has to carry something that ties its log lines together,
and can say what to do when it does not.

## Ideal minimal answer

Start from the order number to find the one request, then search all four services for a single
value minted at the gateway and passed on by every hop, which each service writes into its log
lines. Matching on 14:32 across four machines is guesswork, because their clocks do not agree.

## Listen for

- Wants one value, minted at the edge and passed on every hop, that appears in all four sets of
  logs
- Says that value has to be written into the log lines, not just sat in a header
- If nothing like that exists today, says so plainly instead of describing a search by clock time
- The logs need to be searchable in one place, not four separate machines
- Gets from what the customer gave them — an email, an order number — to something technical they
  can search on

## Expected knowledge

- A header added by the caller is available to every hop that bothers to forward it
- Clocks on different machines disagree, so matching by time is guesswork

## Strong signals

- Asks whether the id survives a hop that goes through a queue rather than a direct call
- Notices that the absence of a log line is itself information, and is careful about what it means

## Weak signals

- Matches on timestamps across four services and treats the result as certain
- "I would look in the logs" with no answer to what they would search for
- Assumes every service logs every request

## Answer bands

### weak

- Proposes eyeballing each service's logs around 14:32 and hoping.
- Has no way to link a line in one service to a line in another.
- Suggests reproducing it in a test environment as the first move.

### junior

- Names a value carried along the request and searched for everywhere.
- Knows where it would come from and that every hop has to pass it on.
- Can get from the customer's order number to something searchable.

### mid

- Says what to do when the chain is incomplete: log at your own edge what you sent and received.
- Treats a missing line as ambiguous and says what would resolve it.
- Wants the four log sets in one searchable place and can justify the cost.

## Follow-ups

- Payment has nothing at all for that request. Does that mean it never arrived?
  probes: absence of evidence; sampling, log level, dropped or rate-limited logging
- Three of the four have it and the fourth is a third party you cannot change. What now?
  probes: recording the exchange at your own boundary; mapping their reference to yours
- The customer gives you their email address and nothing else.
  probes: getting from a business fact to a technical handle

## Sources

- https://www.w3.org/TR/trace-context/
