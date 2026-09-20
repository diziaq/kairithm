---
id: microservices-idempotency-non-idempotent-side-effect-01
schema_version: 1
title: The write is safe to repeat, the email and the warehouse are not
category: microservices
topic: idempotency
level: senior
tags: [idempotency, correctness, retries, failure-modes, transactions]
time_estimate_min: 9
order: 50
links:
  deeper: [microservices-idempotency-four-schemes-one-refund-01]
  related: [microservices-distributed-transactions-order-payment-split-01]
---

## Ask

Your order handler writes the order, sends a confirmation email, and calls the warehouse API to
create a shipment. You have already made the database write safe to repeat — the same order twice
leaves one row. Last night the handler threw after the warehouse call and the platform ran it
again. This morning one customer has two confirmation emails, and a second pallet has left the
building. The warehouse API has no notion of a repeat. What do you change about those two steps?

## Tests

Whether the candidate treats safety against repeats as a property of each individual effect rather
than of the handler, and can design for effects that land in systems they do not control and
cannot take back.

## Listen for

- The safe write buys nothing for the other two: the guarantee stops at the edge of their own
  store, and a pallet is not a database row
- The handler has three effects with three different behaviours on a repeat, and a rerun replays
  all of them regardless of which one failed
- Splits the work: commit local state first, then drive the outside effects from a durable record
  that remembers which ones are already done
- Sends the warehouse a reference of their own choosing so the other side can recognise a repeat,
  and asks the warehouse team for that if it does not exist
- Where a lookup exists, asks the other side whether the shipment is already there before creating
  one
- Weighs the two effects differently: a second email costs an apology, a second pallet costs the
  freight, the stock and somebody's afternoon
- Separates preventing the second pallet from noticing it went out — the second is cheaper and
  works even on a system you cannot change

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

- Sees that the rerun replays all three effects and that only one of them was made safe.
- Suggests sending something the warehouse can match on, or checking before creating.
- Treats the email as the lesser problem, with a reason in money or effort.

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
