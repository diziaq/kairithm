---
id: microservices-consistency-two-services-disagree-01
schema_version: 1
title: Billing says active, access control says cancelled
category: microservices
topic: consistency
level: senior
tags: [consistency, ownership, correctness, operations]
time_estimate_min: 9
order: 160
links:
  related: [microservices-ownership-paged-for-someone-elses-data-01]
---

## Ask

Billing says the subscription is active. Access control says it was cancelled three days ago. Each
is reading its own data and each is internally consistent. A paying customer is locked out right
now. How do you work out which one is wrong, and how do you stop it happening again?

## Tests

Whether the candidate insists on a single owner for a fact, and designs for the copy drifting
rather than assuming updates always arrive.

## Listen for

- Asks which service owns the fact "is this subscription active", and expects exactly one answer
- The other one holds a copy, so the question becomes how the copy is fed and how far behind it
  may legitimately be
- One dropped or mishandled update leaves the copy wrong forever, because nothing ever revisits it
- Wants something that periodically compares the two and reports how many disagree, rather than
  trusting the updates
- Immediate move and durable fix are separate: unblock this customer by hand, then go and count
  how many others are in the same state
- Asks what the copy is even for, because sometimes the answer is to ask the owner at read time

## Expected knowledge

- An update that is sent and lost produces silence, not an error
- A copy that is only ever written by events converges only if every event lands

## Strong signals

- Treats the count of mismatches as a signal with a threshold, not a one-off script
- Asks whether the two disagree about the fact or about the moment — a cancellation timestamp
  either side of a boundary
- Considers rebuilding the copy from the owner as a routine operation rather than an emergency

## Weak signals

- Picks whichever service looks more authoritative to them and moves on
- Replays the events and calls it fixed without asking how many were lost
- Proposes a shared table both services read

## Answer bands

### mid

- Works out which service should be believed and fixes the customer.
- Sees that an update went missing somewhere between the two.
- Stops at replaying the update, with nothing that would catch the next one.

### senior

- Establishes a single owner for the fact and reduces the other side to a copy with stated
  freshness.
- Designs something that compares the two sides on a schedule and raises the count of
  disagreements.
- Goes looking for the whole affected population rather than closing the one ticket.
- Says what the access decision should do when its copy is known to be stale.

### lead

- Settles the ownership argument between the two teams and says on what basis.
- Decides how much the business can tolerate being wrong in each direction — letting a cancelled
  user in, or locking a paying one out — and designs to that.
- Puts the reconciliation count in front of someone whose job it is to care about it.

## Follow-ups

- You unblock this customer. How many others are wrong at this moment?
  probes: whether they go after the population rather than the ticket
- The update was sent and never arrived. What in your design ever notices?
  probes: detection as well as prevention; a sweep comparing both sides
- Both teams insist theirs is the authoritative one. How do you settle it?
  probes: making an ownership decision, and that a duplicated fact needs one owner
