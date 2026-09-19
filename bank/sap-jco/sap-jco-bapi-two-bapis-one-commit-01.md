---
id: sap-jco-bapi-two-bapis-one-commit-01
schema_version: 1
title: Both or neither, across two BAPIs
category: sap-jco
topic: bapi
level: senior
tags: [transactions, consistency, integration, correctness]
time_estimate_min: 9
order: 170
links:
  related: [sap-jco-stateful-sessions-context-required-01]
---

## Ask

New requirement: create a customer and its contract in one go, and the business says either both
or neither. Both BAPIs are in the same SAP system. What do you build — and what do you tell them
if the second one turns out to live in a different system?

## Tests

Whether the candidate can build a single unit of work out of two BAPI calls, and whether they
will refuse to promise atomicity across systems instead of inventing it.

## Listen for

- Within one system: both calls plus one `BAPI_TRANSACTION_COMMIT` at the end, with each call's
  `RETURN` table checked for `E` or `A` first, and `BAPI_TRANSACTION_ROLLBACK` if anything
  refuses
- Those calls have to share one session, or they are not one unit of work at all
- With `WAIT` set, the commit comes back after the change has actually been applied; without it,
  a read straight afterwards can legitimately show nothing
- A failure during the asynchronous update lands in the update queue on the SAP side, not in
  your return value — so "committed" is not the end of the story unless you waited
- Across two systems there is no shared commit: say so, and design compensation instead — pick
  which side is the source of truth, make the second step retriable, and decide what undoes the
  first
- Who reconciles when the compensation itself fails, and how the half-finished pair is found

## Expected knowledge

- BAPI changes are applied through the update mechanism at commit time
- Two separate pooled calls do not form one unit of work

## Strong signals

- Asks whether the business really means both-or-neither, or means "the customer is useless
  without a contract, and somebody must notice within an hour"
- Names the window where the first system has committed and the second has not, and says who
  sees it
- Points out that the ABAP side may already offer one function module that does both properly
- Will not describe a two-system compensation as a transaction

## Weak signals

- Wraps the two calls in a Java transaction annotation and believes SAP joins it
- Promises atomicity across systems with no mechanism behind it
- Reads back immediately after committing and treats an empty result as a failure

## Answer bands

### mid

- Sequences the two calls and saves once at the end.
- Checks the message table of each call before going on.

### senior

- Keeps both calls in one session and says why that is required.
- Handles the refusal case explicitly, including undoing the first call's work.
- Knows the difference between the save returning and the change being visible, and picks
  deliberately.
- States plainly that the two-system version has no shared commit and moves to compensation.

### lead

- Turns the requirement into something implementable: what the business needs is a bounded
  inconsistency window and a guaranteed detection, not atomicity.
- Says who owns the reconciliation, how the stuck pairs surface, and what the operator does with
  them.
- Considers pushing the whole unit into one ABAP-side call and weighs that against owning the
  orchestration in Java.

## Follow-ups

- The customer is created, the contract is refused, and your undo call also fails. What now?
  probes: whether compensation has a failure path and an owner
- Straight after saving, your code reads the contract back and gets nothing. Is that a bug?
  probes: waiting for the change to be applied versus returning immediately
- The business insists on both-or-neither across the two systems and will not accept a window.
  How do you handle that conversation?
  probes: whether they can refuse a requirement and offer something achievable instead

## Notes

Verified: with the wait flag set, the commit is performed so that the changed data is readable
afterwards; without it, an immediate read can still see the old state, and an update failure
surfaces in the update queue rather than in the caller's result.

## Sources

- https://community.sap.com/t5/application-development-and-automation-discussions/how-and-when-to-use-wait-parameter-in-bapi-transaction-commit-help/td-p/4473620
- https://github.com/SAP-samples/abap-cheat-sheets/blob/main/17_SAP_LUW.md
