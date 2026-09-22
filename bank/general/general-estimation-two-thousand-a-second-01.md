---
id: general-estimation-two-thousand-a-second-01
schema_version: 2
title: Two thousand a second, by lunchtime
category: general
topic: estimation
level: mid
tags: [capacity, performance, requirements]
time_estimate_min: 7
order: 640
links:
  deeper: [general-estimation-date-for-unknown-system-01]
  related: [microservices-scalability-autoscaled-into-database-01]
---

## Ask

Product say the launch will bring two thousand requests a second to one endpoint. That endpoint
averages two hundred and fifty milliseconds, and each instance runs fifty request threads. They
want to know how many instances to buy, and they want it by lunchtime. What do you tell them?

## Tests

Whether the candidate will do the arithmetic out loud, and then say what the resulting number does
and does not mean.

## Ideal minimal answer

Two thousand a second at a quarter of a second each is five hundred in flight; at fifty threads an
instance that is ten instances fully occupied, so fifteen to have any room. And it is a starting
point: the quarter of a second gets worse as the queues form, and the database behind fifteen
instances will run out before the threads do. I would test it.

## Listen for

- Does the multiplication out loud: two thousand times a quarter of a second is five hundred at
  once, divided by fifty is ten instances
- Refuses to run at ten, because ten is every thread busy every moment, and gives a figure with
  room in it and a reason for the size of the room
- Says the two hundred and fifty milliseconds is not a constant: as the threads fill, requests
  wait to be picked up and the figure the estimate was built on grows
- Names something downstream that gives way before the instance count does — connections to the
  database, a rate limit at a third party, a shared cache — and does the second multiplication
- Asks whether two thousand is the peak or the average, and what the first five minutes look like
- Asks where the two thousand came from and what happens to the estimate if it is wrong by three
  times either way
- Gives product a number with the assumptions attached rather than a bare figure, and says what
  would replace it
- Says what measurement settles it — driving load at the endpoint until something breaks — and how
  long that takes to arrange

## Expected knowledge

- How many requests are in progress at once follows from the rate and how long each one takes
- A thread is occupied for the whole request, including time spent waiting on something else
- Every instance holds its own share of any pooled resource behind it

## Strong signals

- Asks for the spread of response times, not just the average, before trusting the figure
- Points out that the average will itself change once the endpoint is under real load, so the
  estimate is circular until measured
- Multiplies the instance count by the per-instance connection pool and checks it against the
  database limit without being asked
- Says what to do if the honest answer does not arrive by lunchtime, and what to give product
  instead

## Weak signals

- Produces a number with no working shown
- Multiplies the request rate by the instance count, or divides by the wrong figure, and does not
  sanity-check the result
- Says it will autoscale, with no figure and no ceiling
- Gives the arithmetic and stops, treating the answer as the deliverable
- Recounts a previous launch instead of answering about this one

## Answer bands

### weak

- Guesses a number, or says it depends, without attempting the arithmetic.
- Gets the arithmetic wrong and does not notice the result is implausible.
- Treats the stated average as a fact about the system under load.

### junior

- Does the multiplication correctly and arrives at ten.
- Reports ten as the answer.
- Does not add room, and does not question either input.

### mid

- Gets to ten, adds room, and can say what the room is for.
- Says the quarter of a second will grow under load, once asked what could make the figure wrong.
- Names one thing downstream that would break before the instances did.
- Gives product the number together with what it assumes.

### senior

- Volunteers which assumption is most likely to be wrong and which limit is hit first.
- Does the second multiplication — instances against per-instance connections — and checks it
  against a real ceiling.
- Asks whether the two thousand is peak or average and how quickly it arrives.
- Proposes the measurement that replaces the estimate, says what it costs, and gives product
  something usable before it is done.

## Follow-ups

- They tell you the two hundred and fifty is the average and one call in a hundred takes two
  seconds. Does your figure change?
  probes: the tail holding threads far longer than the average suggests
- You buy fifteen, and each one keeps twenty open connections to the database. Anything you want
  to check?
  probes: a per-instance number multiplied by a fleet against a fixed ceiling behind it
- The two thousand arrives in the first minute, not spread over the hour. What do you want in
  place before that minute?
  probes: warm-up, how long new capacity takes to arrive, and turning work away rather than dying
- Marketing hear fifteen and write it into the plan. What exactly did you say to them?
  probes: whether the assumptions travel with the number or get stripped off

## Sources

- https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing
- https://sre.google/sre-book/handling-overload/
- https://sre.google/workbook/implementing-slos/

## Notes

The arithmetic is the easy half and the card is not about getting ten. It is about what the
candidate says next: that the average response time is an input which changes under the load being
planned for, and that the first thing to break is behind the endpoint rather than in front of it.
A candidate who produces fifteen with the assumptions attached has the card; one who produces
fifteen as a fact has not.
