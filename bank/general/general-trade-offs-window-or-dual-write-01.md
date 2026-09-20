---
id: general-trade-offs-window-or-dual-write-01
schema_version: 1
title: Two hours down on Sunday, or three weeks of writing both
category: general
topic: trade-offs
level: senior
tags: [correctness, consistency, operations, failure-modes]
time_estimate_min: 8
order: 155
links:
  related: [microservices-consistency-two-services-disagree-01]
  deeper: [general-trade-offs-ship-the-shortcut-01]
---

## Ask

You have to split one name column into two across a table of two hundred million rows that is
written to all day. One engineer wants a two-hour maintenance window on Sunday night and a
single migration script; another wants to write both shapes for three weeks, fill in the old
rows in the background, and never take the system down. Which do you pick, and what would
change your mind?

## Tests

Whether the candidate compares two ways of changing live data on how each one fails part-way
through and what it leaves behind, rather than choosing the one that sounds safer or more
modern.

## Listen for

- Asks who is using the system at that hour and what two hours of it being unavailable costs
- Asks what happens if the script is half finished when the window runs out, and whether it can
  be stopped and picked up again
- Wants a timed run against a copy at full size before either plan is agreed to
- Points out that the three-week plan leaves the same fact in two places, and asks how anyone
  would notice them disagreeing
- Separates the second plan into steps — write both, fill in the past, move the reads, remove
  the old — and treats each as a decision of its own
- Asks who removes the old column and when, because the change is not finished while it is
  still there
- Asks what the split should produce for rows that do not divide into two cleanly

## Strong signals

- Wants a comparison of old and new running while both exist, so a mismatch is found by a check
  rather than by a customer
- Says what the application should read for a row the background work has not reached yet
- Treats the estimate of the script's runtime as the weakest part of the first plan and asks for
  a measurement instead
- Expects both columns to still be there a year later unless somebody owns taking one away

## Weak signals

- Rules out downtime on principle without knowing how long the script would take
- Assumes it will fit in the window because it ran quickly against a development database
- Has no way back once either plan has started
- Leaves removal of the old column as tidying up that somebody will get to

## Answer bands

### weak

- Picks a side on principle — we never take the system down, or we never carry two shapes of the
  same data — without asking how long the script would take.
- Treats a quick run against a development database as evidence that it fits in the window.
- Cannot say what state the table is in half way through either plan, or how to get back.

### junior

- Asks how long the script takes and whether anyone uses the system on a Sunday night.
- Says it should be tried somewhere else before it is run for real.
- Worries that rows written while the change is happening could be missed.

### mid

- Asks for a timed run on a full-size copy before committing to either option.
- Describes what the application sees while only some of the rows have been converted.
- Names a way back from each plan if it goes wrong in the middle.
- Points out that two copies of the same fact can end up disagreeing.

### senior

- Breaks the longer plan into steps and says which of them can be undone and which cannot.
- Keeps the two copies compared while both exist, and treats a mismatch as something to be
  alerted on rather than audited later.
- Sizes the window from a measured run and says what the team does when midnight arrives and the
  script is a third done.
- Refuses to start until someone has decided what happens to the rows that do not split.

### lead

- Weighs what two hours of unavailability costs the business against three weeks of the team
  carrying two shapes of the same data.
- Gives the removal of the old column an owner and a date, and says what stops the work stalling
  half done.
- States the condition that would make them abandon the chosen plan and take the other one.

## Follow-ups

- The script starts at ten on Sunday night and by midnight it has got through a third of the
  table. What do you do?
  probes: whether the plan had a stopping point, or only a hope that it would finish in time
- A month after the switch someone finds a few thousand rows where the two versions of the name
  do not match. What went wrong, and when should you have known?
  probes: checking while the change is running rather than declaring success at the end
- Same change, but the table is a tenth of the size and the system has no users at all at the
  weekend. Does your answer change?
  probes: whether the numbers drive the choice or a preference for one style of change does
