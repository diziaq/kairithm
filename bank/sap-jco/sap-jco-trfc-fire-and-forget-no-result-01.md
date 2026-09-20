---
id: sap-jco-trfc-fire-and-forget-no-result-01
schema_version: 1
title: The endpoint got fast and two postings went missing
category: sap-jco
topic: trfc-qrfc
level: junior
tags: [integration, delivery-semantics, failure-modes]
time_estimate_min: 6
order: 25
links:
  deeper: [sap-jco-trfc-sm58-backlog-01]
---

## Ask

To make a slow endpoint fast, a colleague changed a posting call: the code now asks the
destination for a transaction id, fires the function module with that id, and returns
immediately. The endpoint went from three seconds to fifty milliseconds. In test, two postings
never appeared in SAP and there is nothing in our log. What does our code actually know about
that call, and where would you look for the two that are missing?

## Tests

Whether the candidate understands that a transactional call returns when the request has been
recorded, not when the work has been done, and knows that the outcome is therefore reported
somewhere other than in their own log.

## Listen for

- The call now returns as soon as SAP has written the unit down; the function module runs
  afterwards, in its own unit of work
- So a successful return means "accepted", not "posted" — the two are no longer the same thing
- Nothing comes back: no export parameters, no tables, no message from the function module, and
  no exception if it fails later, which is why the log is empty
- An error in the delayed execution is recorded on the SAP side against that destination, in the
  transactional RFC monitor, not on ours
- The two missing postings are most likely sitting there with an error, or still waiting to be
  retried — they are not lost
- If we need to know the outcome, somebody has to go and get it: read the document back, or have
  the SAP side report failures to us

## Expected knowledge

- A transaction id identifies one unit of work and is created before the call
- `SM58` is where transactional units and their errors are visible on the SAP side

## Strong signals

- Asks why the call was slow in the first place, before accepting that hiding the wait was the
  fix
- Says the client should confirm the unit afterwards so the SAP side can clear its record
- Asks what the caller of the endpoint now believes when it gets a 200 back

## Weak signals

- Treats the fast return as proof the posting succeeded
- Looks for the error in the Java log and concludes SAP silently dropped the data
- Says the fix is to catch the exception the call throws, without noticing there is none

## Answer bands

### weak

- Thinks the posting is lost because nothing was logged on our side.
- Cannot say what changed about the call other than that it is faster.

### junior

- States that the call returns once SAP has accepted the unit and runs it later.
- Knows no result or error comes back to the caller.
- Goes to the SAP side to look for the two failed units rather than re-sending blindly.

### mid

- Spells out what the endpoint's 200 now promises to its caller, and what it does not.
- Says how the outcome would be brought back — reading the document, or the SAP side reporting
  errors outward — rather than leaving it unanswered.
- Notes the unit will be retried, so whatever is on the other end has to cope with running twice.

## Follow-ups

- The colleague says the endpoint is now fast and the tests are green, so it is fine. What do you
  tell the person who takes the order over the phone?
  probes: whether they can express "accepted, not posted" to a non-technical listener
- One of the two turns up in SAP an hour later, posted correctly. How?
  probes: the unit was stored and retried, not lost
- What would you add so that a posting failing in SAP at three in the morning reaches us?
  probes: the outcome has to be pulled or pushed back; it does not arrive on its own

## Notes

The client-side API is `JCoDestination.createTID()` followed by
`JCoFunction.execute(destination, tid)`; return parameters cannot be delivered, which is why
BAPIs with a return structure are a poor fit for this style of call. A candidate who describes
the behaviour without the method names has answered well.

## Sources

- https://github.com/cemeng/sap-integration/blob/master/sapjco3-darwinintel64-3.0.14/javadoc/com/sap/conn/jco/JCoDestination.html
- https://help.sap.com/doc/saphelp_nw74/7.4.16/en-US/48/99b963ee2b73e7e10000000a42189b/content.htm
- https://help.sap.com/doc/saphelp_em92/9.2/en-US/48/821b412ddd3cb8e10000000a42189d/content.htm
