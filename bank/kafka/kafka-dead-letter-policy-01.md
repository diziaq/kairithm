---
id: kafka-dead-letter-policy-01
schema_version: 1
title: Deciding what twenty teams are allowed to set aside
category: kafka
topic: dead-letter
level: lead
tags: [failure-modes, api-design, operations, correctness]
time_estimate_min: 12
order: 86
links:
  related: [microservices-distributed-transactions-compensation-cannot-undo-01]
---

## Ask

You are writing the rule for a platform used by twenty teams: which failures may a consumer push
out of the main flow into a dead letter topic, and which must stop the pipeline instead? Twenty
teams will follow whatever you write. How do you draw the line?

## Tests

Whether the candidate can turn error handling into a rule other teams can apply unsupervised, and
defend where the line sits.

## Listen for

- Splits failures by cause: a record that can never succeed, a dependency that is briefly down,
  and a defect in the consumer's own code
- Says a dependency being down must not push anything aside, because every record would go
- Says a bad deploy must stop the flow, because pushing valid records aside hides the defect
- Requires that anything set aside is counted, alerted on above a rate, and can be put back
- Asks what the data is worth: a page view and a payment do not get the same rule

## Expected knowledge

- A consumer that keeps failing on one record blocks its partition
- Taking a record out of the main flow takes it out of sequence for its key

## Strong signals

- Writes the rule so a team can apply it without a meeting, naming classes of error rather than
  listing symptoms
- Insists the rate is a first-class signal with a named owner, not a log line
- Says what happens when the rule turns out to be wrong, and how it gets revised

## Weak signals

- Gives a blanket rule such as "three attempts then set it aside", with no reference to why it
  failed
- Does not distinguish an outage in a dependency from a single bad record
- Leaves the topic with no owner and no alert

## Answer bands

### mid

- Separates a record that will never succeed from a dependency that is briefly unavailable.
- Says anything set aside needs an alert and a route back.

### senior

- Adds the case of the consumer's own defect, and says pushing those aside hides a rollback that
  should have happened.
- Sets the rule by the cause of the failure rather than by a count of attempts.
- Notes that anything set aside has left the sequence for its key.

### lead

- Writes a rule twenty teams can apply without asking, and says how a team appeals against it.
- Ties how strict the rule is to what the records are worth, and names who decides that.
- Says how the rule is watched across teams, and what would trigger a revision.

## Follow-ups

- One team's database is down for ninety minutes and their rule pushes every record out of the
  main flow. What do you tell them?
  probes: that a whole-dependency outage must not be drained sideways
- A bad deploy makes a consumer throw on every perfectly valid record for ten minutes. Where
  should those records be?
  probes: that a defect in the code must stop the flow rather than empty the topic into a siding
- One of the twenty teams handles payments and one handles page views. Should they follow the same
  rule?
  probes: whether the value of the data sets how strict the rule is

## Sources

- https://kafka.apache.org/documentation/#connect_errorreporting
