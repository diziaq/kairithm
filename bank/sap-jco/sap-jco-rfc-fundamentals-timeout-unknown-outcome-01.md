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

Verified: JCo 3 has no per-call execution timeout. There is no way to say "give up on this
`JCoFunction.execute` after thirty seconds". `jco.destination.max_get_client_time` is the setting
candidates usually reach for and it is not this — it bounds how long a caller waits to be handed
a pooled connection when the peak limit is already allocated, and expires before the function
module has been called at all. The only documented way to bound an execution is indirectly,
through the lifetime of a session: when JCo sees a session end it cancels the calls belonging to
it. So a candidate who says "we set a timeout on the call" should be asked which property, and
the honest answer is that the communication error in the scenario came from the network or the
gateway, not from a JCo timer.

NEEDS-REVIEW — narrowed after review. What is verified and can be asserted: a document that was
already committed stays committed, because nothing issues a rollback on the client's behalf; and
uncommitted work is never persisted, because no commit ever ran. What could not be confirmed from
public documentation is the *timing and mechanics* on the SAP side — whether an in-flight, not
yet committed unit is torn down the moment the socket is lost, or only when the work process is
later reused, and how gateway timeouts interact with that. Do not ask a candidate to state the
moment, and do not state it yourself. The card does not depend on it: the three possible outcomes
stand either way.

## Sources

- https://help.sap.com/doc/abapdocu_752_index_htm/7.52/en-US/abenrfc_context.htm
- https://help.sap.com/doc/abapdocu_751_index_htm/7.51/en-us/abapcommit.htm
- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
