---
id: microservices-ownership-paged-for-someone-elses-data-01
schema_version: 2
title: Paged at three in the morning for another team's bad data
category: microservices
topic: ownership
level: lead
tags: [ownership, operations, failure-modes, correctness]
time_estimate_min: 10
order: 240
---

## Ask

Checkout starts failing at three in the morning. The cause is a malformed row in the catalogue
service's data, written last week by an import job owned by a third team. The checkout engineer
spent four hours finding it. Nothing in the architecture is technically broken. What do you
change?

## Tests

Whether the candidate can turn a cross-team failure into concrete changes in where data is
validated, who is alerted, and how a fault is attributed.

## Ideal minimal answer

The engineer who was woken could not fix the cause and the team who could was not told, so route
this class of alert to the writer and make the failure name the bad record and its source.
Validate the import against what its consumers require, in the import team's own pipeline, and
alert on the data so a bad row is found the day it lands.

## Listen for

- The team that was woken cannot fix the cause, and the team that can was not told; that mismatch
  is the thing to fix
- Validation at the point of writing, so a bad row never enters and never travels; the import job
  should be checked against what its consumers require
- Checkout defends itself too: skip or quarantine a row it cannot use and fail one product rather
  than the whole page
- The failure should say which record and where it came from, so four hours becomes four minutes
- Underneath it is an undocumented, unverified contract between three teams
- A week between the bad write and the failure is its own problem: the damage was detectable long
  before anyone noticed

## Expected knowledge

- An alert should reach someone who can act on it
- A malformed record is durable and keeps failing until someone removes it

## Strong signals

- Asks how many other rows are already bad, not only how to prevent the next one
- Distinguishes making the data correct from making the page survive incorrect data, and wants
  both
- Says what the import job should do with a batch it cannot fully validate, rather than assuming
  reject-everything

## Weak signals

- "The import team should be more careful"
- Adds a null check in checkout and considers the incident closed
- Moves the pager to the catalogue team and changes nothing else
- Tells the story of a three-in-the-morning page at a previous job and never says what to change
  here

## Answer bands

### mid

- Adds defensive handling in checkout so the page survives a bad row.
- Says the import job should validate its input.
- Does not address who is alerted or how the cause was found.

### senior

- Puts a check at the writing edge and one at the reading edge, and explains why both.
- Makes the failure carry enough information to identify the record and its source.
- Goes looking for how many other bad rows are already in there.

### lead

- Writes the contract between the three teams down and says what verifies it, in whose pipeline.
- Decides who is on the pager for this class of fault and what the alert has to contain to be
  routed there.
- Judges the four hours as the primary cost and targets that, separately from preventing the fault.
- Addresses the week-long gap with a signal on the data rather than on the services.

## Follow-ups

- The import team say their job did exactly what it was asked to do. Are they wrong?
  probes: locating accountability without blame; where the check belongs and who specifies it
- A week passed between the bad write and the failure. What would have shortened that?
  probes: detection at write time against detection at read time; alerting on data, not services
- Who is on the pager for this tomorrow morning, given the structure you already have?
  probes: making a concrete ownership call inside an imperfect organisation
