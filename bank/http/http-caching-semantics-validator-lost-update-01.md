---
id: http-caching-semantics-validator-lost-update-01
schema_version: 2
title: A version column the API never exposed
category: http
topic: caching-semantics
level: mid
tags: [consistency, correctness, api-design]
time_estimate_min: 8
order: 140
links:
  related: [spring-persistence-optimistic-locking-01]
---

## Ask

`PUT /products/{id}` takes the whole product. A back-office screen and a partner integration both
load product 40, each change a different field, and each save. The second save wins and the
first change is gone. The table already has a version column that the API has never exposed. How
do you stop this at the API?

## Tests

Whether the candidate can carry concurrency control across a stateless boundary, rather than
solving it only inside the transaction where the two writes never meet.

## Ideal minimal answer

Hand the caller something that identifies the version they read, on the response to the read, and
require it back on the write. The server applies the change only if it still matches and refuses
otherwise, so the caller has to re-read and decide what to do. The version column already in the
table is a fine value to use.

## Listen for

- A whole-object write carries fields the caller read some time ago, so the later save overwrites
  the earlier one with stale values
- A transaction does not help: the two writes never overlap, they are minutes apart
- The identity of what was read has to travel out to the caller and come back on the write
- Names the response header that carries it, the request header that asserts it, and the status
  returned when it does not match
- Says what the caller does with a refusal — re-read and re-apply, or show the human what
  changed — and that sending the same body again re-creates the problem
- The existing version column can be the value, provided it changes on every write
- The comparison and the write have to be one operation at the store, not read, compare, then
  write in the service

## Expected knowledge

- A conditional request lets the server test a condition against the current state before
  applying the method
- A response header can carry an opaque token that identifies the current version of a resource

## Strong signals

- Distinguishes a token that must match exactly before a write from one used to avoid resending
  an unchanged body on a read
- Asks whether a narrower update — only the fields that changed — would remove most of the
  collisions, and says what that costs the API's shape
- Points out that two copies of the service must not both be able to accept the write, and says
  what enforces that
- Asks how often this actually happens before building anything, and what the conflict rate
  would tell them

## Weak signals

- "Wrap it in a transaction"
- Holds a lock while a person has a form open
- Puts a version number in the body and never says what the server does when it disagrees
- Returns 200 with an error message in the body
- Says last write wins is acceptable without asking whose change was lost

## Answer bands

### weak

- Proposes a transaction or a database lock and stops.
- Cannot say why the two saves do not collide at the database.

### junior

- Says the second save carries values read before the first one.
- Suggests the caller send something identifying what it read.

### mid

- Names the read header, the write header and the refusal status, and describes the round trip.
- Says what the caller is expected to do after a refusal.
- Uses the existing version column as the value rather than inventing a second mechanism.

### senior

- Insists the comparison and the write happen as one operation at the store.
- Separates the write-guard use of the token from the bandwidth-saving use on reads.
- Raises a narrower update shape as an alternative before anyone suggests it, and says what it
  trades.
- Wants the conflict rate visible, because a rising one means the design is wrong rather than
  the callers.

## Follow-ups

- The integration gets the refusal and immediately sends exactly the same body again.
  probes: a blind retry re-creates the lost change; the caller has to read again first
- The two changes touch different fields and could both have been kept. Is that the server's
  call?
  probes: who owns the merge; detection and resolution are different jobs
- Two copies of your service accept the write in the same millisecond. What stops both
  succeeding?
  probes: compare-and-set enforced by the store, not by service code
- The partner also complains about downloading four hundred kilobytes of product they already
  have.
  probes: the same token used on the read path to avoid resending an unchanged body

## Sources

- https://www.rfc-editor.org/rfc/rfc9110.html#section-8.8.3
- https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.1
- https://www.rfc-editor.org/rfc/rfc9110.html#section-15.5.13
- https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.4

## Notes

Figures to release if asked: about 40,000 products, the back-office screen is used by nine
people, the partner integration pushes updates every fifteen minutes, and the version column is
maintained by the persistence layer and increments on every write.

What the card is really testing is whether the candidate notices the boundary. Everything needed
to prevent this already exists inside the database; the failure is that the API never let the
caller say which version it was writing against. `ETag` on the read, `If-Match` on the write,
`412` when it does not match — RFC 9110 §8.8.3, §13.1.1 and §15.5.13 respectively.

Two things to hold them to. The value must change on every write, which a version counter does
and a last-modified timestamp with second granularity does not. And the server must evaluate the
condition and apply the write atomically; a candidate who reads the row, compares in Java, and
then updates has moved the race rather than removed it.

`spring-persistence-optimistic-locking-01` asks the same question from inside the persistence
layer and at lead level. Do not run both with one candidate unless you specifically want to see
whether they connect the two ends.
