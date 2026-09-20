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

The mechanism in the scenario is qRFC: queued RFC, which adds serialisation on top of tRFC by
placing units in a named queue and processing that queue strictly in order. Inbound queues are
monitored in `SMQ2` and outbound in `SMQ1`; the stuck entry sits at the head with an error
status. Do not hand the candidate the term, and do not turn this into a transaction-code
question — the design answer is the queue key and the detection time.

The successor referred to in `## Expected knowledge` is bgRFC, which supersedes both tRFC and
qRFC and offers ordered and unordered units under one API. It is monitored in `SBGRFCMON` and
configured in `SBGRFCCONF`.

Verified: moving an existing qRFC flow to bgRFC is a development effort, not a switch. bgRFC has
its own API and data model on the ABAP side, so a flow built on `CALL FUNCTION ... IN BACKGROUND
TASK` with `TRFC_SET_QUEUE_NAME` has to be rewritten against it; some destination and queue-name
mapping can be configured in `SBGRFCCONF` without code changes, but that does not carry the
calling code across. A candidate who reaches for bgRFC as the answer should be asked who writes
that ABAP and when it ships — the outage in the scenario is tomorrow.

Verified in the decompiled JCo 3.1.14, and it sharpens that point rather than softening it: the
**Java** side of bgRFC needs no new library. JCo 3.1 already ships `JCoFunctionUnit`,
`JCoRequestUnit`, `JCoUnitIdentifier`, `JCoFunctionUnitState` and `JCoBackgroundUnitAttributes`,
`JCoDestination` declares `confirmFunctionUnit` and `getFunctionUnitState`, and
`com.sap.conn.jco.rt.StaticFunctionTemplates` carries built-in templates for `BGRFC_DEST_SHIP`,
`BGRFC_DEST_CONFIRM` and `BGRFC_CHECK_UNIT_STATE_SERVER`. So if a candidate says "the connector
does not support it", they are wrong; the cost is on the ABAP side and in the operating model,
which is exactly where the card wants the conversation.

Verified: a qRFC queue is processed strictly in order by the scheduler, which starts the next
unit only when the current one has finished, so a failed unit at the head blocks the whole queue.
Encoding a business key into the queue name is the documented, standard remedy, and on the Java
side it is genuinely cheap: the queue name is an argument to
`JCoFunction.execute(destination, tid, queueName)` — `com.sap.conn.jco.rt.AbapFunction` passes it
straight through, and `com.sap.conn.jco.rt.ClientConnection` turns the call into `RfcQueueInsert`
rather than the plain transactional insert. Choosing the queue per call is a code change of one
argument, not a configuration project. That is useful when a candidate assumes the split has to
be negotiated with Basis first — the negotiation is about the ordering guarantee and the number
of queues, not about the mechanism.

## Sources

- https://help.sap.com/doc/saphelp_snc70/7.0/en-US/76/e12041c877f623e10000000a155106/content.htm
- https://help.sap.com/docs/SAP_NETWEAVER_701/6da114706c4b1014bfedc1de475963c2/48927c2caa6b17cee10000000a421937.html
- https://help.sap.com/doc/saphelp_nw74/7.4.16/en-US/48/99b963ee2b73e7e10000000a42189b/content.htm
