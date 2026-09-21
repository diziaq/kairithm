---
id: sap-jco-bapi-success-nothing-saved-01
schema_version: 2
title: The BAPI returned a document number and nothing was saved
category: sap-jco
topic: bapi
level: junior
tags: [transactions, correctness, consistency]
time_estimate_min: 6
order: 50
links:
  related: [spring-transactions-partial-save-01]
  deeper: [sap-jco-bapi-two-bapis-one-commit-01]
---

## Ask

Your code calls a BAPI to create a sales order. No exception, and a document number comes back in
the result. The order is nowhere in SAP. What happened?

## Tests

Whether the candidate knows that a BAPI leaves the decision to save to its caller, and that the
absence of a Java exception says nothing about what SAP did.

## Ideal minimal answer

The BAPI does not save on its own: nothing called `BAPI_TRANSACTION_COMMIT`, so the work was
discarded when the session ended. The document number is allocated during the call and proves
nothing about whether the order exists.

## Listen for

- A BAPI does not save on its own; the caller has to call `BAPI_TRANSACTION_COMMIT` afterwards
- Without it the work is discarded when the session ends, which is exactly the symptom
- The number in the result is allocated during the call and proves nothing about the outcome
- The `RETURN` table has to be read first: message type `E` or `A` means do not save, and call
  `BAPI_TRANSACTION_ROLLBACK` instead
- A BAPI is specified to report business problems as rows in `RETURN` rather than by raising, so
  a call that raises nothing has told you nothing yet — the result has to be inspected

## Expected knowledge

- A BAPI is a remote-callable function module with a documented interface
- Changes are collected and applied when the work is committed, not statement by statement

## Strong signals

- Asks where in their code that final step belongs, and notices it must run on the same session
  as the work it is saving
- Says a BAPI that reports nothing and writes nothing is a normal outcome to design around, not
  a bug report

## Weak signals

- Concludes success from the absence of a Java exception
- "The BAPI must be broken" or "SAP lost it"
- Only ever checks the first line of the message table

## Answer bands

### weak

- Blames SAP or the function module with no account of what the caller owes it.
- Treats the returned number as proof the order exists.

### junior

- Names the missing final step that makes the work permanent.
- Says the returned number alone does not mean anything yet.

### mid

- Reads the message table before deciding, and says which message types stop them.
- Names the counterpart that throws the work away when a message says stop.
- Notices the saving step has to belong to the same session as the work.

## Follow-ups

- They add the missing step and now the order appears, but a read two lines later still shows
  nothing. What would you suspect?
  probes: asynchronous application of the change, and reading too early
- The job runs twice after a restart and there are now two orders. Whose problem is that?
  probes: whether a repeat is safe, and where the check belongs
- How would you have found this in a code review rather than in production?
  probes: whether they treat the caller's obligations as reviewable

## Notes

The most common wrong answer at this level is treating a silent, empty result as success. The
second most common is adding the saving step in a place that does not share the session with the
call it is meant to save — that is the deeper card.

## Sources

- https://help.sap.com/doc/abapdocu_751_index_htm/7.51/en-us/abapcommit.htm
- https://help.sap.com/doc/abapdocu_752_index_htm/7.52/en-US/abensap_luw_update_task_abexa.htm
