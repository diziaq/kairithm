---
id: spring-web-layer-error-contract-01
schema_version: 1
title: Three shapes of error from one service
category: spring
topic: web-layer
level: mid
tags: [api-design, failure-modes, observability, operations]
time_estimate_min: 8
order: 71
links:
  deeper: [spring-web-layer-thread-exhaustion-01]
---

## Ask

A client team complains that your service reports failures three different ways: some endpoints
return a JSON object with a `message` field, some return an empty body with a 500, and when the
token has expired they get an HTML page. Every controller catches its own exceptions. Design the
fix — and tell me why the HTML one is the odd case.

## Tests

Whether the candidate can move error handling from scattered catch blocks to one boundary, and
whether they know where that boundary's reach ends in the request path.

## Listen for

- One place that turns failures into responses, rather than a catch block per controller
- A single response shape for every failure, and that the framework has a standard one worth
  adopting rather than inventing another
- The HTML page appears because that failure happened before the request reached the dispatching
  machinery, so the shared handler never saw it
- Names what handles a failure that escapes that far, and how to make its output consistent too
- Distinguishes what the client is told from what is logged: a correlation identifier out, the
  stack trace kept in

## Expected knowledge

- That a handler advising all controllers is applied by the dispatching machinery
- That filters and security run outside it

## Strong signals

- Adopts the standard problem format instead of a homegrown envelope, and says why a shared
  shape across services is worth more than a nicer one per service
- Says the status code is part of the contract and argues about which failures are the client's
  fault
- Points out that the error body must not leak internals, and that the stack trace belongs in
  the log with an identifier the client can quote

## Weak signals

- Proposes one giant catch of `Exception` returning 500 for everything
- Cannot explain why one path produced HTML
- Puts the error shape in each controller again, just more consistently

## Answer bands

### weak

- Suggests catching everything in each controller and returning a message.
- Has no explanation for the HTML response.

### junior

- Knows there is a way to handle exceptions for all controllers in one place.
- Cannot say what falls outside its reach.

### mid

- Moves handling to one shared place and defines a single body shape.
- Maps failures onto sensible status codes rather than defaulting to 500.
- Knows the token failure happened before dispatch, so the shared handler was never consulted.

### senior

- Adopts the standard problem format and argues for consistency across services.
- Makes the fallback path produce the same shape as the handled path.
- Separates the client-facing body from the logged detail, tied together by an identifier.
- Says how the contract is tested so it cannot drift back.

## Follow-ups

- The failure happens in a filter, before any controller. What does the client get now, and what
  do you want them to get?
  probes: the fallback path and making it produce the same shape
- Support cannot find the log line for a customer's failed request. What is missing?
  probes: an identifier in the body that ties back to the logs
- The body currently contains the class name of the exception. Any objection?
  probes: leaking internals; treating the error body as a published contract

## Sources

- https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-rest-exceptions.html
- https://docs.spring.io/spring-boot/reference/web/servlet.html#web.servlet.spring-mvc.error-handling

## Notes

`@RestControllerAdvice` plus `ResponseEntityExceptionHandler` is the shared boundary; Spring
Framework 6 provides `ProblemDetail` (RFC 7807) and `ErrorResponse`, and
`spring.mvc.problemdetails.enabled` turns it on for the framework's own exceptions. A failure
thrown in a servlet filter never reaches `DispatcherServlet`, so it is handled by the container's
error dispatch and Boot's error controller — which is where the HTML comes from.
