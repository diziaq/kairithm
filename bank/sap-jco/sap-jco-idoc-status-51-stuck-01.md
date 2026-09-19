---
id: sap-jco-idoc-status-51-stuck-01
schema_version: 1
title: Three hundred IDocs in status 51 and a business asking to re-send
category: sap-jco
topic: idoc
level: mid
tags: [operations, failure-modes, idempotency]
time_estimate_min: 7
order: 100
links:
  deeper: [sap-jco-idoc-error-ownership-01]
---

## Ask

Your interface sends IDocs into SAP. Three hundred of last night's are sitting in status 51 and
the business wants to know whether to re-send the files. What do you tell them?

## Tests

Whether the candidate knows what status 51 means about where the data already is, and therefore
why re-sending is the wrong recovery.

## Listen for

- Status 51 means the IDoc arrived and was stored in SAP, and the posting into the application
  failed — the data is already there
- So re-sending the file produces a second IDoc for the same business document, and if the cause
  is then fixed you get two postings
- The recovery is to fix the cause and reprocess the stored IDocs, which creates no duplicate
- Reads the status text to separate a data problem from a setup problem: missing master data, a
  locked object, a partner or authorisation issue
- Three hundred at once is usually one cause; group by message before touching anything
- Knows 53 means posted and 64 means waiting to be posted, and that a pile of 64 is a different
  fault — the posting job is not running

## Expected knowledge

- Inbound IDocs can be posted immediately or collected and posted by a job, depending on the
  partner setup
- Reprocessing is a standard action on the SAP side, not a custom program

## Strong signals

- Asks who is allowed to decide a failed document will never post, and where that is recorded
- Wants to know why nobody noticed for a whole night before discussing the three hundred
- Checks whether some of the three hundred have since been posted manually, so reprocessing would
  duplicate them after all

## Weak signals

- Treats re-sending as free
- Cannot say whether the business data is inside SAP already
- Asks the ABAP team to "delete and re-import" without considering what has been posted

## Answer bands

### weak

- Says re-send the files, with no account of what is already stored.
- Cannot say what the status number tells them.

### junior

- Knows the documents reached SAP and failed on the application side.
- Says somebody should look at the error before anything is re-sent.

### mid

- Explains why re-sending duplicates and reprocessing does not.
- Reads the error text and splits data causes from setup causes.
- Groups the three hundred by cause instead of handling them one by one.

### senior

- Names the second population — documents that never arrived at all — and where those live.
- Asks how the failure went unseen all night and treats that as the actual defect.
- Says who owns which class of error and how a fixed one gets back into flight safely.

## Follow-ups

- Half of them turn out to be missing a customer that was created this morning. What do you do
  with the other half?
  probes: grouping by cause, and not applying one recovery to everything
- The business says they will just key the urgent ones in by hand. What do you need to happen
  before the stored ones are pushed through?
  probes: manual work creating duplicates on reprocessing
- Two hundred more failed last night and nobody was told again. What would you build first?
  probes: alerting on age and count, and who receives it

## Notes

Status 51 is "application document not posted". 53 is posted, 64 is ready to be passed to the
application. Do not turn this into a status-number quiz: the point is the difference between the
IDoc existing and the business document existing.
