---
id: general-debugging-partial-fix-01
schema_version: 2
title: The fix cut the errors but did not end them
category: general
topic: debugging
level: mid
tags: [correctness, observability, failure-modes]
time_estimate_min: 7
order: 80
links:
  related: [spring-transactions-self-invocation-01]
  deeper: [general-debugging-corruption-no-repro-01]
---

## Ask

Last week you shipped a fix for a bug that was throwing about a thousand errors a day. Since the
deploy it throws eighty a day, and the ones that are left look identical in the logs to the ones
that went away. What do you do next?

## Tests

Whether the candidate can tell a partially effective fix from a second cause with the same
symptom, and reasons from evidence instead of applying the same fix harder.

## Ideal minimal answer

Treats the surviving eighty as a separate question, says an identical log line can be produced
by more than one path, and compares those failures against the ones that stopped on concrete
dimensions — account, region, client version — with a stated hypothesis and the evidence that
would confirm it.

## Listen for

- Treats the remaining eighty as a separate question rather than as leftovers of the first
- Asks what the fix actually changed and which of the thousand it could account for
- Pulls a sample of the surviving failures and compares them against the ones that stopped
- Looks for what the survivors have in common: one account, one region, one code path, one
  version of a client
- Considers that the original diagnosis was right for most cases and wrong for the rest

## Weak signals

- Calls it a ninety-two per cent win and moves on
- Declares the same cause and asks for the fix to be applied in more places
- Assumes the errors are stale, or a caching artefact, without checking timestamps

## Answer bands

### weak

- Treats the drop as proof the diagnosis was right and the rest as noise.
- Proposes suppressing or downgrading the remaining log lines.
- Cannot say how they would tell the two groups apart.

### junior

- Wants to look at examples of the errors that are still happening.
- Checks the timestamps to confirm they are after the deploy, not before.
- Asks whether the fix went out everywhere it was supposed to.

### mid

- States a hypothesis for why some cases survived and says what evidence would confirm it.
- Compares the surviving failures on concrete dimensions, once asked what they have in common,
  rather than by their message.
- Recognises that an identical log line can be produced by more than one path.
- Says what they would add to the error record so the next split is visible without this work.

### senior

- Reasons about how the first diagnosis was arrived at and what it was never able to exclude.
- Asks whether the eighty are a smaller version of the same fault or a rarer, worse one, and
  lets the answer set the priority.
- Notices without being asked that a partial drop can also come from traffic shifting rather than
  from the change, and checks that first.

## Follow-ups

- The eighty a day are all from the same two customers, both of them large. Does that change
  what you do?
  probes: whether volume or blast radius drives the priority, and whether they spot a shared
  input rather than a shared code path
- A colleague suggests wrapping the call in a retry so the failures stop appearing. What do you
  say?
  probes: hiding a symptom versus fixing a cause; whether a repeat is safe here at all
- The deploy also contained four other changes from other people. How confident are you that
  your change is what moved the number?
  probes: attribution, and whether they treat a correlated deploy as proof
