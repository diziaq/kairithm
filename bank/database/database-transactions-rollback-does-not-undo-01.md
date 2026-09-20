---
id: database-transactions-rollback-does-not-undo-01
schema_version: 1
title: The rollback did not undo the charge
category: database
topic: transactions
level: junior
tags: [transactions, correctness, failure-modes]
time_estimate_min: 6
order: 210
links:
  deeper: [database-transactions-lost-update-wallet-01]
---

## Ask

A handler opens a transaction, inserts the order row, calls the payment provider, writes the
payment row, and commits. The payment row breaks a constraint, so the whole transaction rolls
back. The customer has been charged and has no order. What did the rollback actually undo, and
what would you change?

## Tests

Whether the candidate knows where a rollback stops — it restores rows and nothing else — and can
reorder the work so that the failure left behind is one somebody can repair.

## Listen for

- Says the two rows are gone and that nothing outside the database moved back
- Names effects that were never covered: the money taken, a mail sent, a message published, a
  file written
- Takes the call to the payment provider out of the transaction, and then says what the handler
  does when the call succeeds and the write afterwards fails
- Sees that with no order row the service has no trace that money was taken, so nothing can find
  it later
- Suggests writing down the intent before calling out, so a crash leaves something to act on

## Expected knowledge

- A rollback restores the rows the transaction changed; it does not reverse work done elsewhere
- A sequence is deliberately outside the rollback: the values it issued are not handed back, so
  gaps are normal in PostgreSQL and in MySQL `AUTO_INCREMENT`
- Keeping a transaction open across a call to another system holds its locks for the whole of
  that call

## Strong signals

- Asks how long the transaction stays open while the provider is thinking, and what that does
  when traffic is high
- Points out the gap cannot be removed, so the real choice is which order of steps leaves the
  repairable failure
- Says that repeating the whole handler must not take the money a second time

## Weak signals

- Believes the rollback also cancelled the charge
- Moves the commit earlier without saying what happens if the provider then fails
- Proposes catching the error and carrying on in the same transaction
- Talks only about the constraint, and never about the money

## Answer bands

### weak

- Says everything was undone because the transaction rolled back.
- Cannot name one effect the rollback failed to reverse.

### junior

- Says the rows are gone and the charge is not.
- Moves the provider call out of the transaction, or stores the record of the charge separately.
- Names one other effect a rollback would not have reversed.

### mid

- Orders the steps so the failure that survives is one somebody can clean up, and says which.
- Says what the service does when the provider succeeded and the write did not, including what
  the customer is shown.
- Notices the lock held while the handler waits on a third party, and what it costs under load.
- Says a repeat of the whole handler must not charge twice.

## Follow-ups

- Swap the order: take the money first, then insert the rows and commit. Which failure do you
  have now, and is it a better one?
  probes: whether they can compare two failure modes instead of hunting for a perfect order
- Order ids come straight from the database. A customer sees theirs jump by six and asks whether
  orders were deleted. Same bug or not?
  probes: gaps after a rollback, and why they are by design rather than a fault
- The provider takes eight seconds to answer and this runs during a sale. What else suffers?
  probes: locks and pooled connections held for the length of a remote call
- The handler throws after the money is taken and the caller sends the request again. What
  happens the second time?
  probes: repeat safety, without handing over the word

## Sources

- https://www.postgresql.org/docs/current/tutorial-transactions.html
- https://www.postgresql.org/docs/current/sql-createsequence.html
- https://dev.mysql.com/doc/refman/8.0/en/innodb-auto-increment-handling.html

## Notes

The point of the card is the boundary of the rollback, not the constraint. If the candidate only
debugs the constraint, ask what would have happened had the network dropped at the same line.

Two engine pins worth holding a candidate to:

- In PostgreSQL an error puts the whole transaction into an aborted state; every later statement
  fails with "current transaction is aborted" until rollback, unless a savepoint was set first.
  So "catch it and carry on" does not work there.
- In MySQL/InnoDB a statement error usually rolls back only that statement, and the transaction
  can continue — which is exactly why a candidate who has only used one engine is often confident
  about the wrong thing.

Sequence and `AUTO_INCREMENT` values are not rolled back on either engine; the gap is the price of
not serialising every insert behind one counter.
