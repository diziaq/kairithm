---
id: kafka-schema-evolution-required-field-01
schema_version: 1
title: One new field stops a consumer over the weekend
category: kafka
topic: schema-evolution
level: mid
tags: [api-design, correctness, testing]
time_estimate_min: 8
order: 50
links:
  deeper: [kafka-schema-evolution-field-split-01]
---

## Ask

A producer team adds one new field to the event they publish and deploys on Friday afternoon. On
Monday a consumer that nobody has touched in months is failing to deserialise every record. What
did they get wrong, and what should the rule have been?

## Tests

Whether the candidate can reason about two independently deployed sides of one topic, and name
what has to hold for a change to be safe to ship alone.

## Listen for

- Asks whether the new field has a default, and says a required field without one breaks anybody
  still reading the old shape
- Separates the two directions: an old reader handed new data, and a new reader handed old data
- Points out the consumer also has to read the months of records already sitting on the topic
- Says the rule belongs somewhere that mechanically refuses the change, not in a code review
- Asks whether anybody even knows who reads this topic

## Expected knowledge

- A reader and a writer of one topic ship on their own schedules
- Adding a field with a default is the safe shape of an addition

## Strong signals

- Asks how long records are kept, because that decides how long the old shape has to keep working
- Notices that rolling the producer back does not undo the records already written
- Asks which direction of compatibility the topic is actually configured to enforce

## Weak signals

- Says the consumer team should just update their code, with nothing to stop the next one
- Treats the fix as redeploying both sides at the same moment
- Cannot say which side of the change is allowed to move first

## Answer bands

### weak

- Says the consumer team should update their code, and stops there.
- Cannot say why a new field would break a reader at all.
- Suggests both teams coordinate every release.

### mid

- Names the missing default as the cause, and says what a safe addition looks like.
- Distinguishes an old reader on new data from a new reader on old data.
- Says the topic still holds records in the old shape that have to keep working.

### senior

- Puts the rule somewhere that rejects the change before it ever ships.
- Asks how long the old shape has to stay readable, and ties that to how long records are kept.
- Points out that rolling the producer back leaves the offending records exactly where they are.

## Follow-ups

- They roll the producer back on Monday morning. Is the consumer fine now?
  probes: that the records already written keep the new shape
- Next quarter they want to drop a field they believe nobody uses. What has to be true first?
  probes: the other direction, and how you establish that nobody reads it
- How would you stop this happening again without asking every team to be careful?
  probes: a check that runs, rather than discipline

## Sources

- https://avro.apache.org/docs/current/specification/#schema-resolution
