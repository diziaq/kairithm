---
id: general-trade-offs-keep-the-list-in-memory-01
schema_version: 1
title: Someone suggests keeping the list in memory
category: general
topic: trade-offs
level: junior
tags: [performance, consistency, failure-modes]
time_estimate_min: 6
order: 20
links:
  deeper: [general-trade-offs-retry-the-payment-01]
---

## Ask

A page is slow, and part of the reason is that it reads the same list of shipping countries out
of the database on every request. A colleague suggests loading it once into memory at startup.
What do you want to know before you agree, and what could that change break?

## Tests

Whether the candidate can name the cost of a change they have just been handed the benefit of,
instead of accepting it because it is obviously faster.

## Listen for

- Asks how often the list actually changes, and who changes it
- Works out what happens after somebody edits it — the running process keeps serving the old one
- Asks whether the page is slow because of this read at all, or whether that is an assumption
- Notices that several running copies of the service will disagree with each other for a while
- Asks how big the data is and whether it is the same for every user
- Proposes a way to refresh it, and accepts that the way costs something too

## Weak signals

- Agrees straight away because reading from memory is faster
- Cannot say what happens when the underlying data changes
- Proposes restarting the service when the list is edited, and does not see that as a cost
- Reaches for a large caching product for a list of countries

## Answer bands

### weak

- Accepts the suggestion with no question, on the grounds that memory is fast.
- Cannot describe any situation in which the change would cause a problem.
- Says the database is slow without knowing whether this query is the reason.

### junior

- Asks how often the list changes and how quickly an edit needs to be visible.
- Notices that the copy in memory will go out of date.
- Suggests refreshing it periodically or restarting after a change.

### mid

- Asks for evidence that this read is a meaningful part of the page time before changing
  anything.
- Points out that separate copies of the service will hold different versions at the same time.
- Names who is hurt by a stale list and for how long, and lets that set the refresh interval.
- Compares doing nothing, refreshing on a timer, and invalidating on write, with costs for each.

## Follow-ups

- Two hours after an admin adds a country, a customer still cannot pick it. Who finds that out,
  and how?
  probes: whether staleness has a visible owner and a bound, or is just hoped away
- The list is edited about twice a year. Does that change your answer?
  probes: whether the rate of change drives the decision rather than taste
- You measure the page and this query is four milliseconds out of nine hundred. Now what?
  probes: willingness to say no to a change that is real but irrelevant
