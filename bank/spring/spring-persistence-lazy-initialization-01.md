---
id: spring-persistence-lazy-initialization-01
schema_version: 1
title: The collection that is sometimes there
category: spring
topic: persistence
level: junior
tags: [failure-modes, performance, api-design]
time_estimate_min: 6
order: 80
links:
  deeper: [spring-persistence-n-plus-one-01]
---

## Ask

`GET /orders/{id}` returns an `Order` entity straight from the repository. Its `lines` collection
is lazy. In the running application the JSON contains the lines. In a unit test that calls the
same service method and then reads `order.getLines()`, it throws. Explain why the same code
behaves differently in the two places.

## Tests

Whether the candidate knows that a lazy field is only loadable while the session that produced
the entity is still open, and can identify what keeps it open in one case and not the other.

## Listen for

- A lazily loaded field is a placeholder that needs the session that loaded the entity to still
  be open
- In the running application something holds that session open past the service call, which is
  why serialising the response can still fetch
- The test has no such thing, so the session closed when the service method returned
- Notices that the working case is working by accident and that the query is being issued during
  response writing
- Returning a purpose-built response object instead of the entity makes both cases the same

## Expected knowledge

- What lazy loading is for
- That reading an entity's data requires an open session

## Strong signals

- Says the setting that makes it work in the application also holds a database connection for
  the whole request, and would rather turn it off and fix the code
- Points out that serialising an entity puts the database on the response-writing path, where
  a failure is halfway through a response that already has a status code

## Weak signals

- Proposes making every relation eager
- Adds a call inside the service that touches the collection, without saying why that works
- Says the test is wrong and should start the whole application

## Answer bands

### weak

- Says one is a test and tests are different, with no mechanism.
- Suggests making everything eager.

### junior

- Knows the collection is loaded on demand and that the session must still be open.
- Says the test's session had already closed.

### mid

- Names what keeps the session open across the whole request in the running application.
- Says the JSON only works because the fetch happens while the response is being written.
- Returns a purpose-built object from the service so the boundary is explicit.

## Follow-ups

- Someone turns off the thing that makes it work in the app, to see what breaks. What do you
  expect?
  probes: whether they can predict the failures rather than only explain them afterwards
- Making the relation always load fixes both cases. What does it cost you on the list endpoint
  that returns fifty orders?
  probes: opens the door to the query-count problem without naming it
- The response writer fails halfway through. What has the client already received?
  probes: status code already sent; why database work on the write path is risky

## Sources

- https://docs.spring.io/spring-boot/reference/data/sql.html#data.sql.jpa-and-spring-data.open-entityManager-in-view

## Notes

`spring.jpa.open-in-view` defaults to `true` in Spring Boot and logs a warning at startup saying
so. It is what makes the running application work. It also keeps a database connection bound for
the whole request, which is the reason most teams eventually turn it off.
