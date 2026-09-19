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

NEEDS-REVIEW — unverified claim about exactly when the ABAP session is terminated after the
client disconnects. What is safe to assert: the work is not automatically rolled back on the
client's behalf, and a document already saved stays saved. Do not let a candidate be marked down
for being unsure about the precise moment the ABAP side notices.

If a candidate asserts JCo has a per-call timeout setting, ask which one and what it does. Do not
assume such a parameter exists.
