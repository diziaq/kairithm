---
id: microservices-idempotency-key-scope-and-lifetime-01
schema_version: 2
title: Where the request reference lives and how long it lasts
category: microservices
topic: idempotency
level: mid
tags: [idempotency, correctness, api-design, transactions, operations]
time_estimate_min: 8
order: 40
links:
  deeper: [microservices-idempotency-non-idempotent-side-effect-01]
---

## Ask

Your team added a header where the client puts a fresh reference on each Create Order, and the
service ignores a create whose reference it has already seen. It has been live a week. Tell me
where that reference is stored, how long it is kept, and what the service does when the same one
comes back with a completely different body.

## Tests

Whether the candidate can turn a one-line rule into a design that survives multiple instances,
restarts, concurrency and time.

## Ideal minimal answer

The reference and the order are written in one transaction in the shared database, or the
service can create the order and forget that it did. A repeat gets the original order identifier
back, not an acknowledgement and not a second order; the same reference with a different body is
rejected; and retention is set from how long a client may still be retrying.

## Listen for

- The record of the reference and the effect of the request are committed together, or the
  service can do the work and forget that it did
- An in-process map dies with the instance and is not shared with its nine siblings
- A retention window argued from how long a client might keep trying, not an arbitrary number,
  and says what happens after it lapses
- The same reference with a different body is a client bug: reject it loudly rather than silently
  returning something the caller did not ask for
- A repeat returns the original outcome — the order identifier — not a bare acknowledgement
- The window between accepting a reference and finishing the work: a second copy arriving inside
  it must wait or be turned away, never run alongside

## Expected knowledge

- Two requests can be in flight at once on two instances
- A uniqueness rule enforced by the store settles a race that application code cannot

## Strong signals

- Stores enough of the original response to reconstruct it, and says why the caller needs it
- Asks whose reference it is — per client, per endpoint, or global — and what happens if two
  clients pick the same string
- Treats the stored record as data with an owner, a size and a cleanup job

## Weak signals

- Keeps them in a local cache and does not notice the second instance
- "We keep them forever" with no thought about growth
- Returns the cached result no matter what the body says
- Checks for the reference, then writes, with nothing preventing two runs of that pair

## Answer bands

### weak

- Describes the rule back without saying where anything is stored.
- Puts the record somewhere that does not survive a restart or a second instance.
- Has no answer for two copies arriving at the same time.

### junior

- Stores the reference in the shared database and knows a local map would not do.
- Picks a retention period, even if the reasoning is thin.
- Has not thought about a repeat arriving while the first is still running.

### mid

- Commits the record and the order in one transaction, and says why they cannot be separated.
- Returns the original result to a repeat, and says what the caller does with it.
- Ties retention to client retry behaviour and names what happens once a record is gone.
- Rejects a mismatched body rather than answering from the stored result.

### senior

- Handles the in-flight case explicitly with a rule the store enforces, not a read-then-write.
- Treats the stored records as an operational concern: growth, cleanup, and what breaks if the
  cleanup job stops.
- Says which endpoints do not need any of this, and why paying for it everywhere is wasteful.

## Follow-ups

- Two copies of one request arrive half a second apart, and the first has not finished. What does
  the second one see?
  probes: the in-flight window; a database constraint versus a check in application code
- That table is now the largest thing you own. What do you do?
  probes: retention argued from client behaviour rather than a number someone liked
- A client generates one value at startup and reuses it for every order all day. What breaks, and
  whose problem is it?
  probes: contract clarity and whether they validate rather than trust the caller

## Sources

- https://docs.stripe.com/api/idempotent_requests
- https://www.rfc-editor.org/rfc/rfc9110#name-idempotent-methods
