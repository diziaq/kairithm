---
id: sap-jco-function-calls-first-row-only-01
schema_version: 2
title: Five hundred rows, all of them the same row
category: sap-jco
topic: function-calls
level: junior
tags: [correctness, integration]
time_estimate_min: 4
order: 30
links:
  related: [java-collections-mutable-key-lookup-01]
  deeper: [sap-jco-function-calls-leading-zeros-01]
---

## Ask

A colleague calls a function module that returns a table of five hundred rows. SAP definitely
returns five hundred different ones, but their Java code logs the same row five hundred times.
What did they write?

## Tests

Whether the candidate knows how a returned table is read in JCo, and can debug from a symptom to
the line that causes it rather than blaming the far side.

## Ideal minimal answer

They looped `getNumRows()` times but never moved the cursor, so every read came from whichever
row the table was parked on. A `JCoTable` is a cursor, not a list — the loop needs `firstRow()`
then `nextRow()`, or `setRow()` with the index on each pass.

## Listen for

- A `JCoTable` is a cursor over the rows, not a list; reading a field reads whichever row the
  cursor is on
- They looped the right number of times and never moved the cursor
- `getNumRows()` returned five hundred, which is why the loop count looked correct and hid the
  bug
- Knows a correct read pattern: `firstRow()` then `nextRow()`, or `setRow(i)` inside an index
  loop
- Says how to confirm it in a minute: print a key field per iteration, or check the value that
  the cursor position is on

## Expected knowledge

- Table parameters are read from the table parameter list of the `JCoFunction`
- A row is a structure of typed fields, read by field name

## Strong signals

- Suggests copying each row into a domain object at the boundary so the cursor never escapes the
  mapping code
- Notices the same shape of bug when the code appends rows to send data in and forgets to append
  before setting fields

## Weak signals

- Blames the function module or asks for an ABAP change
- Says "convert it to a list" with no idea what is being iterated
- Wants to log more without a hypothesis

## Answer bands

### weak

- Assumes SAP returned the same row five hundred times.
- Cannot say how rows are read out of the result.

### junior

- Identifies that the row position is never advanced and shows the corrected loop.
- Explains why the count was right while the content was wrong.

### mid

- Describes both read patterns and when each is clearer.
- Maps rows into their own objects at the boundary so nothing downstream depends on the cursor.
- Names the mirror-image mistake on the way in, when rows are filled before being added.

## Follow-ups

- The same code has to send eight hundred rows into SAP instead. What do you watch out for?
  probes: the append-then-fill order, and the mirror image of the same defect
- The result comes back with the right rows but every text field has spaces on the end. Where
  would you deal with that?
  probes: whether trimming and mapping live in one boundary layer or are sprinkled everywhere
- How would a unit test have caught this without an SAP system to talk to?
  probes: whether they isolate the mapping from the call

## Notes

Reject an answer that stops at "they forgot a loop". The point is that the cursor makes a wrong
program look right, which is why the count matched.

Verified in the decompiled JCo 3.1.14: `com.sap.conn.jco.JCoTable` really is a cursor, not a
collection. It declares `getNumRows()`, `firstRow()`, `lastRow()`, `nextRow()`, `getRow()`,
`setRow(int)`, `appendRow()` and `appendRows(int)`, and the field accessors it inherits from
`com.sap.conn.jco.JCoRecord` read whichever row the cursor is currently on. Both corrected
patterns in `## Listen for` are supported — `firstRow()` then `nextRow()`, or `setRow(i)` in an
index loop — and `appendRow()` is the mirror-image trap on the way in, since the fields have to
be set after the row is appended, not before.

## Sources

- https://github.com/cemeng/sap-integration/blob/master/sapjco3-darwinintel64-3.0.14/javadoc/com/sap/conn/jco/JCoTable.html
- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
