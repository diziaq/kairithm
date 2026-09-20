---
id: sap-jco-connection-pooling-logons-despite-pool-01
schema_version: 1
title: Pooling is on and the logons keep coming
category: sap-jco
topic: connection-pooling
level: mid
tags: [performance, configuration, operations, failure-modes]
time_estimate_min: 7
order: 45
links:
  deeper: [sap-jco-connection-pooling-capacity-across-nodes-01]
---

## Ask

One service, one instance, one named destination held for the lifetime of the application —
nothing builds a destination per call. `jco.destination.peak_limit` is 50 and
`jco.destination.pool_capacity` is 1. You run a load test at forty requests in flight, and Basis
come back saying they are seeing thousands of logons an hour. Walk me through what those two
numbers are doing to your connections.

## Tests

Whether the candidate can read the two pool numbers as a shape — how much work may be in flight,
and how much survives between calls — and predict from them what a single instance does to the
SAP side at a given load.

## Listen for

- The two numbers answer different questions: one is how much work may be in flight at once, the
  other is how much is kept alive when nobody is using it
- At forty requests in flight the first number is not what is biting; the second is what decides
  how much of that work has to log on from nothing
- Keeping one connection alive means thirty-nine of the forty are closed as soon as they are
  handed back, and the next wave logs on again
- The remedy is sizing the second number against the load the service actually sustains, not
  raising the first
- Knows a connection kept alive is not free either: it occupies something on the far side whether
  or not anybody is using it, which is why the number is agreed rather than simply maximised
- Would ask for the sustained load and the shape of the traffic before naming a number
- Says a destination holding nothing between calls is the same waste as building a new one each
  time, arrived at by a different route

## Expected knowledge

- One of the two numbers caps how much may be in use at once; the other caps how much is kept
  alive while nobody is using it
- An idle count of zero turns pooling off altogether
- A logon is work for the far side: authentication, a user session set up and torn down

## Strong signals

- Asks for the logon rate and the distribution of load before proposing a number, instead of
  doubling whatever is there
- Points out that what is held open is a session somebody on the SAP side is carrying, so the
  number belongs in a conversation with them
- Knows a connection that goes unused long enough is dropped anyway, so a pool warms and cools
  with the traffic and a number chosen for the peak is not held all day
- Asks what the traffic actually looks like — a steady forty, or forty for ten seconds an hour —
  because the two want different numbers

## Weak signals

- Raises the first number because fifty sounds small
- Treats the two as one knob under two names
- Sets the idle count to zero to save memory
- Blames the network, or the load generator, for the logon volume

## Answer bands

### weak

- Cannot say which of the two numbers is which.
- Raises both until the logons stop.
- Says pooling is switched on, so repeated logons should be impossible, and goes no further.

### junior

- Says the service is opening connections over and over and the pool is not holding on to them.
- Points at the second number as the one to change.

### mid

- States what each number bounds, and which of them explains the logon volume at this load.
- Walks one wave of forty requests through the pool and says how many of them log on.
- Chooses the idle count from the load the service really sustains, and says what a connection
  held open costs the far side.

### senior

- Wants the sustained load and the logon rate measured before and after, rather than settling it
  by argument.
- Says what the pool does when traffic falls away for an hour and then returns, and what that
  costs the first requests back.
- Treats the number as something agreed with whoever owns the SAP instance rather than a local
  tuning decision.
- Separates a burst that wants headroom from a steady load that wants a floor, and says which
  this is.

## Follow-ups

- Somebody sets the idle count to zero because the servers are short of memory. What happens to
  the logon rate?
  probes: that zero switches pooling off entirely, so the storm gets worse rather than better

- The load test is repeated with twice as many requests in flight. Which of the two numbers do
  you change, and who do you have to ask before you change it?
  probes: that one is local arithmetic and the other spends a resource belonging to somebody else

- A colleague says the fix is to raise the first number to two hundred. What do you tell them?
  probes: whether they have located the logon volume in the right number, or are guessing

- The traffic is really forty at once for twenty seconds, once an hour, and almost nothing in
  between. Does your number change?
  probes: whether the shape of the traffic, not the peak, drives the choice

## Sources

- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
- SAP KBA 2005477, "Configurable SAP JCo pooling parameters" — names every pool property, but the
  full text sits behind an S-user login, so it is cited by number rather than linked.

## Notes

Verified: `jco.destination.peak_limit` is the maximum number of connections that may be active
for a destination simultaneously, and `jco.destination.pool_capacity` is the maximum number of
idle connections kept open, where 0 disables pooling entirely. Defaults have moved between JCo
versions — `pool_capacity` went from 0 to 1 in 3.0.8 — so do not build any part of the question
on a default value, and do not hold a candidate to one.

The arithmetic in the Ask is an idealisation and is meant to be: real traffic does not arrive in
clean waves of forty, so "thirty-nine fresh logons per wave" is the shape of the answer, not a
figure to be reproduced. Credit the candidate who says so.

The idle connections here are expired on a timer as well, which is what the first-call-of-the-
morning troubleshooting card is built on. Mentioning it is a strong signal; chasing it is a
detour, because in this card the connections are being closed on return, not while asleep.

Deliberately one instance and one destination. The lead card on this topic owns what happens
across many instances, where a real limit can be enforced, and what a caller experiences once the
pool is exhausted. If the candidate goes there, note it and bring them back — and do not run both
cards in the same interview.
