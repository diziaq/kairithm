---
id: sap-jco-idoc-status-51-stuck-01
schema_version: 2
title: Three hundred IDocs in status 51 and a business asking to re-send
category: sap-jco
topic: idoc
level: mid
tags: [operations, failure-modes, idempotency]
time_estimate_min: 7
order: 100
links:
  related: [kafka-offsets-commit-window-01]
  deeper: [sap-jco-idoc-error-ownership-01]
---

## Ask

Your interface sends IDocs into SAP. Three hundred of last night's are sitting in status 51 and
the business wants to know whether to re-send the files. What do you tell them?

## Tests

Whether the candidate knows what status 51 means about where the data already is, and therefore
why re-sending is the wrong recovery.

## Ideal minimal answer

Do not re-send: status 51 means the IDocs arrived and were stored in SAP and only the posting
failed, so a re-send creates a second IDoc for the same business document and, once the cause is
fixed, a second posting. Fix the cause and reprocess the stored ones, and read the status text
first to group the three hundred, separating data causes from setup causes.

## Listen for

- Status 51 means the IDoc arrived and was stored in SAP, and the posting into the application
  failed — the data is already there
- So re-sending the file produces a second IDoc for the same business document, and if the cause
  is then fixed you get two postings
- The recovery is to fix the cause and reprocess the stored IDocs, which creates no duplicate
- Nothing will move these on its own: a failed IDoc sits in that status until a person or a job
  reprocesses it, so "leave it and see" is a decision to leave three hundred documents unposted
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
- Sets out re-sending and reprocessing with accurate trade-offs, and will not tell the business
  which one to do

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
- Asks, without being pointed at it, how the failure went unseen all night, and treats that as
  the actual defect.
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

Interviewer background only, never as a recall test: the documents and their status texts are
listed in `WE02`, and reprocessing failed inbound IDocs is a standard action in `BD87`. A
candidate who says "they can be pushed through again from the SAP side" without naming either
has answered this card.

Contrast with the tRFC backlog card in the trfc-qrfc topic, which looks similar and is not: there
the units are held by the sending system and are retried automatically, so the work is to survive
the burst when they drain. Here nothing retries on its own and somebody has to decide.

Verified in the decompiled SAP IDoc library 3.1.4, and it settles why re-sending duplicates. A
send is a transactional unit: every `com.sap.conn.idoc.jco.JCoIDoc.send(...)` overload takes a
transaction id, and internally it calls `JCoFunction.execute(destination, tid)` — or
`execute(destination, tid, queueName)` for the queued variants — against one of
`IDOC_INBOUND_ASYNCHRONOUS`, `IDOC_INBOUND_IN_QUEUE` or `INBOUND_IDOC_PROCESS`. A second send of
the same file is a new transaction id and therefore a genuinely new unit, which lands as a second
IDoc. There is nothing in the library that would recognise it as a repeat. Also worth knowing:
`com.sap.conn.idoc.jco.rt.JCoIDocDocument.createJCoIDocNumber` invents a synthetic 16-digit
number when `getIDocNumber()` is empty, so the sender's own number is not a business key either.

Verified, and a useful correction if a candidate reaches for it: the IDoc library knows nothing
about status codes. `com.sap.conn.idoc.IDocDocument.getStatus()` returns the raw two-character
`STATUS` field of the control record as a `String` — the implementation in
`com.sap.conn.idoc.rt.DefaultIDocDocument` is a plain field read — and there is no constant,
enum, classification or validation for 51, 53, 64 or any other value anywhere in the jar. Status
is also not among the fields `checkMandatoryFields()` requires. So the meaning of 51 is entirely
an ABAP-side fact, as the sources here have it, and a candidate who suggests their Java code will
"check the status" of a sent IDoc has to be asked where that status would come from — it would
need separate RFC calls that this library does not make.

## Sources

- https://sapintegrationhub.com/sap-s4-hana/sap-idoc-status-codes-guide/
- https://community.sap.com/t5/technology-blog-posts-by-members/how-to-use-transaction-bd87-to-reprocess-failed-idocs/ba-p/13641328
- https://help.sap.com/docs/SUPPORT_CONTENT/abap/3353525129.html
