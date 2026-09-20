---
id: kafka-schema-evolution-required-field-01
schema_version: 1
title: One new field stops a consumer over the weekend
category: kafka
topic: schema-evolution
level: mid
tags: [api-design, correctness, failure-modes, testing]
time_estimate_min: 8
order: 50
links:
  deeper: [kafka-schema-evolution-field-split-01]
---

## Ask

A producer team adds one new field to the event they publish and deploys on Friday afternoon. On
Monday a consumer that nobody has touched in months is failing on every record — it binds the
payload straight onto a class and refuses anything it was not told about. The producer team says
the change was additive and therefore safe. Who is right, and what should the rule have been?

## Tests

Whether the candidate can reason about two independently deployed sides of one topic, tell the
two directions of compatibility apart, and say what has to hold for either side to ship alone.

## Listen for

- Says an old reader handed new data only breaks when its decoding step refuses what it does not
  recognise; a format that resolves each record against the shape it was written with drops the
  extra quietly
- Says the opposite direction is the one where a fallback value matters: a reader that expects the
  field, handed records written before it existed, has nothing to put there
- Points out the consumer also has to work through the months of records already sitting on the
  topic, which stay in the shape they were written in
- Says the rule belongs somewhere that mechanically refuses the change, not in a code review
- Asks whether anybody even knows who reads this topic

## Expected knowledge

- A reader and a writer of one topic ship on their own schedules, and either may move first
- Whether an unrecognised field is an error or is ignored is a property of the encoding and of how
  the decoding side is set up, not of the topic
- An addition that carries a fallback value is the shape that survives both directions

## Strong signals

- Asks how long records are kept, because that decides how long the old shape has to keep working
- Notices that rolling the producer back does not undo the records already written
- Asks which direction is actually being enforced anywhere, and where that check runs
- Separates a consumer that survived by accident from a change that was genuinely safe

## Weak signals

- Says the consumer team should just update their code, with nothing to stop the next one
- Treats the fix as redeploying both sides at the same moment
- Calls any addition safe without asking what happens to records already written
- Cannot say which side of the change is allowed to move first

## Answer bands

### weak

- Says the consumer team should update their code, and stops there.
- Cannot say why an added field would break a reader at all.
- Suggests both teams coordinate every release.

### mid

- Says an addition is only safe in one direction, and names which direction failed here.
- Points out that how the consumer decodes a record is what decided the outcome, not the topic.
- Says the topic still holds records in the old shape that have to keep working.

### senior

- Gives the rule for the other direction too, and says what a reader needs for a field the older
  records never carried.
- Puts the check somewhere that rejects the change before it ships, and says where that runs.
- Points out that rolling the producer back leaves the offending records exactly where they are.

## Follow-ups

- They roll the producer back on Monday morning. Is the consumer fine now?
  probes: that the records already written keep the shape they were written in
- The consumer team instead ships a class that has the new field on it, and it now fails on
  everything written before Friday. What did they miss?
  probes: the other direction, and that there is nothing to fill the field with for old records
- How would you stop this happening again without asking every team to be careful?
  probes: a check that runs, rather than discipline

## Sources

- https://avro.apache.org/docs/current/specification/#schema-resolution
- https://kafka.apache.org/documentation/#topicconfigs_retention.ms

## Notes

Get the direction right, because this is commonly stated backwards. Under a schema-resolving
format such as Avro, a reader using its old schema against data written with a newer one ignores
the field it does not know about — so the failure described here is a property of the
deserialiser in use, a strict binding that rejects unknown properties, rather than of the
addition itself. A default matters in the *other* direction: a reader whose schema has the field,
reading records written before it existed, needs a default to fill in or resolution fails.
Compatibility enforcement is a schema registry feature and a separate component; the broker does
not police record shape.
