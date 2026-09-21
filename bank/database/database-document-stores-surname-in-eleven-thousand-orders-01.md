---
id: database-document-stores-surname-in-eleven-thousand-orders-01
schema_version: 2
title: A surname copied into eleven thousand orders
category: database
topic: document-stores
level: mid
tags: [data-modelling, correctness, consistency]
time_estimate_min: 8
order: 310
links:
  related: [database-relational-model-denormalised-copy-01]
---

## Ask

An orders service in MongoDB stores each order as a document with the customer's name, address
and phone copied into it. A customer marries, changes her surname, and asks for her invoices to
show the new one. Support says "just update the customer." There are eleven thousand orders. What
do you tell Support?

## Tests

Whether the candidate treats a copied field as a deliberate choice that owes an update path, and
can tell a stale duplicate apart from a deliberate record of what was true at the time.

## Ideal minimal answer

Ask Support whether an invoice shows her name as it is now or as it was on the day; that decides
everything else. There is no single place to edit: updating eleven thousand orders is eleven
thousand independent writes, with readers seeing a mixture while it runs, and fields that must
follow the customer should be a reference instead.

## Listen for

- There is no single place to edit: the name sits inside every order record
- Asks first whether an invoice is meant to show the name as it is now or as it was on the day
- Rewriting eleven thousand records is eleven thousand writes, and readers see a mixture of old
  and new while it runs
- If those fields must follow the customer, the order should hold only a reference and the name
  should be fetched from the customer
- If the invoice is evidence of what was agreed, the copy is right and should not be touched —
  the answer is to reissue or annotate, not to overwrite
- Distinguishes the fields that are a snapshot from the fields that are a cache
- Asks what else in the system has already copied that name

## Expected knowledge

- The same value copied into many documents means many separate writes
- MongoDB has supported multi-document transactions since 4.0, at a cost; a plain bulk update is
  not one

## Strong signals

- Asks what the record is for before proposing to alter it
- Plans the rewrite to be resumable and safe to run twice, rather than as one long command
- Notices that a customer's address has exactly the same problem and exactly the opposite answer
  from her display name

## Weak signals

- Updates the customer record and assumes the orders follow
- Proposes a bulk rewrite with no account of what readers see mid-flight
- Declares the document model a mistake and a relational schema the fix, without answering the
  question that was asked

## Answer bands

### weak

- Updates the customer and assumes the orders pick it up.
- Proposes rewriting every order with no mention of what happens part way through.
- Says this proves the wrong database was chosen, and leaves the invoice question unanswered.

### junior

- Says the name is duplicated into each order and there is no one field to edit.
- Recognises that fixing it means touching every affected order.
- Asks someone whether the old invoices are supposed to look different afterwards.

### mid

- Asks whether the invoice should carry today's name or the name at the time of the order, and
  says the answer decides everything else.
- Describes the rewrite as many independent writes, with readers seeing a mixture while it runs.
- Proposes holding a reference for the fields that must follow the customer, and accepts the
  extra fetch that costs.

### senior

- Splits the fields by purpose — evidence of an agreement versus a copy kept for convenience —
  and handles each differently in the same answer.
- Names who has to authorise an edit to an already issued invoice, rather than deciding alone.
- Describes the rewrite as batched, restartable and safe to repeat, and says how progress is
  tracked.
- Asks what else already holds that name, so the fix does not leave a second copy behind.

## Follow-ups

- Half way through the rewrite the process dies. What does the data look like now?
  probes: no atomicity across records; whether they planned for a partial run at all
- She asks that her older invoices keep the surname she had then, for her own records. Does that
  change your answer?
  probes: whether a duplicate can be the correct historical record rather than stale data
- Orders written two years ago have no phone field at all. What does the code that renders an
  invoice do?
  probes: that the shape now lives in the application, and how it copes with several shapes at
  once
- Tomorrow the same request arrives for a field that appears on two million orders instead of
  eleven thousand. Same plan?
  probes: whether the plan scales, or whether it only worked because the number was small

## Notes

Figures to release when asked, and credit the candidate who asks: about eleven thousand orders
for this customer, about four million in the collection; invoices are regenerated on demand from
the order record, not stored as files; finance keeps its own export of issued invoices.

The best answers are split answers: the display name on an open, unshipped order should follow
the customer, and the name on a settled invoice should not.

## Sources

- https://www.mongodb.com/docs/manual/core/transactions/
- https://www.mongodb.com/docs/manual/data-modeling/
