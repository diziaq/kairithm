---
id: sap-jco-bapi-two-bapis-one-commit-01
schema_version: 2
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

## Ideal minimal answer

In one system: both calls on one session, each call's `RETURN` table checked for `E` or `A`,
then one `BAPI_TRANSACTION_COMMIT` — or `BAPI_TRANSACTION_ROLLBACK` if either refuses; with
`WAIT` set the commit returns after the change is applied, without it an immediate read can
legitimately show nothing. Across two systems there is no shared commit, so I would say that
plainly and design compensation instead.

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

Verified: `BAPI_TRANSACTION_COMMIT` issues `COMMIT WORK` with `WAIT` blank and `COMMIT WORK AND
WAIT` with `WAIT` set. `AND WAIT` means processing does not continue until the update work
process has run the update modules, which is what makes the data reliably readable on an
immediate read afterwards; without it the caller resumes while the update is still running, so
an immediate read-back can legitimately return the old state. An update-task failure is recorded
in the update queue, visible in `SM13`, and does not appear in the caller's `RETURN` table. Treat
`SM13` as interviewer background — the candidate needs the concept, not the code.

## Sources

- https://help.sap.com/doc/abapdocu_751_index_htm/7.51/en-us/abapcommit.htm
- https://help.sap.com/doc/abapdocu_752_index_htm/7.52/en-US/abensap_luw_update_task_abexa.htm
- https://github.com/SAP-samples/abap-cheat-sheets/blob/main/17_SAP_LUW.md
