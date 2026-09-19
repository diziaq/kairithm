---
title: A create call to SAP times out. Do you retry it?
difficulty: 4
tags: [sap, rfc, reliability, idempotency]
time_minutes: 6
order: 20
---

## Ask

Your service calls a change BAPI in SAP. The call times out. Do you retry it automatically?

## Look for

- A timeout does not prove SAP did nothing
- Classifies the operation first, because a create is not a read
- Uses a stable business key and reconciles, rather than retrying blind
- Represents "final outcome unknown" as its own state, separate from success and failure
- Duplicate prevention has to be checkable in SAP, not only in the service memory

## Red flags

- Always retries three times with backoff
- Calls a request id in Java an idempotency key when SAP never sees it
- Treats a successful transport as a successful business commit

## Follow-ups

- What does your API return to its caller while reconciliation is pending?
- How does that survive a restart of your service?
