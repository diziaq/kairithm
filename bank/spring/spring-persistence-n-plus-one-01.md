---
id: spring-persistence-n-plus-one-01
schema_version: 2
title: Fifty orders, one hundred and fifty-two queries
category: spring
topic: persistence
level: senior
tags: [performance, observability, correctness]
time_estimate_min: 9
order: 81
links:
  deeper: [spring-persistence-optimistic-locking-01]
  related: [database-hibernate-batch-insert-01]
---

## Ask

`GET /orders?page=0&size=50` takes 1.8 seconds. Someone enabled statement logging and counted
152 queries for one call. Operations tripled the connection pool and it made no difference.
Take me from that log to a fix, and tell me what you would check about the fix before merging
it.

## Tests

Whether the candidate can read a query count as a structural property of how the data is
fetched, pick a fetching strategy on the shape of the data, and verify the fix rather than
assume it.

## Ideal minimal answer

152 is one query for the page, one for the total, and one per row for each lazy relation touched;
a bigger pool cannot help because those run one after another on one connection. Choose between
fetching in the same query, batching the follow-ups and selecting only the fields needed. A
collection fetch with paging loses the page boundary, so assert the query count in a test.

## Listen for

- Decomposes the number rather than reacting to it: one query for the page, one to count the
  total for the paged response, then one per row for each lazily fetched relation that gets
  touched — fifty rows across three relations, plus those two
- A bigger pool cannot help, because the queries are sequential on one connection inside one
  request
- Names more than one way to fix it and picks on shape: fetching the relation in the same query,
  batching the follow-up fetches, or selecting only the fields the response needs
- Knows that fetching a collection in the same query as a paged result is a trap, because the
  row count no longer matches the page size
- Verifies by counting queries in a test, not by timing it once on a warm cache

## Expected knowledge

- Lazy versus eager fetching, and that eager everywhere is not a fix
- That the framework can report how many statements it issued

## Strong signals

- Asks what the endpoint actually needs to return before optimising how it is loaded
- Knows that joining two separate collections in one query is rejected outright, and what to do
  instead
- Says the paging case degrades to loading everything and filtering in memory, and that a
  warning is logged when it happens
- Adds an assertion on the query count to the test suite so the regression is caught

## Weak signals

- Makes the relations eager and declares victory
- Adds a cache in front of the endpoint
- Raises the pool, the page size, or the timeout
- Times the endpoint once after the change and calls that verification

## Answer bands

### weak

- Blames the database or the pool.
- Cannot account for where 152 comes from.

### mid

- Decomposes the number into the page query plus one per row for each relation touched.
- Knows a bigger pool cannot help because the calls are sequential within one request.
- Fetches the relation together with the page, or batches the follow-ups.

### senior

- Chooses between fetching together, batching, and selecting only needed fields, and says why
  for this endpoint.
- Knows paging plus a collection fetch loses the page boundary and what the framework does then.
- Asserts the query count in a test so it cannot regress.
- Asks whether the endpoint should be returning this shape at all.

### lead

- Sets a standard for the team: which endpoints may return entities, and what is measured.
- Weighs the cost of a purpose-built query per endpoint against one generic mapping everyone
  fights.

## Follow-ups

- The fix works for one relation. You add a second one the same way and it refuses to run at
  all. Why?
  probes: two collections joined in one query; whether they know the limit or discover it in
  production
- Paging still has to work. What happens to the page size once you pull the child rows in the
  same query?
  probes: rows per entity versus rows per page; the in-memory fallback
- The change shaved 1.6 seconds locally on a hundred rows. What do you want to see before you
  believe it holds?
  probes: verification on production-shaped data, and a count rather than a stopwatch

## Sources

- https://docs.jboss.org/hibernate/orm/6.4/userguide/html_single/Hibernate_User_Guide.html#fetching
- https://docs.spring.io/spring-data/jpa/reference/jpa/entity-graph.html

## Notes

`@EntityGraph`, `join fetch`, and `hibernate.default_batch_fetch_size` are the three mechanisms.
Join-fetching two `List` collections at once raises `MultipleBagFetchException`. Combining a
collection fetch with `firstResult`/`maxResults` makes Hibernate apply pagination in memory and
log a warning about it — that detail separates people who have shipped this from people who have
read about it.
