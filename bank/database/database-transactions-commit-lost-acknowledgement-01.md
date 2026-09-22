---
id: database-transactions-commit-lost-acknowledgement-01
schema_version: 2
title: The commit went through, the caller never heard
category: database
topic: transactions
level: senior
tags: [transactions, idempotency, retries, failure-modes]
time_estimate_min: 12
order: 212
links:
  related: [database-consistency-read-your-writes-profile-01, microservices-idempotency-non-idempotent-side-effect-01]
---

## Ask

A payout service commits, and the connection drops before the response reaches the caller. The
caller sends the request again and the payout goes out twice. The team's proposal is to widen the
transaction so it covers more of the handler. Where is the gap really, and what would you build?

## Tests

Whether the candidate separates a durable commit from a delivered answer, and builds a way for
the caller to discover the outcome instead of guessing it.

## Ideal minimal answer

A commit is durable; the answer is a separate delivery that was lost, so the caller cannot tell
'nothing happened' from 'I was not told', and widening the transaction leaves the same gap after
it. Write a row keyed by a reference the caller creates before its first attempt, in the same
transaction as the payout, and have the second call return that outcome instead of paying again.

## Listen for

- Says the commit is a fact in the database and the answer is a separate delivery that can be
  lost, so the caller cannot tell "it did not happen" from "I was not told"
- Points out that a wider transaction makes the window larger, not smaller, because the same gap
  sits after any commit
- Writes something in the same transaction as the payout that a later attempt can recognise —
  a row keyed by a reference the caller supplies
- Says the second attempt should find that row and return the first outcome, instead of doing the
  work again or failing
- Knows the reference has to come from the caller and be the same on the second try, so it is
  created before the first attempt rather than by the server
- Asks what the client does on a timeout today: how many times it tries again, and how fast
- Treats a refused connection differently from a timeout — one certainly did nothing, the other
  is unknown

## Expected knowledge

- A commit is durable once its log record is flushed; the answer travelling back is a separate
  and unprotected step
- A uniqueness rule is the cheap way to make a repeat collide, and the collision is decided by the
  database rather than by a check the code ran first
- A look-then-write check on two connections can pass on both before either writes

## Strong signals

- Names the case where the first attempt is still running when the second arrives, and says what
  the second one waits on
- Says how long the record of an attempt is kept, and what a repeat arriving after that gets
- Considers the second request carrying the same reference but a different amount, and decides
  what the service does
- Separates the caller's need (an answer) from the operator's (something to reconcile), and serves
  both
- Notes that no protocol closes the window completely, and says what is settled out of band

## Weak signals

- Proposes a longer transaction, or one that stays open across the response
- Suggests a select for an existing payout before inserting, and stops there
- Says the client should simply not try again
- Reaches for a distributed transaction spanning the payment provider without costing it
- Tells the story of a double payout at a previous job and never says what they would build here

## Answer bands

### mid

- Says the work happened and the answer was lost, and that trying again blindly repeats it.
- Proposes a marker in the database that the second attempt can find.

### senior

- Puts the marker in the same transaction as the payout, so the two cannot disagree.
- Says where the reference comes from and why the server cannot invent it.
- Describes what the second call returns, and raises the case where the first is still in flight
  before being asked about it.
- Explains why widening the transaction does not close the window.

### lead

- Decides how long the record is kept and what a late repeat is told, tying it to how disputes
  are settled.
- Chooses between making the second caller wait and answering "still going", from the caller's
  own timeout budget.
- Says which part is reconciled out of band anyway, because the window never fully closes.

## Follow-ups

- The first attempt is still running when the second arrives. What does the second one do while
  it waits?
  probes: two attempts in flight, and whether the store or the code decides the race
- The caller makes up a fresh reference each time, because to it each attempt is a new request.
  Does your design still help?
  probes: where the key must be created for the mechanism to mean anything at all
- Same reference, but the amount in the second request is different. What happens?
  probes: whether the stored marker covers the content, and what a mismatch means
- A week later the caller sends it once more. What comes back?
  probes: how long the record is kept, and the answer for a repeat after it is gone

## Sources

- https://www.postgresql.org/docs/current/wal-reliability.html
- https://docs.stripe.com/api/idempotent_requests

## Notes

The distinction the card is built on: a commit is a local durable fact, and the caller learning
about it is a message over a network. Nothing inside the database can make those two happen
together, which is why the answer has to be a protocol between caller and service rather than a
transaction setting.

Figures to release when asked:

- The caller is a scheduler that retries three times with a two-second gap, then gives up.
- Payouts run at about 30 per second at peak; duplicates were found twice last quarter.
- Nothing today ties a request to the row it produced.

Watch for the candidate who says "make it idempotent" and then cannot say where the key comes
from, what the second call returns, or what happens when both attempts are in flight. The word is
not the answer. The two hard parts are the key's origin — the caller, before the first attempt —
and the in-flight case, which needs the uniqueness rule to be what blocks the second writer,
because a look-then-write check lets both through.
