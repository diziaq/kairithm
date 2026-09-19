---
id: microservices-api-evolution-deleting-a-field-nobody-uses-01
schema_version: 1
title: Deleting a field you are fairly sure nobody uses
category: microservices
topic: api-evolution
level: senior
tags: [api-design, ownership, operations, correctness]
time_estimate_min: 9
order: 140
links:
  related: [microservices-ownership-shared-library-everyone-edits-01]
---

## Ask

You want to delete a field from a response. You are fairly sure nobody uses it. Six teams consume
this API and two of them are outside the company. How do you find out for certain, and how long
does this take?

## Tests

Whether the candidate can run a deprecation as a process with evidence, a deadline and a decision
rule, rather than as an announcement.

## Listen for

- You cannot tell from traffic alone whether one field is read, so something has to be added to
  measure it
- A published date, written down where consumers look, and the difference between an internal
  team you can chase and an external one you cannot
- Says what happens on the day if somebody is still reading it: hold, or break them deliberately
  and with agreement
- Gives a realistic timescale in months, and is comfortable saying so out loud
- Weighs the cost of carrying the field forever against the cost of a surprise outage for a
  customer
- Asks why it is being removed at all, because the answer changes how hard you push

## Expected knowledge

- Usage evidence is something you build, not something you have
- An external consumer may be bound by a contract that governs how much notice they get

## Strong signals

- Distinguishes fields that are merely unused from ones that are actively harmful to keep
- Proposes a controlled break — a short scheduled removal with the field returning afterwards —
  to smoke out silent consumers
- Names who signs off when an external party has not replied

## Weak signals

- Emails everyone, waits two weeks, deletes it
- Treats a version bump as free and creates a new version for one field
- Assumes silence means consent with no escalation path

## Answer bands

### mid

- Wants to measure who reads it before touching anything.
- Announces a removal date and keeps the field until then.
- Has no answer for an external consumer that goes quiet.

### senior

- Builds the evidence deliberately and says what it can and cannot prove.
- Sets a window sized from how consumers actually work, including jobs that run monthly.
- Says what happens on the deadline day, in both directions.

### lead

- Treats it as a policy question, not a ticket: what the default notice period is for anyone
  publishing an API here.
- Makes an explicit call when the evidence runs out, and names who carries the consequence.
- Compares the cost of keeping the field forever against the cost of the programme to remove it,
  and is willing to keep it.
- Says how the same decision gets made next time without another round of investigation.

## Follow-ups

- The measurement shows zero reads for ninety days. Is that proof?
  probes: quarterly jobs, seasonal traffic, disaster-recovery paths that run once a year
- One of the two outside the company goes silent and never replies. What is your call?
  probes: deciding under an unresponsive counterparty; escalation and contractual obligation
- Your CEO wants the field gone this week because of a data protection request.
  probes: reframing when the constraint stops being convenience and becomes obligation
