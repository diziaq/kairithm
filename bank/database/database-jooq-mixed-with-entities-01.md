---
id: database-jooq-mixed-with-entities-01
schema_version: 2
title: The read side sees the old value
category: database
topic: jooq
level: senior
tags: [transactions, correctness, failure-modes, maintainability]
time_estimate_min: 10
order: 445
---

## Ask

One service has its reads on jOOQ and its writes still on entities, inside the same transaction.
A method loads an order, sets its status to `CANCELLED`, then runs a jOOQ query filtered on
status — and the order comes back as if nothing changed. In another method a jOOQ update is
invisible to code holding that same order. Explain both.

## Tests

Whether the candidate can reason about two data access paths sharing one transaction, and say
which one is holding state the other cannot see.

## Ideal minimal answer

First ask whether jOOQ is handed the transaction-bound connection. If it is, the change is still
pending in memory and Hibernate 6 flushes only before its own queries over overlapping tables,
so a query it did not issue reads the old row; the jOOQ update then leaves the managed order
stale, and the flush at the end writes the old value back over it.

## Listen for

- The change is still sitting in memory; nothing has sent it, so a query that goes straight at
  the connection reads the row as it was
- The entity side pushes waiting changes out before running queries it issued itself, against
  tables it knows are affected, and has no idea a query it did not issue is about to run
- Asks first whether both paths are even on the same connection — if the other one has its own
  data source it is a separate transaction and could never see uncommitted work
- A write that goes around the loaded objects leaves them stale, and the next push can put the
  old values back over it
- Says the caches on the entity side do not learn that a row changed underneath them
- The fix is a boundary — which rows each path owns — rather than sprinkling a push before every
  read

## Expected knowledge

- That a change to a loaded object is held until something sends it
- That two paths must share one connection to share one transaction
- Hibernate 6 sends waiting changes before its own queries when the tables overlap; this is not
  the same as before any statement on the connection

## Strong signals

- Asks how the other path obtains its connection before diagnosing anything else
- Names the lost update the stale object can cause, not only the stale read
- Says what a test would assert to catch it: the row, after the method returns, in a fresh read
- Points out that the second symptom is the dangerous one, because nothing throws

## Weak signals

- Adds a push-to-database call before every query on the other path and calls it the pattern
- Says the transaction has not committed yet so of course nothing is visible, without asking
  about the connection
- Runs the other path in its own transaction to make it consistent
- Suggests turning off the caches and expects that to fix the first symptom

## Answer bands

### weak

- Says one of the two libraries is broken.
- Cannot say where the changed value lives between the setter and the commit.

### mid

- Says the change has not been sent yet, so a query issued outside sees the old row.
- Says a write that goes around the loaded objects leaves them holding stale values.

### senior

- Asks whether the two share a connection and says what each answer would mean.
- Explains why the entity side pushes changes out for its own queries and not for this one.
- Volunteers that the stale object can carry the old value back to the database at the end of the
  method.
- Puts the rule at a boundary — which rows each path owns — instead of at every call site.
- Names what would catch it: a fresh read in a test, not an assertion on the object.

### lead

- Says what the team must keep in their heads to work this way safely, and whether the read-side
  gain is worth it.
- Makes the rule survive the next hire: a convention with something enforcing it.
- Says at what point the split stops paying and one path should own everything.

## Follow-ups

- Someone adds a line that forces the update out to the database before every read on the other
  path. Fix, or habit?
  probes: whether they see a write being ordered by somebody else's read, and want a boundary
- A well-meaning change gives the other path its own data source. What do you expect to see?
  probes: two connections, two transactions, invisible work, and a lock wait between them
- The stale object is thrown away when the request ends, so the team says no harm was done.
  Persuade them otherwise.
  probes: the push at the end of the method carrying old values back over the newer write
- The same row is also held in a cache that outlives the request. What now?
  probes: whether they follow the stale value out past the transaction

## Sources

- https://docs.jboss.org/hibernate/orm/6.4/userguide/html_single/Hibernate_User_Guide.html#flushing
- https://www.jooq.org/doc/latest/manual/getting-started/jooq-and-jpa/
- https://docs.spring.io/spring-framework/reference/data-access/jdbc/connections.html

## Notes

Two mechanisms, one symptom each. Hibernate auto-flushes before a query it issues whose query
spaces overlap the pending changes; a jOOQ query running on the same JDBC connection is outside
that, so it sees the row as it was. And a jOOQ write bypasses the persistence context entirely,
so a managed instance of that row stays stale and can be flushed back over the update. Both
depend on jOOQ being handed the transaction-bound connection — with Spring that is
`DataSourceUtils` or a transaction-aware proxy. If it has its own pool, the first answer is
simply that these are two transactions, and the candidate who asks about that first is ahead.
