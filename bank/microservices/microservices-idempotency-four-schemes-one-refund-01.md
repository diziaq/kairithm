---
id: microservices-idempotency-four-schemes-one-refund-01
schema_version: 1
title: Four services, four ways of not paying twice
category: microservices
topic: idempotency
level: lead
tags: [correctness, retries, failure-modes, operations]
time_estimate_min: 10
order: 60
links:
  related: [microservices-distributed-transactions-compensation-cannot-undo-01, spring-proxying-retry-transaction-order-01]
---

## Ask

A refund crosses four of your services, and each one defends itself differently: one has a
uniqueness rule in its own database, one keeps a marker in a shared cache for an hour, one
compares the incoming request against the last fifty rows it wrote, and one trusts callers not to
send anything twice. Finance found ninety refunds paid out twice last month. You have one quarter
and one team. What do you change, what do you leave alone, and what does each choice cost the
people who keep it running afterwards?

## Tests

Whether the candidate can rank mechanisms by how they fail rather than by how modern they are,
choose between them under a stated budget, and name the running cost each one leaves behind.

## Listen for

- Ranks the four by what each does when something goes wrong, not by which is the current
  fashion: only the rule inside the store is settled by the store itself
- Names the failure of the cache one in the money: the marker is lost on a failover or thrown out
  when memory runs short, the second request looks new, and that customer is paid twice
- Comparing against recent rows is a guess in both directions — two genuine refunds of the same
  amount look identical, and a repeat arriving on the fifty-first row walks straight through
- Asks what a repeat actually costs in each flow before spending anything, and refuses to pay the
  same price everywhere
- Decides where the rule is enforced — at each service's own write, or once in front of them all
  — and says what a shared checker does when it is down: either refunds stop, or repeats get
  through, and somebody has to choose which in advance
- Has an answer for the service nobody can change: the rule moves to its caller, or the repeats
  are found afterwards and put right
- Names the standing cost of each option: a table that grows and needs a cleanup job someone
  owns, a cache that needs a memory budget and a story for losing its contents, a shared checker
  that every refund now depends on and that pages a human at three in the morning
- Adds a daily comparison against the money actually moved, because whatever is chosen will let
  something through, and says who acts on what it finds
- Sees that the callers must send something stable for any of this to work, so the first change
  is in the contract with them, not in the four services

## Expected knowledge

- A caller whose request timed out cannot know whether it was applied
- Spending on stopping a repeat and spending on finding one are different budgets

## Strong signals

- Asks what the callers send today, because nothing works until two attempts can be tied together
- Says out loud which of the four he will not touch this quarter, and why that is the right call
- Sorts the flows into those where a repeat must never happen and those where it only has to be
  found by the next morning
- Treats the ninety refunds as evidence to be explained — which of the four let them through —
  before designing anything

## Weak signals

- Standardises everything on one mechanism without pricing it per flow
- Puts a single shared lookup in front of every write with no answer for it being unavailable
- Announces a policy that every endpoint must tolerate repeats, with no owner, no store and no
  migration behind it
- Keeps the row comparison because it has not caused a problem yet
- Promises all four rewritten in the quarter without saying what is dropped to pay for it

## Answer bands

### mid

- Separates the four by mechanism and says why trusting callers is not one.
- Names one concrete way the cached marker disappears.
- Proposes a single approach everywhere, with little on what it costs afterwards.

### senior

- Says what happens to the money in a specific failure of each of the four.
- Picks where the rule is enforced and states what that place depends on to be correct.
- Notices that the callers have to send something stable before any of it holds.
- Weighs the machinery against what one repeat costs in that particular flow.

### lead

- Chooses a target per flow from the budget given, and leaves the flows not worth the quarter
  alone with a reason.
- Names what each option costs the team after the project ends: a cleanup job, a memory budget, a
  new dependency on the write path, a new reason to be woken up.
- Puts a way to find and correct the ones that get through behind whatever is chosen, and says
  who runs it.
- Sequences the work so the agreement with the callers lands before the services change.
- States what is still possible after the quarter, and how the team would learn it happened.

## Follow-ups

- The cache behind the second service is failed over at midnight and the last few seconds of
  writes are gone. A refund request arrives twice around then. What happens to that customer's
  money?
  probes: whether the scheme survives the failure of the thing it rests on
- One of the four is bought software and nobody here can change a line of it. What do you do
  about that one?
  probes: moving the rule to the caller or the edge; correction where prevention is not available
- You put one shared checker in front of all four and it is unreachable for ten minutes on a
  Friday afternoon. What did you decide would happen?
  probes: choosing in advance between refusing refunds and letting repeats through, and who owns it
- It is six months later and the quarter's work shipped. How would you know the problem has not
  come back?
  probes: reconciliation as a standing capability with an owner, rather than a one-off fix

## Sources

- https://docs.stripe.com/api/idempotent_requests
- https://www.rfc-editor.org/rfc/rfc9110#name-idempotent-methods

## Notes

The card is about choosing and paying, not about naming a pattern. If the candidate designs one
perfect mechanism and applies it everywhere, push on the quarter, the team of one, and the
service that cannot be changed.
