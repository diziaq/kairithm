---
id: general-debugging-nobody-can-see-production-01
schema_version: 1
title: A week per bug, and most of it spent working out what production did
category: general
topic: debugging
level: lead
tags: [observability, operations, ownership, failure-modes]
time_estimate_min: 9
order: 215
links:
  related: [sap-jco-troubleshooting-oncall-without-sap-access-01]
---

## Ask

Every hard bug in your area this year has taken more than a week, and most of that week goes on
working out what production was actually doing. Logs are sampled, nobody is allowed to copy
customer data into a test environment, and a single request crosses four teams' services. You
have one engineer for a quarter. What do you spend it on, and what are you signing everyone
else up for?

## Tests

Whether the candidate can choose one investment in how the system is investigated, from a fixed
budget and constraints they cannot remove, and can say what it commits other teams to keeping
alive afterwards.

## Listen for

- Goes back over the recent investigations and asks which step of the week was actually the
  expensive one
- Separates not having the facts at all from having them in four places that cannot be lined up
- Says what a request would have to carry for four sets of records to be joined, and asks what
  adopting that costs each of the four teams
- Prices the running cost as well as the build: what is kept, for how long, and who keeps it
  working when the code changes
- Takes the rule about customer data as fixed and designs within it rather than seeking an
  exception
- Picks one thing and names what the quarter is deliberately not buying
- Says how they would tell, three months later, whether investigations got shorter

## Strong signals

- Measures the current cost — how many investigations, how many hours each — before spending the
  quarter
- Prefers something that can be turned up for one customer or one request over something paid
  for on every request
- Names the outcome where one team adopts it and the other three do not, and says what would
  make it stick
- Says who owns the result after the quarter ends and what happens when that person moves on

## Weak signals

- Buys a product and treats the decision as finished at the purchase
- Asks for everything to be recorded everywhere, with no view of the bill or of who maintains it
- Proposes working from real customer records after being told that is not available
- Spends the quarter on the bug currently in front of the team and changes nothing about the
  next one

## Answer bands

### mid

- Names one concrete gap and proposes filling it.
- Says what should be written on every failure so the next investigation starts with something.
- Asks the other three teams to do the same thing.

### senior

- Uses the last few investigations to find the missing fact that cost the most time, and aims
  the quarter at that one.
- Works within the restriction on customer records instead of treating it as negotiable.
- States what the change costs to run each month and what it costs the other teams to keep
  working as their code changes.
- Defines what they would measure in three months to know it was worth the quarter.

### lead

- Compares the options out loud and says why one is worth a quarter and the others are not.
- Names the long-term obligation the other teams are taking on, and gets it agreed rather than
  assumed.
- Makes the new capability the path of least resistance for the next service, so it does not
  decay back within a year.
- Says what the team stops doing to release the engineer, and who owns the result afterwards.

## Follow-ups

- Two of the four teams pick your change up in the first fortnight. Five months later the other
  two still have not. How much of the value did you get?
  probes: whether take-up was planned and owned, or assumed to follow from shipping
- The bill for what you are now keeping comes back larger than the cost of the engineer who
  built it. What do you do?
  probes: whether they can trade completeness against cost — everything always, versus more on
  demand, versus less kept for less time
- A year later someone who joined last month is handed the same kind of bug. What is different
  about their first two days?
  probes: whether the investment changed the normal path for everybody, or helped once
