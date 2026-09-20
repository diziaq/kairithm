---
id: kafka-schema-evolution-field-split-01
schema_version: 1
title: Splitting one field into two on a live topic
category: kafka
topic: schema-evolution
level: senior
tags: [api-design, operations, correctness]
time_estimate_min: 10
order: 66
links:
  related: [microservices-api-evolution-deleting-a-field-nobody-uses-01]
---

## Ask

A topic carries customer records with a single `name` field. Product wants it split into
`first_name` and `last_name`. There are nine consumers, three of which belong to teams you do not
control, and the topic keeps ninety days of records. How do you do it?

## Tests

Whether the candidate can sequence a change that no single compatibility rule permits, across
teams they cannot instruct.

## Listen for

- Says this is not a plain addition, so no single deploy is safe and it has to be staged
- Proposes writing both shapes for a period, then moving the readers, then dropping the old field
- Asks how long the old shape must survive, and ties it to the ninety days plus the slowest reader
- Says the teams they do not control set the schedule, and asks how they will know all nine have
  moved
- Considers a parallel topic with a cutover as the alternative, and says when that is cheaper

## Expected knowledge

- A change that drops or renames a field cannot be read by anything expecting the old one
- Consumers ship on their own schedules, and some may be reading from far behind the end

## Strong signals

- Names how they would observe that the old field is no longer being read, rather than asking
  teams whether they are done
- Points out that a consumer working through ninety-day-old records sees the old shape long after
  the producer stopped writing it
- Says what they would do if one of the three teams never moves at all

## Weak signals

- Proposes a coordinated release across nine teams
- Drops the old field in the same change that adds the two new ones
- Has no way of knowing when it is safe to finish

## Answer bands

### mid

- Says both shapes have to be present at the same time for a while.
- Sequences it: producer first, readers next, removal last.

### senior

- Puts a number on how long the old field must stay, from how long records are kept and how far
  behind a reader may be.
- Says how they would establish that nobody reads the old field any more.
- Names the parallel topic alternative and the condition that would make them choose it.

### lead

- Plans for a team that never migrates, and says what happens to them.
- Gives the final removal an owner and a trigger, so it does not sit unfinished for years.
- Weighs carrying both fields indefinitely against forcing the change on other teams.

## Follow-ups

- One of the three teams you do not control has not replied in six weeks. What do you do?
  probes: whether their plan depends on cooperation they cannot compel
- A consumer is restarted with its position moved back to the start of the ninety days. What does
  it see?
  probes: that stored records keep the shape they were written in, whatever the producer does now
- Six months from now, is the old field gone?
  probes: whether they built a trigger for the last step or left it to goodwill

## Sources

- https://avro.apache.org/docs/current/specification/#schema-resolution
- https://kafka.apache.org/documentation/#topicconfigs_retention.ms
