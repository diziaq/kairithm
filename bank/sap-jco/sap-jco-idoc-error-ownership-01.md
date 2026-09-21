---
id: sap-jco-idoc-error-ownership-01
schema_version: 2
title: Forty failed documents a week and a customer finds them first
category: sap-jco
topic: idoc
level: lead
tags: [operations, observability, consistency, ownership]
time_estimate_min: 10
order: 220
---

## Ask

You have taken over an IDoc interface where, on a bad week, forty documents fail and nobody
notices until a customer phones. Design the operating model: who finds out, who fixes it, and
how does anyone know the backlog is empty?

## Tests

Whether the candidate can build an ownership and detection model around an integration, rather
than describing tools, and whether they separate failures by who can actually resolve them.

## Ideal minimal answer

Two populations with two owners: documents that never reached SAP, and documents that arrived
and failed to post — business errors like missing master data to the business, technical ones to
IT. Reconcile sent against posted daily so an empty backlog is measured, alert on age as well as
count, name who acts out of hours, and say who may declare a document dead.

## Listen for

- Separates the populations: documents that never reached SAP at all, and documents that reached
  it and failed to post — different places, different owners, different recovery
- Business errors such as missing master data or a blocked customer belong to the business;
  technical errors belong to IT; the model has to route them, not pile everything into one inbox
- A daily reconciliation that counts sent against posted, so "the backlog is empty" is measured
  rather than believed
- Alerting on age as well as on count: one document stuck for six hours can be worse than forty
  stuck for five minutes
- Reprocessing a stored document is safe to repeat; re-sending the source is not, and the model
  has to say who may do which
- Somebody has to be allowed to declare a document dead, and that decision has to be recorded
- Asks what a late document actually costs before deciding how loud the alert is

## Expected knowledge

- A failed inbound document is retained and can be reprocessed
- Counts on the sending side and the receiving side can be compared

## Strong signals

- Builds a view the business can read themselves instead of a queue only IT can see
- Sets an expiry so failures cannot accumulate silently for months
- Says what happens when the person who owns the business errors is on holiday
- Starts from the customer's experience — they found out first — and works back to the control
  that was missing

## Weak signals

- Proposes a daily manual check of the monitor as the control
- Routes everything to the integration team regardless of cause
- Treats reprocessing and re-sending as interchangeable

## Answer bands

### mid

- Puts monitoring and an alert on failed documents and names who receives it.
- Knows failed documents are retained and can be pushed through again.

### senior

- Splits errors by cause and routes each to the team that can fix it.
- Reconciles counts end to end rather than trusting a single monitor.
- Distinguishes safe reprocessing from a re-send that duplicates.

### lead

- Defines the operating model: owners, response times, escalation, and what happens out of
  hours.
- Makes the state visible to the business in their own terms, and agrees the thresholds with
  them.
- Sets the rule for abandoning a document and records who decided.
- Measures the model itself — how many are found by monitoring versus by a customer — and
  reviews it.

## Follow-ups

- One of the forty was a duplicate somebody keyed in by hand while waiting. How does your model
  cope?
  probes: manual intervention outside the interface, and reconciliation catching it
- The business owner says every one of these is for the technology team to sort out. How does
  that conversation go?
  probes: whether they can hold a boundary and justify it
- Six months in, how would you know the model is working?
  probes: measuring detection, not just failures
- A document has been failing for three weeks and nobody will decide. What do you do?
  probes: expiry rules and accountability

## Notes

Keep the candidate away from tool names. The discriminator is whether they can name the two
populations of failures and assign each an owner, a detection time and a recovery that is safe
to repeat.

Verified in the decompiled SAP IDoc library 3.1.4, and it is why the two populations really are
two. On the sending side, `com.sap.conn.idoc.jco.JCoIDoc.send(...)` is transactional in every
overload — it takes a transaction id and dispatches through `JCoFunction.execute(destination,
tid[, queueName])` — so it returns once SAP has recorded the unit and gives the caller no
outcome, no document number back and no exception for anything that fails afterwards. Documents
that never reached SAP are therefore visible only as unconfirmed transactional units on the SAP
side, while documents that arrived and failed to post are visible only as IDoc status. Nothing
in the client library spans both, which is exactly why the reconciliation in `## Listen for` has
to be built rather than looked up.

Verified: the library will not catch a malformed document for you either.
`com.sap.conn.idoc.IDocDocument.checkSyntax()` exists and does enforce mandatory segments and
occurrence limits from the metadata, but `JCoIDoc.send` never calls it, and
`com.sap.conn.idoc.rt.DefaultIDocSegment.addChild` validates only that the segment type is a
legal child — not how many of them there are. So a structurally invalid IDoc is sent happily and
fails on the SAP side, arriving in the population the business has to triage. A candidate who
proposes validating before sending has proposed something real and unusual.

Verified: the library has no notion of what a status code means. `IDocDocument.getStatus()` is a
raw two-character control-record field, and there are no status constants or classification
anywhere in the jar. Routing errors by cause, which this card is built on, is therefore
application work on top of SAP-side information — it is not a feature anyone can switch on.
