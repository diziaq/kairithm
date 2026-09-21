---
id: database-mybatis-no-persistence-context-01
schema_version: 2
title: Two bugs the week after the mapping layer came out
category: database
topic: mybatis
level: senior
tags: [correctness, maintainability, testing, transactions]
time_estimate_min: 10
order: 435
links:
  related: [java-testing-mocks-assert-the-calls-01]
---

## Ask

A service was moved off its entity mapping layer onto MyBatis. Two bugs land the same week: a
method that changes a field on a loaded object writes nothing, and a method that reaches the same
row by id in one place and by order number in another ends up with two objects that drift apart.
The team wants both fixed. What do you tell them?

## Tests

Whether the candidate can state what a hand-written mapping layer deliberately does not do, and
design around the absence rather than rebuilding it badly in the service.

## Ideal minimal answer

Neither is a defect: MyBatis watches nothing, so a change only reaches the database when a
statement is run, and two queries for the same row give two objects because there is no identity
map — that is the trade for every write being visible in a mapper. Do not hand-build a register
of loaded rows: write explicitly, read once, and assert on the row.

## Listen for

- Nothing is watching the object, so a change only reaches the database if somebody calls a
  statement that writes it
- Two reads produce two objects; there is no register of what this unit of work has already read
- Says both of these are the deal the team took, not defects: no hidden write means every write
  is visible in a mapper file
- Warns off the obvious repair — a home-made store of rows already read, keyed by id — and says
  what owning one would cost: staleness, write ordering, thread scope
- Asks where the transaction boundary sits now, given the write happens when the statement runs
- Names the actual change: explicit write calls, and one loaded object passed along rather than
  fetched a second time

## Expected knowledge

- That a write here happens when a statement is run, and not before or after
- That the previous layer watched loaded objects for the length of a unit of work, and this one
  does not
- That MyBatis does keep results from a repeated identical query inside one session, which is a
  narrower thing

## Strong signals

- Knows results are reused for the same statement with the same arguments inside one session, and
  can say why that did not save the second bug
- Asks how the first bug got past the tests, and wants the assertion moved onto the row rather
  than the object
- Says which of the two objects wins at write time and makes that explicit rather than incidental
- Asks whether the move off the old layer is finished, because a half-move is the worst of both

## Weak signals

- Builds a register of loaded rows by hand because the old framework had one
- Says the library is broken or immature
- Adds a cache so the two reads agree
- Wraps everything in a longer transaction and expects that to make the change stick

## Answer bands

### weak

- Calls it a defect in the library.
- Expects the setter to reach the database and cannot name what would send it.
- Proposes a cache so the two reads line up.

### mid

- Says nothing tracks the object, so a statement has to be called to write the change.
- Says two reads yield two objects and one will overwrite the other.
- Fixes both by writing explicitly and by reading once.

### senior

- Frames the absence as the trade the team accepted, and names what they got in return.
- Rejects hand-building a register of loaded rows and lists what it would then owe.
- Says where the unit of work boundary sits relative to each write, and what an exception between
  two writes leaves behind.
- Asks what test would have caught the first bug, and moves the assertion onto the row.

### lead

- Sets a convention for the whole service and says what enforces it after review.
- Says which layer this service should actually be on, given what it does, and what would change
  their mind.
- Names the cost of sitting between the two for a year and who pays it.

## Follow-ups

- Someone proposes a per-request map of rows already read, keyed by id, so the two paths agree.
  Walk me through the first month of living with that.
  probes: what they would owe once they own it — stale rows, write ordering, thread scope
- In one test the two reads do hand back the same object and the bug will not reproduce. What
  could make that happen?
  probes: results reused for an identical query inside one session, and its conditions
- A column is renamed. What has to change, and what tells you that you missed one?
  probes: XML is not compiled; whether the safety net is tests or hope
- The first bug shipped. What was the test asserting, and what should it have been asserting?
  probes: asserting on the object in memory rather than on what is in the database

## Sources

- https://mybatis.org/mybatis-3/configuration.html#settings
- https://mybatis.org/mybatis-3/java-api.html

## Notes

MyBatis keeps a local cache per `SqlSession`, so the same statement with the same arguments does
return the same object inside one session; `localCacheScope` controls it and defaults to
`SESSION`. That is a per-statement result cache, not an identity map across the unit of work,
which is why two different queries for one row give two objects. With Spring the session is bound
to the transaction, so a candidate who has seen the reuse behaviour is describing something real
— push them on why it did not help here.
