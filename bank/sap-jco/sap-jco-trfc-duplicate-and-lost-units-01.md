---
id: sap-jco-trfc-duplicate-and-lost-units-01
schema_version: 2
title: Two movements booked twice and three that never arrived
category: sap-jco
topic: trfc-qrfc
level: senior
tags: [idempotency, consistency, delivery-semantics, failure-modes]
time_estimate_min: 9
order: 175
links:
  related: [kafka-offsets-external-store-01]
  deeper: [sap-jco-qrfc-blocked-queue-01]
---

## Ask

Your Java listener receives goods movements from SAP over tRFC and keeps a table of transaction
ids so that nothing is ever processed twice. During a database failover last month, two movements
were booked twice — and three others never reached your system at all, although SAP shows them as
sent and has nothing outstanding for that destination. Both of those in one incident. How?

## Tests

Whether the candidate can treat receiver-side duplicate protection as a small state machine that
has to commit together with the business data, and can reason about what each wrong ordering
produces.

## Ideal minimal answer

The duplicates are business rows that committed while the id record did not, so the repeat
looked new; the losses are worse, because the id was written before the work committed, so the
repeat was answered as done and the sender discarded it. The check must say run it for a unit
that failed, the id and rows must commit together, and the record kept until the sender
confirms.

## Listen for

- The two failures are opposite mistakes in the same mechanism, which is why one incident can
  produce both
- The duplicates: the business rows committed but the record of the id did not, or went to a
  store that lost its last writes, so the repeat arrived and looked new
- The disappearances are the worse bug — the id was written and answered as "seen" before the
  work was actually committed, so the repeat was answered with "already done", the sending side
  treated the unit as complete and removed it
- The check JCo makes before executing a unit has to say "not done, run it" for a unit that
  failed or half-ran last time, and "done, skip it" only for one that definitely committed
- Which means the id and the business effect have to land in one commit, in one database, not in
  two writes that can be separated by a crash
- Forgetting an id is its own decision: the sending side confirms a unit once it knows it
  succeeded, and that confirmation — not the local commit — is the point at which the record can
  safely go
- A repeat can also arrive while the first attempt is still running, possibly on another node, so
  the protection has to be a constraint the database enforces and not a read followed by a write

## Expected knowledge

- A JCo server registers a handler that is asked about a unit before it runs, told when the unit
  completed, and told again when the sender confirms it
- tRFC is at-least-once; the transaction id is the only thing that makes a repeat recognisable

## Strong signals

- Points out that the silent losses would never have been noticed if somebody had not counted
- Puts the id row and the business rows in one transaction and says so explicitly
- Distinguishes a unit that failed from one that was skipped, and wants them countable separately
- Asks how long ids are kept and what happens to a very late repeat after they are gone
- Asks what the receiving logic does if it is simply run twice, as a second line of defence

## Weak signals

- Keeps the ids in a cache, or in a different store from the business data, and sees no problem
- Records the id first so nothing can slip through, without seeing what that does to a failure
- Proposes checking for existing ids and then inserting, with no mention of two of them at once
- Suggests comparing counts every morning as the fix

## Answer bands

### mid

- Sees that the id record and the business write can come apart and explains the duplicates.
- Suggests putting both in one transaction.

### senior

- Explains both directions of the failure, including why marking a unit as seen too early makes
  documents vanish for good.
- States what the pre-execution check must answer for a unit that failed halfway through.
- Makes the id and the business data commit together, and relies on the database to reject a
  second insert rather than on a prior read.
- Separates the moment the unit is complete from the moment the sender confirms it, and ties the
  cleanup to the latter.

### lead

- Weighs strict tracking against making the posting itself repeatable, and says when each is
  worth its cost.
- Decides how long ids are kept, from how long the sending side can still retry, and who owns
  the table when it grows.
- Says what would have detected the silent losses on the night rather than a month later.

## Follow-ups

- The same unit arrives on two of your nodes at the same moment. What stops both from booking it?
  probes: a database constraint versus a read-then-write in application code
- The team's instinct is to write the id down the moment the unit shows up, so nothing can slip
  past. What does that buy and what does it cost?
  probes: whether they see the silent loss that early marking creates
- How long would you keep those ids, and what did you use to pick the number?
  probes: tying the retention window to how long the sender may still repeat a unit
- The warehouse manager asks whether a movement can still be booked twice after your fix. What do
  you promise, and what do you not?
  probes: honesty about the remaining window and the second line of defence

## Notes

The receiver-side callbacks are `JCoServerTIDHandler` — `checkTID`, `commit`, `rollback` and
`confirmTID`. The documented rule that matters here is that `checkTID` must return `true` for a
unit that failed on a previous attempt, or it will never be delivered again. A candidate who
describes the state machine without the method names has answered this card.

Verified, and the load-bearing half of this card: the documented contract is that `checkTID` has
to return `true` for a transaction id that failed on a previous attempt, or the unit will never
be delivered again. `false` is the answer only for one that definitely committed. Returning
`false` for a unit that did not complete is a permanent data-loss bug in the handler — which is
exactly the three missing movements in the scenario.

Verified in the decompiled JCo 3.1.14, replacing the second half of the previous flag: a throwing
`commit` callback causes a rollback and a system failure. `com.sap.conn.jco.server.JCoServerTIDHandler`
declares exactly `checkTID`, `confirmTID`, `commit` and `rollback`. In
`com.sap.conn.jco.rt.AbstractServerConnection` the call to `onCommit(tid)` is wrapped, and its
`catch (Throwable)` converts whatever came out into `new RfcException(RfcRc.RFC_FAILURE, "Commit
fault: " + message, RfcErrorGroup.RFC_ERROR_SYSTEM_FAILURE, ...)`. The enclosing
`catch (RfcException)` then calls `onRollback(tid)` for the same transaction id and rethrows. So
if `commit` throws, JCo calls `rollback` for that unit and reports a system failure to the sender
— it is specified after all, and a handler that throws out of `commit` gets a rollback it may not
have been expecting. Worth knowing, but do not ask a candidate to state it.

NEEDS-REVIEW — one sentence, and it is ABAP-side rather than merely unchecked. The precise
conditions and timing under which the sending system re-sends a unit whose `confirmTID` was lost
belong to the tRFC scheduler inside SAP and are not in the client jar; what is documented is only
that the sender keeps the record while the unit is unconfirmed, and that a stale record is
eventually cleaned up. Do not ask a candidate to state the retry schedule. The safe position the
card is built on — a repeat is possible until the sender has confirmed, so keep the record until
then — is sound regardless.

## Sources

- https://help.sap.com/doc/saphelp_nwpi711/7.1.1/en-US/48/88b5c5521672d3e10000000a42189c/content.htm
- https://help.sap.com/doc/saphelp_nw73ehp1/7.31.19/en-US/41/c78586b4f349dc90d522a75cb1a5bd/content.htm
- https://help.sap.com/doc/saphelp_nw74/7.4.16/en-US/48/99b963ee2b73e7e10000000a42189b/content.htm
