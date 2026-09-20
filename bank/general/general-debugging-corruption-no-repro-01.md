---
id: general-debugging-corruption-no-repro-01
schema_version: 1
title: Twice a week, in production only
category: general
topic: debugging
level: senior
tags: [correctness, observability, failure-modes, operations]
time_estimate_min: 9
order: 140
links:
  related: [spring-proxying-interface-vs-class-01]
  deeper: [general-debugging-nobody-can-see-production-01]
---

## Ask

Twice a week or so, a record in production ends up with two fields that contradict each other.
It has never happened in any test environment, nobody can make it happen on demand, and the team
has spent a month adding log lines without catching it. How do you get to the bottom of this?

## Tests

Whether the candidate can design an investigation — a hypothesis, the evidence that would
distinguish it from the alternatives, and a way to capture that evidence — rather than
scattering more logging and waiting.

## Listen for

- Starts from the damaged records themselves: what they have in common, what wrote them, when
- Works backwards from the state to the set of code paths that can produce it at all
- Names candidate mechanisms — two writers racing, a partially applied update, a repeat of a
  message, an older client, a manual change — and says what evidence separates them
- Wants the write path to record who wrote it and in which version, not just that it wrote
- Treats "we cannot reproduce it" as a missing tool, not as a reason to stop
- Asks whether the damage can be detected automatically, so the next one is found in minutes

## Strong signals

- Proposes a check that runs continuously over the data and alerts on the contradiction, and
  treats that as the first deliverable rather than the fix
- Asks whether the contradiction is reachable through the normal path at all, and looks at jobs,
  migrations and support tooling
- Considers containing the damage — refusing the write, or making it recoverable — in parallel
  with finding the cause

## Weak signals

- More logging, in more places, as the whole plan
- Proposes a scheduled job that quietly repairs the rows
- Says it must be a database problem and stops there
- Waits for it to happen again with no change to what will be captured when it does

## Answer bands

### weak

- Adds logging everywhere and waits.
- Blames infrastructure or the framework without a mechanism.
- Suggests repairing the affected rows and closing the ticket.

### mid

- Examines the damaged records for a shared account, time, or entry point.
- Names one plausible mechanism and how they would test it.
- Adds targeted instrumentation on the specific write rather than everywhere.

### senior

- Reduces the space by asking what code can write that combination at all.
- Lists competing mechanisms and, for each, the evidence that would rule it out.
- Builds detection first so the interval between the fault and the investigation collapses.
- Keeps repairing the data and finding the cause as two separate pieces of work.

### lead

- Weighs the cost of the ongoing damage against the cost of the hunt and says who decides.
- Proposes making the bad state impossible to represent, so the class of fault ends rather than
  this instance of it.
- Says what they would stop doing in order to free the people needed, and for how long.

## Follow-ups

- You get one shot at capturing extra information on the write path, and it has to be cheap
  enough to leave on. What do you capture?
  probes: whether they know which facts actually discriminate between their hypotheses
- The team has been at this for a month and morale is low. How do you run the next two weeks?
  probes: timeboxing, dividing the hunt, and the decision to contain rather than solve
- Somebody points out that the two fields never have to be written by the same request. What do
  you do with that?
  probes: whether they reach for a shape of the data in which the contradiction cannot exist
