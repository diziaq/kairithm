---
id: microservices-failure-handling-timeout-budget-does-not-shrink-01
schema_version: 2
title: A 500 ms timeout in front of a five-second one
category: microservices
topic: failure-handling
level: senior
tags: [failure-modes, performance, capacity, operations]
time_estimate_min: 9
order: 600
links:
  shallower: [microservices-failure-handling-timeout-unknown-outcome-01]
  deeper: [microservices-failure-handling-what-you-shed-first-01]
  related: [microservices-retries-layered-multiplication-01]
---

## Ask

Service A calls B with a 500 millisecond timeout. B calls C with its own five-second timeout. C
slows down. A gives up at 500 milliseconds and shows the user an error, and B carries on for
another four and a half seconds holding a worker thread and a database connection. By Monday
lunchtime the whole chain has stopped answering. Walk me through it.

## Tests

Whether the candidate treats the caller's patience as something that has to travel with the
request and get smaller at each hop, and can say what the work already started costs after the
caller has gone.

## Ideal minimal answer

A's 500 ms is not B's limit, so every request A abandons leaves B holding a thread and a
connection for another 4.5 seconds on work nobody will read; at a few hundred a second that is
thousands of occupied slots. Pass the time remaining down so each hop's limit is under its
caller's, and make B stop when A has gone.

## Listen for

- A's timeout is a local decision: A stops waiting, and the request it started downstream keeps
  running to completion
- Does the arithmetic — B holds a thread and a pooled connection for five seconds per call while
  A waits half a second, so at two hundred calls a second that is a thousand in flight against a
  pool sized in the tens
- Names the real cost as the abandoned work, not the request that failed: the user's error is
  cheap, the resources still held by nobody's request are what empties the chain
- Each hop receives the time left, subtracts what it needs itself, and passes a smaller figure on,
  so C's limit is below B's and B's below A's
- Stopping has to be enforced, not just configured: the server side has to notice the caller has
  gone, and the database call needs its own statement-level limit or a cancellation
- B should refuse to start the call to C at all when the time left is less than C normally takes
- Any repeats inside B live inside the same allowance, or the allowance means nothing
- Once B's limit is under A's, the endpoints on B that never touch C stop being starved as well

## Expected knowledge

- A timeout is a caller-side choice and the other side is never told about it
- A worker and a pooled connection are held for as long as the call runs, whoever is still waiting
- The time left on a request can be carried in the request itself and reduced at each hop

## Strong signals

- Works out how many in-flight calls the extra 4.5 seconds costs before proposing any number
- Asks whether B's database call can be stopped at all, and what the driver actually does when
  the caller walks away
- Points out that 500 ms may already be too short for a healthy C, and asks for the latency
  spread before choosing anything
- Wants a count of work that finished after its caller stopped waiting, per hop, as the signal
  that would have shown this months ago

## Weak signals

- Raises A's limit to five seconds so the numbers agree
- Adds repeats in A because the call failed
- Sets one value everywhere and treats the chain as uniform
- Says the request carries its allowance downstream without saying who checks it or what happens
  when it has run out
- Recounts a past incident with the same shape and never says what to do about this chain
- Lists the options accurately and will not pick one

## Answer bands

### mid

- Says that A giving up does not stop B, once asked where B's work goes.
- Reduces B's limit below A's and can give a rough figure with a reason.
- Does not yet account for what B holds while this is happening at Monday volume.

### senior

- Raises of their own accord that each abandoned call leaves a worker and a connection held, and
  multiplies that by the arrival rate to say why the chain fills.
- Carries the time remaining with the request and derives each hop's figure from it, instead of
  three fixed numbers chosen separately.
- Says how the work is actually stopped — the callee checking, the query cancelled — not only
  that a smaller figure is configured.
- Declines to start a downstream call when what is left is less than that call usually needs.

### lead

- Fixes the user-facing figure from what the product needs, then divides it across the hops and
  says who owns each share.
- Names what would have caught it: work completing after its caller gave up, measured per hop.
- Says which teams have to change code for this to survive their hop, and what to do about the
  hop that will not.
- Accepts that some calls get refused at the edge with nothing spent, and says what the client
  is told.

## Follow-ups

- Someone changes A to five seconds so the user waits as long as the rest of the chain does. What
  have they bought?
  probes: the shallow fix — the user now waits five seconds and B still holds everything it held
- B is taking four hundred calls a second when C goes to four seconds. How many of B's workers and
  connections are busy, and what do B's other endpoints return?
  probes: concurrency arithmetic, and collateral failure of paths that never touch C
- B works out what time is left and sends it on. C's team ignore the field entirely. What stops
  C's query?
  probes: whether stopping work needs the callee and its database to co-operate, not just a header
- Half the calls now fail at B without reaching C at all, because ninety milliseconds were left.
  Is that right, and what do you tell A's team?
  probes: refusing work with no time left, and the contract with the caller

## Sources

- https://grpc.io/blog/deadlines/
- https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
- https://www.postgresql.org/docs/current/runtime-config-client.html#GUC-STATEMENT-TIMEOUT

## Notes

The move that separates this from any other timeout question is direction: the figure has to get
smaller as it travels, and something has to honour it at the far end. A candidate who only picks
better numbers per service has not seen the orphaned work. If they mention a header that carries
the remaining time, push them on who reads it and what happens when it reaches zero mid-query.
