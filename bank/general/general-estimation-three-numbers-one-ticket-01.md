---
id: general-estimation-three-numbers-one-ticket-01
schema_version: 1
title: Half a day, three days, two weeks — same ticket
category: general
topic: estimation
level: mid
tags: [collaboration, requirements, delivery]
time_estimate_min: 7
order: 135
links:
  deeper: [general-estimation-date-for-unknown-system-01]
  related: [general-requirements-one-line-ticket-01]
---

## Ask

In planning, three engineers estimate the same ticket. One says half a day, one says three days,
one says two weeks. None of them has said anything obviously wrong, and the room is waiting for a
number. What do you do with that?

## Tests

Whether the candidate reads a spread of estimates as a disagreement about what the work is, and
resolves the disagreement instead of doing arithmetic on the numbers.

## Listen for

- Treats the spread itself as the finding: three people have priced three different pieces of work
- Asks each of them what they pictured doing, and goes after the item the longest number can see
  and the shortest one cannot
- Checks they agree on what finished means here — the rows already in the table, the tests, the
  review, the release, the flag being taken out afterwards
- Refuses to average, and can say why a mean of three different scopes is not a number about
  anything
- Splits the ticket so the part all three agree on is separated from the part they do not
- Names what would have to be true for the shortest number to hold, and how cheaply that could be
  checked
- Puts the thing they disagreed about onto the ticket in writing, so it survives the meeting

## Strong signals

- Asks whether the person with the longest number has worked on this part before, and what
  happened that time
- Notices somebody moving their number after hearing the others, and goes back to them
- Is willing to leave the meeting without a single number, and says exactly what will produce one
- Says what the team does if the longest view turns out to be the right one — cut scope, add
  people, or move the date — and raises it now rather than later

## Weak signals

- Averages the three, or takes the middle one
- Takes the smallest because the team should be ambitious, or the largest to be safe
- Records whatever the most experienced person in the room said and moves on
- Splits the difference to end the meeting

## Answer bands

### weak

- Averages the numbers, or takes the middle one, and moves to the next ticket.
- Records the number given by the most senior person in the room.
- Treats the spread as a difference in how fast the three of them work.

### junior

- Asks all three to say how they arrived at their numbers.
- Notices they may be describing different amounts of work.
- Takes the larger number on the grounds that something is clearly unaccounted for.

### mid

- Asks what each person pictured doing, and chases the specific item one of them saw and another
  did not.
- Checks that all three mean the same thing by finished, naming what that includes here.
- Splits the ticket so the agreed part is separate from the contested part.
- Writes down what the three of them disagreed about instead of leaving it in the room.

### senior

- Says the number is worth nothing until the disagreement is resolved, and is willing to say that
  to the room.
- Goes back to whoever revised their number after hearing the others, and asks what they dropped.
- States what would have to be true for the smallest number, and proposes the cheapest way to find
  that out before anyone commits.
- Raises now what happens if the largest view is right, rather than letting it arrive as a slip.

## Follow-ups

- The largest number comes from the only person who has worked in that part of the code before.
  Does that settle it?
  probes: one person's memory as evidence, and whether they make the reasoning checkable by others
- You press, and the smallest number turns out not to include moving the rows that are already in
  the table. Was that person wrong?
  probes: scope versus speed; whether anyone had agreed what finished means
- The meeting has run over and the room wants a number so it can move on. What do you say?
  probes: whether they will report an unresolved question rather than manufacture agreement
- The same three people, the same spread, on the next four tickets. What does that tell you?
  probes: a pattern that points at how the work is written down rather than at the people

## Notes

The interesting move is refusing the arithmetic. A candidate who asks what each person pictured
has the card; one who then asks what finished means here has more. If they go to bounded
investigation work and dates for a stakeholder, that is the lead card on this topic — note it and
bring them back to the three numbers in front of them.
