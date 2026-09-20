---
id: sap-jco-rfc-fundamentals-timeout-unknown-outcome-01
schema_version: 1
title: The call died and nobody knows whether it posted
category: sap-jco
topic: rfc-fundamentals
level: senior
tags: [idempotency, retries, consistency, failure-modes]
time_estimate_min: 9
order: 130
links:
  related: [sap-jco-bapi-two-bapis-one-commit-01]
---

## Ask

A goods receipt posting dies after two minutes with a communication error. The warehouse
supervisor asks you the only question they care about: was it posted or not? How do you answer
that today, and how do you make sure the question is answerable next time?

## Tests

Whether the candidate treats a broken call as an unknown outcome to be resolved against the far
side, rather than as a failure they can assume away or retry blindly.

## Listen for

- A lost connection says nothing about the state of the work in SAP: it may have completed and
  been saved, completed and been discarded, or never run at all
- Today the answer is to look it up — query SAP for the document using the business key or their
  own reference — not to guess and not to retry blindly
- SAP does not undo the work because the client went away; if the save had already run, the
  document is there
- Next time: carry a reference of your own into a field SAP stores, so the query-back is exact
  and a repeat is recognisable
- A repeat is safe only if somebody made it safe — either the caller checks first, or the ABAP
  side stores the reference and refuses a second one
- If the outcome is genuinely unknowable, retrying is a business decision about double postings,
  not a technical one

## Expected knowledge

- What a timeout on a request-response call can and cannot tell you
- That making an operation safe to repeat requires state somewhere that survives the failure

## Strong signals

- Distinguishes a query-back from a guarantee, and says what happens if the query-back itself
  fails
- Says plainly that a function module not designed for repeats cannot be made safe from the Java
  side alone
- Asks how often this happens before deciding how much machinery it justifies
- Wants the unresolved cases visible in a queue with an owner, rather than logged and forgotten

## Weak signals

- "It timed out, so it did not happen"
- Retries automatically on any error, with nothing preventing a duplicate
- Proposes a longer timeout as the answer to the supervisor's question

## Answer bands

### mid

- Says the outcome is unknown and goes to SAP to check before doing anything else.
- Knows a blind retry can post twice.

### senior

- Enumerates the three possible states behind the error and refuses to collapse them.
- Uses a caller-supplied reference so the check is exact, not a fuzzy search by date and amount.
- Says where the duplicate protection has to live for a retry to be safe, and who has to build
  it.
- Treats the failure as routine and designs the recovery path, including who looks at the ones
  that stay unresolved.

### lead

- Prices the machinery against how often it happens and what a double posting costs the
  business.
- Gets the ABAP side to agree an interface contract rather than working around it in Java.
- Says how the team will know the recovery path still works a year from now.

## Follow-ups

- The supervisor cannot wait and posts it again by hand. What have you got now, and how would
  you find out?
  probes: duplicates created outside the system of record, and detection after the fact
- Suppose the check you want to run needs a field nobody was ever asked to store. What do you
  do?
  probes: whether they can negotiate the interface rather than working around it
- This happens twice a year. Does your answer change?
  probes: cost of the damage driving how much is worth building
- The retry runs and also fails, in the same way. What is the next step?
  probes: escalation path, and whether unresolved cases have an owner

## Notes

Verified in the decompiled JCo 3.1.14, and it can be asserted flatly: **there is no per-call
execution timeout.** `com.sap.conn.jco.JCoFunction` declares exactly three `execute` overloads —
destination, destination plus tid, destination plus tid plus queue name — and none takes a
deadline. Searching the whole public package for a timeout turns up nothing on `JCoDestination`,
`JCoFunction`, `JCoContext` or `JCo`. Below the API the read path is deliberately untimed: the
client socket carries a 500 ms `SO_TIMEOUT`, but
`com.sap.conn.rfc.driver.input.CancelableInputStream.read` catches every `SocketTimeoutException`
and continues the loop, breaking out only if an explicit cancel flag has been set. A long-running
ABAP function therefore blocks the calling thread for as long as it likes.

Verified: `jco.destination.max_get_client_time` is the setting candidates usually reach for, and
it is not this. It bounds how long `com.sap.conn.jco.rt.PoolingFactory.getClient` will wait to
hand over a connection once the peak limit is allocated — default 30000 ms — and it expires
before the function module has been called at all, with a `JCoException` of group
`JCO_ERROR_RESOURCE`. The only other configurable time bound on the client is
`jrfc.client_connect_timeout`, default 60 seconds, which covers the TCP connect and nothing after
it. So a candidate who says "we set a timeout on the call" should be asked which property, and
the honest answer is that the communication error in the scenario came from the network or the
gateway, not from a JCo timer.

Verified: the indirect bound through session lifetime is real. When a session is released,
`com.sap.conn.jco.rt.Context.reset()` calls `closeConnections()`, which routes connections that
were still in use through `ConnectionManager.releaseWithCancel` and on to
`ClientConnection.cancel()`. Note `cancel()` is `protected` and there is no public cancel or
abort anywhere in `com.sap.conn.jco` — an application that wants a hard deadline on a call has to
run it on its own executor and impose the deadline itself. That is a legitimate strong answer to
this card.

NEEDS-REVIEW — one sentence, and it is ABAP-side. What happens inside SAP at the moment the
socket is lost — whether an in-flight, not yet committed unit is torn down immediately or only
when the work process is next reused, and how gateway timeouts interact with that — is not
something the client jar can show. Do not ask a candidate to state the moment, and do not state
it yourself. The rest holds: a document already committed stays committed because nothing issues
a rollback on the client's behalf, uncommitted work is never persisted because no commit ever
ran, and the three possible outcomes stand either way.

## Sources

- https://help.sap.com/doc/abapdocu_752_index_htm/7.52/en-US/abenrfc_context.htm
- https://help.sap.com/doc/abapdocu_751_index_htm/7.51/en-us/abapcommit.htm
- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
