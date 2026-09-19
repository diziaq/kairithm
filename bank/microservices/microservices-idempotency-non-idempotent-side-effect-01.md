---
id: microservices-idempotency-non-idempotent-side-effect-01
schema_version: 1
title: The write is safe to repeat, the email and the warehouse are not
category: microservices
topic: idempotency
level: senior
tags: [correctness, retries, failure-modes, transactions]
time_estimate_min: 9
order: 50
links:
  related: [microservices-distributed-transactions-order-payment-split-01]
---

## Ask

Your order handler is retried by the platform whenever it throws, and you have already made the
database write safe to repeat. The same handler also sends a confirmation email and calls the
warehouse API, which has no notion of a repeat. A retry fires. What actually goes wrong, and what
do you do about those two steps?

## Tests

Whether the candidate understands that safety against repeats is a property of each effect, not
of the handler, and can design for effects they do not control.

## Listen for

- The safe write buys nothing for the other two: the guarantee stops at the edge of their own
  store
- The handler now has three effects with three different behaviours on a repeat, and the retry
  replays all of them
- Splits the work: commit local state first, then drive the outside effects from a durable record
  that remembers which ones are done
- Sends the warehouse a reference of their own choosing so the other side can recognise a repeat,
  and asks the warehouse team for that if it does not exist
- Where a lookup exists, asks the other side whether the shipment is already there before creating
  one
- Weighs the two effects differently: a second email annoys a customer, a second shipment costs
  real money

## Expected knowledge

- A retry replays the whole handler, not the part that failed
- An outside system's behaviour on a repeat is part of its contract, and often undocumented

## Strong signals

- Records what was sent and what came back, so a repeat can be answered from that record
- Points out that the warehouse call timing out leaves the same unknown as any other call, and
  that the design has to survive it
- Designs for detecting a repeat that slipped through, not only for preventing one

## Weak signals

- Says the handler is idempotent because the database write is
- Wraps the outside calls in the database transaction
- Moves the email to the end and calls it solved
- Assumes the warehouse will add a dedupe feature because it is the obvious thing to do

## Answer bands

### mid

- Sees that the retry replays all three effects and names the visible damage.
- Suggests sending something the warehouse can match on, or checking before creating.
- Treats the email as the lesser problem, with a reason.

### senior

- Separates the local commit from the outside effects and drives the latter from a stored record
  of what still has to happen.
- Says what each crash point leaves behind, including a crash after the warehouse call and before
  recording it.
- Asks the warehouse for a matching reference and has a plan for the answer being no.
- Trades the cost of a repeat against the cost of the machinery, per effect.

### lead

- Decides which effects get real protection and which get detection plus a cleanup path, and says
  who does the cleanup.
- Names what the team would put in place to learn that duplicates happened last night.
- Turns the warehouse contract into something written down and tested rather than assumed.

## Follow-ups

- The warehouse team say they cannot change their API this quarter. What can you build with what
  they already have?
  probes: look-before-act, natural keys, a local ledger of what was already sent
- How do you find out tomorrow morning that it went out twice last night?
  probes: detection and reconciliation as part of the design, not only prevention
- One of the two is worth a sprint and one is not. Which, and why?
  probes: cost-weighted prioritisation rather than protecting everything equally
