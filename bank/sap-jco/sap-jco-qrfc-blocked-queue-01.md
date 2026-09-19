---
id: sap-jco-qrfc-blocked-queue-01
schema_version: 1
title: One bad delivery blocks seven hours of postings
category: sap-jco
topic: trfc-qrfc
level: lead
tags: [ordering, failure-modes, operations, delivery-semantics]
time_estimate_min: 10
order: 190
---

## Ask

Deliveries flow into SAP through an inbound queue so they stay in order. One document fails at
two in the morning, and by nine nothing has posted for seven hours because everything behind it
is stuck. The business wants this never to happen again. What do you propose?

## Tests

Whether the candidate understands ordered delivery as a deliberate trade with a known failure
mode, and can redesign around the real ordering requirement instead of removing ordering or
adding people.

## Listen for

- That is the queue doing its job: it is a single file, so one entry that cannot be processed
  blocks everything behind it
- The first question is what ordering actually has to hold — almost always per document or per
  customer, not across the whole flow
- So the design answer is the queue name: encode the real key in it, turning one global line
  into many independent ones that fail separately
- Somebody has to be watching: an alert when a queue goes into error or when its age crosses a
  threshold, at two in the morning, not a person noticing at nine
- The blocking entry needs a decision path — fix and retry, or skip — with an owner and a record
  of who decided
- Entries are retried and may have partly executed, so the receiving logic must tolerate a
  repeat
- Finer queues mean weaker ordering: say which pairs of documents may now cross and get that
  accepted

## Expected knowledge

- Inbound and outbound queues are monitored separately on the SAP side
- The newer background communication framework is the successor to this mechanism

## Strong signals

- Gets the ordering key from the business rather than assuming one
- Sizes the number of parallel queues against the work processes that will drain them, instead
  of creating thousands
- Says what the seven-hour outage actually cost, and lets that set the investment
- Treats "never again" as two separate promises: not blocking globally, and not going unnoticed

## Weak signals

- Removes ordering entirely without checking what depended on it
- Proposes a person checking the monitor every morning as the control
- Suggests deleting the stuck entry as standard practice

## Answer bands

### mid

- Explains why everything behind the failed entry stopped.
- Suggests someone should be alerted and the entry fixed or removed.

### senior

- Splits the flow by a key so failures are contained, and can say which key.
- Puts monitoring on error state and on age, with an owner and an escalation.
- Handles the repeat-execution risk on the receiving side.

### lead

- Establishes the true ordering requirement with the business before changing anything, and
  states what is given up.
- Balances queue granularity against the capacity that drains the queues.
- Defines who may skip an entry, on what evidence, and where that is recorded.
- Prices the change against the cost of the outage rather than proposing everything possible.

## Follow-ups

- Somebody suggests just dropping the entry that failed and carrying on. When is that the right
  call and who makes it?
  probes: whether skipping is a governed decision or an operator reflex
- You split the flow by customer and a big customer now produces a queue of its own that blocks
  anyway. What then?
  probes: skew, and whether granularity alone is the answer
- Explain to the warehouse manager what they lose by having the documents processed in parallel.
  probes: whether they can express the ordering trade in the business's language
- What would have made the difference between a seven-hour outage and a twenty-minute one?
  probes: detection time as the real variable

## Notes

Inbound queues are monitored in `SMQ2` and outbound in `SMQ1`; the stuck entry sits at the head
with an error status. Do not turn this into a transaction-code question — the design answer is
the queue key and the detection time.

NEEDS-REVIEW — unverified claim about migrating an existing flow to the newer background
communication framework: availability and effort depend on the release and on the ABAP side, so
treat "it is a project, not a switch" as the safe position.
