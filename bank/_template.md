---
# Copy this file to bank/<category>/<id>.md, then edit every field.
# Full field reference: docs/question-format.md
# Check your work:      .venv/bin/python -m app.validate

id: category-topic-short-slug-01
schema_version: 2
title: A short label for lists and navigation
category: java              # the directory this file lives in, e.g. java, database, kafka
topic: concurrency          # the narrower area inside the category
level: mid                  # junior | mid | senior | lead — the seniority the QUESTION aims at
tags: [tag-one, tag-two]
time_estimate_min: 5
order: 100                  # optional; position in sequential mode
links:
  deeper: []                # harder card, same topic
  shallower: []             # foundational card, same topic
  related: []               # same level, adjacent topic
  prerequisite: []          # should be understood first
---

## Ask

The only text read aloud. Everything below this section is for the interviewer.

## Tests

One sentence: what capability this card actually probes.

## Ideal minimal answer

The least a candidate can say and still have answered. One or two sentences, under seventy
words. Not the best answer — the floor. Write it so two interviewers would agree whether an
answer cleared it.

## Listen for

- The concrete thing whose presence means the candidate understands it
- The second one

## Expected knowledge

- Optional. What the candidate is expected to already have.

## Strong signals

- Optional. Not needed to pass, but indicates depth or real production experience.

## Weak signals

- Optional. The memorised, shallow or actively wrong answers you hear often.

## Answer bands

Include only the bands that are meaningful for this card. Describe observable behaviour —
what the candidate says or does — never a verdict. "Excellent understanding" is rejected by
the validator.

### weak

- Recites a definition with no example.

### junior

- States the basic definition correctly and gives one working example.

### mid

- Explains the main trade-offs and names a failure case from experience.

### senior

- Explains the underlying mechanism, not the API surface.
- Discusses what happens under load or during a failure.

### lead

- Chooses between alternatives from stated constraints.
- Explains the maintenance cost of each option.

## Follow-ups

Two to four. Describe the situation; do not name the concept. If a follow-up contains a term
from `Listen for`, `Expected knowledge` or a band, it hands over the answer.

- The situation you describe when the first answer is on the right track but thin
  probes: interviewer-only note on what this is meant to surface — never read aloud
- The situation you describe when the first answer is strong
  probes: what you are testing the ceiling with

## Notes

Optional. Interviewer-only context, caveats, common misconceptions.

## Sources

- Optional. Links, where a claim on this card is not obvious.
