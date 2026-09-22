---
id: microservices-distributed-transactions-compensation-cannot-undo-01
schema_version: 2
title: The ticket email has gone out and the booking must be unwound
category: microservices
topic: distributed-transactions
level: lead
tags: [transactions, correctness, failure-modes, api-design]
time_estimate_min: 10
order: 180
---

## Ask

Your booking flow reserves a seat, charges the card, and emails the ticket. The email goes out,
and only then does the seat reservation turn out to be invalid, so the whole booking has to be
unwound. You cannot unsend the email. How do you design the flow given that?

## Tests

Whether the candidate designs around steps that cannot be taken back, and can tell reversal apart
from making amends.

## Ideal minimal answer

Put the email last, after the seat and the card have both succeeded, and treat it as impossible
to take back: the remedy is a correction and a refund, not a reversal. Then agree with the
product owner how many unwound bookings a week is acceptable, what holding a seat longer costs
on a Friday night, and who works the queue when the refund fails.

## Listen for

- Puts the step that cannot be taken back last, after everything that can still fail has already
  succeeded
- Separates undoing from making amends: the email cannot be removed, but a correction and a refund
  can be sent
- Everything checkable should be checked before the irreversible step, even at the cost of an
  extra round trip
- Some steps cannot be compensated at all, and the design has to make them unreachable from the
  failure path rather than compensate them
- What the customer experiences is part of the design: an apology and a refund is a real outcome
  with a cost, not a defect
- Asks why the reservation could be invalid at that point, because a check that late is itself the
  bug

## Expected knowledge

- A compensating step is a new action with its own failure modes, not a rollback
- Ordering steps by reversibility is a design lever

## Strong signals

- Asks what the reservation actually guarantees and for how long, before reordering anything
- Notices that the compensating step can itself fail and says where that ends up
- Quantifies how often the unwind is expected to happen before spending effort on it

## Weak signals

- Describes compensating actions for every step with no acknowledgement that one of them is not
  compensable
- Suggests delaying the email by an hour and calls that the fix
- Treats the refund as automatically successful

## Answer bands

### mid

- Reorders the steps so the email comes last.
- Names a compensating action for the charge.
- Does not notice that the compensating action can fail too.

### senior

- Distinguishes the reversible steps from the one that is not, and designs the sequence around it.
- Moves every validation ahead of the irreversible step and says what that costs.
- Follows the compensating actions through their own failure cases to a defined end state,
  without being asked what happens when the refund itself fails.

### lead

- Trades correctness against inventory: holding the seat longer costs sales, and says how they
  would decide with numbers.
- Sets a rate of unwound bookings the business will accept, rather than aiming at zero.
- Defines where automation stops and a human queue starts, and who staffs it.
- Treats the customer-facing outcome as a product decision made with the product owner.

## Follow-ups

- Reordering means holding a seat two minutes longer, and on Friday nights you sell out. How do
  you decide?
  probes: trading correctness against inventory with stated numbers rather than instinct
- The refund also fails. Now what?
  probes: terminal states, human queues, knowing when to stop automating
- How many of these a week would you accept before rebuilding the flow?
  probes: setting a threshold instead of chasing zero
