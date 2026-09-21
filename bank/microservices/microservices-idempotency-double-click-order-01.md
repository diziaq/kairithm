---
id: microservices-idempotency-double-click-order-01
schema_version: 2
title: Double-click on Place Order creates two orders
category: microservices
topic: idempotency
level: junior
tags: [idempotency, correctness, retries, api-design]
time_estimate_min: 6
order: 30
links:
  deeper: [microservices-idempotency-key-scope-and-lifetime-01]
---

## Ask

A customer double-clicks Place Order. Two orders appear, two emails go out and the card is
charged twice. The frontend team says they will disable the button after the first click. Is that
the fix? What would you do?

## Tests

Whether the candidate sees that a guard in the browser cannot protect a state change on the
server, and can say what would.

## Ideal minimal answer

Disabling the button helps, but the server still accepts two creates, and a refresh, a retried
mobile request or a second tab produces the same two. The server needs something that recognises
the second request as the same intent — a reference sent by the client, or the cart being
checked out — and returns the first order rather than making another.

## Listen for

- The browser guard helps the common case, but the server still happily accepts two creates
- Names other paths that produce the same two requests — a refresh, a flaky network, a mobile app
  resending, a second tab, a proxy
- The check has to live on the server, in the same place the order is written
- Says what makes the two requests "the same one" — a reference the client sends, or a natural key
  such as the cart being checked out
- A repeat should get the first order back, not an error and not a second order

## Expected knowledge

- The client cannot know whether a request it never got an answer to was applied
- A uniqueness rule in a database is enforced even when two requests race

## Strong signals

- Points out that the two requests can land on two instances at the same moment, so a
  look-then-write check is not enough
- Separates "the same intent sent twice" from "the customer really wants two of these"

## Weak signals

- Accepts the browser fix as sufficient
- Suggests comparing the new order against recent orders by content, with no bound or reference
- Says the second request should return an error, with no thought about what the customer sees

## Answer bands

### weak

- Agrees that disabling the button solves it.
- Cannot name any other way two identical requests arrive.
- Talks about the click and never about what the server does with two requests.

### junior

- Says the guard is worth having but the server has to defend itself too.
- Names at least one other path that produces a repeat.
- Proposes something on the server that recognises the second request as a repeat.

### mid

- Puts the check and the write in the same store so they cannot disagree.
- Says what the second request should return to the caller.
- Notices the race between two simultaneous copies and handles it with a rule the store enforces.

## Follow-ups

- The button is disabled and it happens anyway. Give me one way.
  probes: whether they can enumerate paths that walk straight past a client-side guard
- Both requests arrive at two different instances of your service in the same millisecond. Does
  your fix still hold?
  probes: look-then-write races; whether the store enforces the rule rather than the code
- The customer genuinely wants to buy the same thing twice, ten seconds apart. How does your fix
  tell the difference?
  probes: what identifies an intent versus what identifies a payload

## Sources

- https://docs.stripe.com/api/idempotent_requests
