---
id: kafka-dead-letter-unread-topic-01
schema_version: 1
title: Nobody has opened the dead letter topic in six months
category: kafka
topic: dead-letter
level: mid
tags: [failure-modes, observability, operations]
time_estimate_min: 8
order: 48
links:
  related: [spring-web-layer-error-contract-01]
  deeper: [kafka-dead-letter-policy-01]
---

## Ask

A service has been routing records it cannot handle to a dead letter topic for six months. That
topic now holds forty thousand records and nobody has ever read it. The team offers this as
evidence that the pipeline has had no incidents. What is your reaction?

## Tests

Whether the candidate treats a dead letter destination as an operational commitment with a process
behind it, rather than a tidy place to drop records.

## Listen for

- Says forty thousand records quietly set aside is itself the incident
- Asks what is stored next to each record: the failure, where it came from, when, and how many
  attempts it had
- Asks who is alerted, on what threshold, and what the route back into the flow is
- Points out that pushing them all back through now, six months later, may do more harm than the
  original failure
- Asks whether this is one defect repeated forty thousand times or forty thousand different ones

## Expected knowledge

- Records taken out of the main flow are handled by nothing unless somebody builds that
- The topic has its own retention, so the evidence itself can expire

## Strong signals

- Asks whether the original key was kept, because putting a record back without it lands it
  anywhere
- Wants an alert on the rate of arrival rather than on the total
- Asks what forty thousand unhandled events are worth to the business before designing anything

## Weak signals

- Accepts the empty incident log as evidence the pipeline is healthy
- Proposes pushing everything back through immediately
- Cannot say what should be recorded alongside a failed record

## Answer bands

### weak

- Agrees the pipeline has been fine because nothing ever paged anyone.
- Describes the topic as a place records go, with no next step.
- Proposes deleting it to save space.

### mid

- Calls the forty thousand records a silent failure rather than a success.
- Lists what has to travel with a failed record for anyone to act on it later.
- Asks who is alerted, and what the route back into the flow looks like.

### senior

- Asks whether this is one defect repeated or many, and changes the plan on the answer.
- Says why a bulk replay after six months may cause more damage than the original failure.
- Puts an alert on the arrival rate and says what the first responder is meant to do with it.

## Follow-ups

- You decide to push all forty thousand back through the pipeline tonight. What could go wrong?
  probes: stale records, side effects fired again, and what order they land in
- What is written next to a record at the moment it is set aside, so that someone six months later
  can act on it?
  probes: the failure detail, where it came from, the time, the attempt count
- Thirty-nine thousand of them turn out to be the same missing field. Does that change what you
  do?
  probes: whether they separate one defect from many before acting

## Sources

- https://kafka.apache.org/documentation/#connect_errorreporting
- https://kafka.apache.org/documentation/#topicconfigs_retention.ms

## Notes

A dead letter topic is an application or Connect pattern, not a broker feature. Nothing routes
records there or reads them back unless the team writes it.
