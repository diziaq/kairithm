---
id: microservices-failure-handling-timeout-unknown-outcome-01
schema_version: 1
title: The payment call timed out and nobody knows if it landed
category: microservices
topic: failure-handling
level: junior
tags: [failure-modes, correctness, idempotency, operations]
time_estimate_min: 6
order: 10
links:
  deeper: [microservices-failure-handling-cascade-slow-dependency-01]
  related: [microservices-idempotency-double-click-order-01]
---

## Ask

Your checkout service calls the payment service over HTTP and the call times out after three
seconds. Nothing comes back — no success, no error. Did the customer get charged? What does your
code do next, and what do you show the user?

## Tests

Whether the candidate treats a timeout as an unknown outcome that has to be resolved, rather than
as a failure they can assume did nothing.

## Listen for

- Says plainly that they do not know: the other side may have done the work and only the answer
  was lost
- Lists the places it could have stopped — the request never arrived, it arrived and is still
  running, it finished and the reply was lost
- Refuses to fire the charge again without something that makes a repeat safe
- Proposes going back and asking the payment side what it knows about this order's reference
- Leaves the order in a state that says "we do not know yet" instead of forcing it to paid or
  failed

## Expected knowledge

- A timeout is a decision the caller makes; the other side never hears about it
- The difference between a refusal you received and an answer you never got

## Strong signals

- Points out that the user-facing answer and the internal state are two separate decisions
- Says what should happen if the unknown is still unknown an hour later, and who looks at it

## Weak signals

- "It timed out, so it failed" with nothing further
- Immediately calls it again to be sure, with no mention of what that does to a card
- Shows the user a definite failure and moves on

## Answer bands

### weak

- Treats the timeout as proof the charge did not happen.
- Repeats the call straight away and sees no problem with that.
- Cannot name a second possible outcome besides success and failure.

### junior

- States that the outcome is unknown and gives at least one way the work could have completed.
- Hesitates to repeat the charge, even if they cannot yet say what would make it safe.
- Keeps the user informed with something honest rather than a confident wrong answer.

### mid

- Walks the three places the request could have stopped and says what each leaves behind.
- Wants a way to ask the payment side about this order before deciding anything.
- Puts the order in a pending state with a follow-up path rather than guessing.

## Follow-ups

- Your colleague's fix is to call it a second time straight away. What might the card statement
  look like afterwards?
  probes: whether a repeat is safe, and whether they reach for something that makes it safe
- The payment team says their side finished in 200ms and logged a success. Where did your three
  seconds go?
  probes: the reply path, queueing on the caller's own side, timeout as a caller-side choice
- There is no way to ask them and no way to look it up. What do you put on the screen?
  probes: honesty in the UI, and whether they invent certainty they do not have

## Notes

The card is passed by a candidate who says "I do not know whether it happened, and here is how I
find out". Naming a pattern is not the point.

## Sources

- https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
