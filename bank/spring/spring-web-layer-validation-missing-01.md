---
id: spring-web-layer-validation-missing-01
schema_version: 2
title: The annotated field that lets nulls through
category: spring
topic: web-layer
level: junior
tags: [api-design, correctness, failure-modes]
time_estimate_min: 5
order: 70
links:
  deeper: [spring-web-layer-error-contract-01]
  related: [spring-persistence-lazy-initialization-01]
---

## Ask

A `POST /customers` endpoint takes a request body object whose `email` field is annotated
`@NotBlank`. Someone posts a body with no email at all. The endpoint returns `201` and a row
lands in the database with a null email. The annotation is definitely on the field. Why did
nothing check it, and what would the client have seen if it had?

## Tests

Whether the candidate knows that constraint annotations are inert until something is asked to
apply them, and can say what the framework does with a failed check at the web boundary.

## Ideal minimal answer

The annotation on the field is only data; nothing runs it unless the body parameter is marked so
the check is applied at that boundary. Once it is, the handler is never entered and the client
gets a client error instead of a `201`.

## Listen for

- An annotation on a field is data; something has to run the check, and at this boundary the
  parameter has to be marked for it
- Knows a library has to be present for any of it to run, and that the web starter does not
  bring it
- Says what a failed check produces: the handler is never entered and the client gets a client
  error, not a server error
- Would add a test that posts the bad body and asserts the status

## Expected knowledge

- Where the check runs relative to the controller method
- That a rejected request never reaches the service layer

## Strong signals

- Asks whether the column should have been non-nullable in the first place, so the database
  would have caught it too
- Points out that the default body of the error response leaks field and class names, and asks
  what the client contract should be

## Weak signals

- Adds an `if` to the controller and moves on
- Believes the annotation is applied whenever the object is created
- Says the response should be a server error

## Answer bands

### weak

- Cannot say what makes the annotation run.
- Suggests checking the field by hand in the controller as the whole answer.

### junior

- Knows the parameter has to be marked so the check is applied.
- Says the client should get a client error rather than a created response.

### mid

- Explains that the check runs before the handler, so the method body never executes.
- Knows the checking library is a separate dependency from the web starter.
- Asks why the column allowed a null, and treats that as a second defect.
- Adds a test that posts the bad body and asserts on the status.

## Follow-ups

- A field is required only when another field is set to a particular value. Where does that
  check live?
  probes: whether they can go past per-field annotations to object-level rules and where they
  belong
- What exactly should the caller get back, beyond the status code?
  probes: the error contract, and whether they would leak internal field names
- The same object is also used by a message consumer that does not go through the web layer. Is
  it checked there?
  probes: that the boundary applies the rule, not the object itself

## Sources

- https://docs.spring.io/spring-boot/reference/io/validation.html
- https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-methods/validation.html

## Notes

Since Spring Boot 2.3 `spring-boot-starter-validation` is not pulled in by
`spring-boot-starter-web`, so a missing dependency is a real cause here as well as a missing
`@Valid`. A rejected body produces `MethodArgumentNotValidException`, which the default handling
turns into a 400.
