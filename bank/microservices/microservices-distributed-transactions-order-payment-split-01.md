---
id: microservices-distributed-transactions-order-payment-split-01
schema_version: 2
title: The card is charged and the order row never committed
category: microservices
topic: distributed-transactions
level: senior
tags: [transactions, correctness, failure-modes, idempotency]
time_estimate_min: 10
order: 170
links:
  related: [spring-transactions-checked-exception-01]
  deeper: [microservices-distributed-transactions-compensation-cannot-undo-01]
---

## Ask

Placing an order writes a row in your database and charges a card through an external provider.
The provider returns success, and your process is killed before the row commits. The customer has
paid and you have no order. How do you make that impossible?

## Tests

Whether the candidate can walk the individual crash points of a two-system change and design a
sequence where every one of them is recoverable.

## Ideal minimal answer

Commit a local record of the attempt, with your own reference, before calling the provider, so a
crash always leaves a trace; send that reference on the call so the provider recognises a
repeat. A separate sweep then finds attempts with no outcome, asks the provider what happened to
that reference, and drives each one to paid or refunded without a human reading it.

## Listen for

- There is no single commit available: one of the two systems will never join your transaction
- Records the intention locally and commits it before the outside call, so a crash always leaves a
  trace of what was being attempted
- Orders the steps deliberately, and can say what each crash point leaves behind and who cleans it
- A recovery step that asks the provider what happened, using a reference chosen by your side
- The outside call must be safe to repeat, which means the provider has to be able to recognise
  the repeat
- The end state is reached by something that runs later, not by the request that died

## Expected knowledge

- A database transaction spans one database
- Holding a transaction open across a network call to a third party is not viable

## Strong signals

- Insists on the recovery path being exercised on purpose rather than waiting for a real crash
- Notes that the provider timing out produces the same unknown as the crash, and the same recovery
  answers both
- Says how the customer experience is handled in the window before recovery runs

## Weak signals

- "Put both in a transaction"
- Proposes a coordinator across the two with no mention of what it costs or whether the provider
  supports one
- Relies on a finally block or a shutdown hook to clean up
- Assumes the process will get a chance to compensate

## Answer bands

### mid

- Sees that the two writes cannot be made atomic and that the ordering matters.
- Suggests recording something before the call so the situation is discoverable afterwards.
- Cannot yet say who resolves it or how.

### senior

- Lays out the sequence unasked and states, for each crash point, what is on disk and what is
  true at the provider.
- Adds a separate process that finds unresolved attempts and drives them to an end state.
- Makes the outside call safe to repeat and says what the provider needs from them for that.
- Refuses to leave any state that only a human can interpret.

### lead

- Decides how long an unresolved attempt may sit before a person is involved, and who that is.
- Judges the machinery against the volume and value of the orders rather than building the maximum.
- Names how the rarely-run recovery path is kept working — it is the code most likely to rot.

## Follow-ups

- Walk me through where the commit sits relative to the outside call, and what each crash point
  leaves behind.
  probes: whether they can enumerate the failure points rather than name a pattern
- Someone proposes a coordinator that holds a lock across both sides until they agree. What do you
  think?
  probes: why that is unavailable here, what it costs where it is available, blocking on a
  coordinator failure
- Nobody crashes for six months and your recovery code has never once run. Are you comfortable?
  probes: testing rare paths; deliberately exercising the path in production

## Sources

- https://microservices.io/patterns/data/saga.html
