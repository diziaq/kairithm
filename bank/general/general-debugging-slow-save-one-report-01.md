---
id: general-debugging-slow-save-one-report-01
schema_version: 2
title: One customer says a save took thirty seconds
category: general
topic: debugging
level: junior
tags: [observability, performance, failure-modes]
time_estimate_min: 6
order: 10
links:
  deeper: [general-debugging-partial-fix-01]
  related: [microservices-observability-request-lost-across-hops-01]
---

## Ask

A customer writes in to say that saving their profile took about thirty seconds yesterday
afternoon. You try it now and it comes back in a fifth of a second. You have the logs, the
dashboards and the code in front of you. What do you do?

## Tests

Whether the candidate narrows a vague report down to one specific request and looks at evidence
before forming a theory about the cause.

## Ideal minimal answer

Asks for the time and the account so that one request can be found in the logs, looks at a
response-time graph for that window as well as the log line, and checks whether anybody else was
affected in the same period — before naming a cause.

## Listen for

- Asks when it happened, which account, and whether it was once or repeatedly
- Goes looking for that particular request in the logs before proposing a cause
- Compares the graphs for that window against a normal afternoon
- Separates "the save was slow" from "the screen was slow" and asks which the user saw

## Weak signals

- Lists plausible causes without asking a single question about the report
- Concludes there is no fault because it is fast now
- Asks the customer to try again and closes the ticket when it works
- Tells how a slow save was tracked down at a previous job and never says what to do with this
  report

## Answer bands

### weak

- Names possible causes straight away without asking anything about the report.
- Treats the fast response today as proof that nothing happened.
- Blames the customer's connection with nothing to support it.

### junior

- Asks for the time and the account so the request can be found in the logs.
- Looks at a response-time graph for that window as well as the log line.
- Checks whether anyone else was affected in the same period.

### mid

- Splits the thirty seconds across the stages of the path and picks where to look first.
- Distinguishes one slow request from a period when everything was slow, and says what each
  would imply.
- Names what the logs do not currently record without being asked, and what they would add so
  the next report is answerable.

## Follow-ups

- The logs for that afternoon are already gone and nothing is left from that window. What now?
  probes: whether they can still make progress from aggregates, and whether they think about
  log retention before they need it
- You find four more complaints, all between two and three in the afternoon, all on a Tuesday.
  What does that tell you?
  probes: reading a pattern in time, and connecting it to scheduled or batch work
- The customer wants an answer today and you do not have one yet. What do you send them?
  probes: whether they state an open investigation honestly instead of inventing a cause
