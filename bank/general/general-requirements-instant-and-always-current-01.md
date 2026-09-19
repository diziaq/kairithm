---
id: general-requirements-instant-and-always-current-01
schema_version: 1
title: A report that is instant, and never out of date
category: general
topic: requirements
level: senior
tags: [consistency, performance, api-design, collaboration]
time_estimate_min: 8
order: 190
---

## Ask

Product asks for a dashboard that pulls figures from three separate systems, is never more than
a second out of date, and loads instantly for every user. They are certain all three parts are
essential. What do you say back to them?

## Tests

Whether the candidate can turn a wish into constraints, find the decision the request is really
serving, and negotiate — rather than refusing outright or silently promising it.

## Listen for

- Asks who looks at this and what they do differently depending on the number
- Tests the freshness requirement against a real decision: what goes wrong if a figure is a
  minute old
- Explains that precomputing is what makes it instant, and that precomputing is what makes it
  stale, in plain language
- Points out that the three systems will disagree with each other anyway, and asks what the
  dashboard should show when they do
- Offers a shape that satisfies the real need — most numbers precomputed, one or two live on
  demand, the age of each shown on screen
- Separates the parts that are expensive from the parts that are cheap, instead of treating the
  request as a single block

## Strong signals

- Asks for the one figure that genuinely has to be current, and treats the rest differently
- Puts the age of the data on the screen so the freshness question becomes visible rather than
  assumed
- Frames the conversation as a choice with prices, not as a refusal, and lets product pick
- Asks what happens to the dashboard when one of the three systems is unavailable, and gets an
  answer before building

## Weak signals

- Says it is impossible and leaves it there
- Agrees to all three and plans to explain the shortfall after it is built
- Goes straight to a technology as the answer without establishing what is needed
- Treats "real time" as a well-defined requirement and never asks what it means here

## Answer bands

### weak

- Rejects the request without offering an alternative.
- Accepts all three requirements and starts designing.
- Names a product or technique as the answer with no question about the need.

### mid

- Asks who uses it and how often the numbers actually change.
- Explains that keeping it fresh and keeping it fast pull against each other, with an example.
- Proposes a refresh interval and asks whether that would be acceptable.

### senior

- Traces the request back to the decision the viewer is making, and sizes the requirement from
  that.
- Prices each of the three demands separately and shows which one is carrying the cost.
- Offers a design where different figures have different ages, and the age is visible.
- Raises what the dashboard does when the three sources disagree or one is down.

### lead

- Runs the conversation so product leaves with a choice they understand and own.
- Commits to a version that can ship in weeks and a way to learn whether the freshness is
  actually needed.
- Says what this costs to run every month, and asks whether the value justifies it.
- Writes down what was agreed, including what was dropped, so it is not relitigated in the demo.

## Follow-ups

- They tell you it has to be instant because the current report takes ninety seconds and people
  have stopped using it. Does that change the problem?
  probes: whether they hear the real complaint behind the stated requirement
- Two of the three systems show a different total for the same day. What does the screen say?
  probes: reconciliation, and whether the requirement was ever well defined
- One of the three is down for an hour. What do the viewers see?
  probes: partial results, and whether availability was part of the requirement at all
