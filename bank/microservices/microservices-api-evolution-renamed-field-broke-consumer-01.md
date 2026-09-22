---
id: microservices-api-evolution-renamed-field-broke-consumer-01
schema_version: 2
title: A renamed field and a sev-2 from a team you have never met
category: microservices
topic: api-evolution
level: junior
tags: [api-design, correctness, testing, operations]
time_estimate_min: 6
order: 130
links:
  deeper: [microservices-api-evolution-deleting-a-field-nobody-uses-01]
---

## Ask

You rename a field in your JSON response from `customerId` to `customer_id` and deploy on
Tuesday. On Thursday a team you have never met raises a sev-2: their nightly job has been writing
nulls into their reports for two days. What should have happened instead?

## Tests

Whether the candidate recognises a change that is invisible to their own tests as a breaking
change to somebody else, and can describe a safe way to make it.

## Ideal minimal answer

Renaming the field is a breaking change even though my build stayed green: the consumer looked
for `customerId`, got nothing, and wrote null. I should have added `customer_id` alongside it,
told the consuming teams, and removed the old name later.

## Listen for

- Removing or renaming anything in a response is a breaking change, even though nothing in their
  own build failed
- The safe sequence: add the new field, keep the old one, tell people, watch whether the old one
  is still read, then remove it
- Their tests could not have caught it, because the expectation lives in the other team's code
- Two days passed before anyone noticed, because the consumer was a nightly job — the damage was
  already in someone's reports
- Has some answer to "who calls this endpoint", even if the honest answer today is nobody knows

## Expected knowledge

- A caller parses the payload it was written against, and an absent field usually reads as empty
- Publishing a response makes its shape part of a contract, whether or not one was written down

## Strong signals

- Asks how the other team's data gets repaired, not only how to avoid it next time
- Notices that a consumer which fails loudly would have been better than one that wrote nulls

## Weak signals

- "They should have handled it" and nothing further
- Proposes a version number for the whole API as the only answer
- Says the tests should have caught it, without saying whose tests
- Recounts how a similar break was found at a previous job and never says what should have
  happened on Tuesday

## Answer bands

### weak

- Does not see why renaming a field is different from any other change.
- Blames the other team for not keeping up.
- Suggests announcing it in a chat channel as the whole process.

### junior

- Calls it a breaking change and would have added the new name alongside the old one.
- Says the other team needed warning and time.
- Has a rough idea that the old name gets removed later.

### mid

- Describes a full sequence with a way to observe whether anyone still reads the old name.
- Says where a check would live so that this fails in a pipeline rather than in production.
- Raises the two days of corrupted reports unasked, as work that also has to be done.

## Follow-ups

- Your build was green. Whose build should have gone red?
  probes: where the expectation lives, and consumer-side verification
- Before you touch this response again, how do you find out who reads it?
  probes: access data, gateway records, asking around; whether they have any plan at all
- Adding a field rather than renaming one — can that break anybody?
  probes: strict parsers, schema validation, tolerance of unknown fields
