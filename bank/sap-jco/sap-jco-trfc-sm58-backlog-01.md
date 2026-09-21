---
id: sap-jco-trfc-sm58-backlog-01
schema_version: 2
title: Four thousand entries waiting in SM58
category: sap-jco
topic: trfc-qrfc
level: mid
tags: [retries, idempotency, failure-modes, delivery-semantics]
time_estimate_min: 8
order: 70
links:
  deeper: [sap-jco-trfc-duplicate-and-lost-units-01]
---

## Ask

SAP pushes documents to your registered Java listener over tRFC. Your listener was down for two
hours overnight and `SM58` now shows four thousand entries for that destination. What happens to
them, and what do you expect to see on your side when the listener comes back?

## Tests

Whether the candidate understands tRFC as a store-and-forward mechanism with at-least-once
delivery, and can predict both the recovery and its effect on their own service.

## Ideal minimal answer

Nothing is lost: the four thousand units are recorded in the sending SAP system and something on
the SAP side retries them once the program is registered again, and an entry only clears when
the unit is confirmed. Delivery is at-least-once, so a unit can arrive twice and my listener has
to recognise its transaction id, and the backlog drains as a burst rather than a trickle.

## Listen for

- The units are recorded in the sending SAP system and are not lost while the receiver is away
- They are retried — by the retry job or scheduler on the SAP side, or by hand from the monitor —
  so the backlog drains once the program is registered at the gateway again
- Each unit carries a transaction id; the guarantee is at-least-once, so a unit already processed
  can arrive again if its confirmation was lost
- Duplicate protection is the receiver's job: remember the transaction id and refuse to execute
  a second time, rather than hoping
- When the backlog drains it arrives as a burst, not a trickle — four thousand units as fast as
  they can be dispatched, against a listener sized for normal traffic
- tRFC gives no ordering across those four thousand units

## Expected knowledge

- A registered server program at an SAP gateway, and a TCP/IP destination in `SM59` that names
  its program id
- The JCo server side is told about a unit before it is executed and again when it is finished

## Strong signals

- Says exactly what the check on an incoming transaction id must answer: already committed means
  skip, previously failed means run it again
- Asks whether these documents are order-sensitive, and treats that as a different design
- Plans for the burst: bounded concurrency on the listener, or the SAP side throttled, so
  recovery does not take out the downstream

## Weak signals

- Believes tRFC delivers exactly once and no duplicate handling is needed
- Thinks the entries are lost while the listener is down
- Would clear the monitor to make the number go away

## Answer bands

### weak

- Assumes the traffic is gone and asks the business to re-send.
- Cannot say where the four thousand units are stored or who retries them.

### junior

- Knows the units are held in SAP and get retried when the receiver is available.
- Expects them to be processed after the restart.

### mid

- Describes the retry path and what makes a unit disappear from the monitor.
- Says a unit may arrive twice and that the receiver has to recognise it.
- Predicts the burst and asks whether the listener and everything behind it can take it.

### senior

- States the delivery guarantee precisely and where de-duplication actually happens.
- Says what the check must answer for a unit that failed halfway through last time.
- Raises ordering as a separate property that this mechanism does not provide, and what it would
  cost to get it.

## Follow-ups

- The listener comes back and the first thing you see is a document you already booked last
  night. How did that happen and what should have stopped it?
  probes: at-least-once delivery, lost confirmations, and where the de-duplication lives
- The backlog drains in ninety seconds and your downstream falls over. What would you change?
  probes: bounded concurrency and whether recovery is designed or accidental
- The business asks whether the documents will be booked in the order they were raised. What do
  you say?
  probes: ordering is not provided here; opens the queue design question
- One unit fails every time it is retried. Who decides what happens to it?
  probes: poison-entry handling and ownership

## Notes

`SM58` shows transactional RFC units recorded in the SAP system, including those bound for an
external receiver. Re-sending is not the recovery path; the units are already recorded.

Verified in the decompiled JCo 3.1.14, supporting the second `## Expected knowledge` bullet:
`com.sap.conn.jco.server.JCoServerTIDHandler` declares exactly four methods — `checkTID`,
`confirmTID`, `commit` and `rollback` — each taking the `JCoServerContext` and the transaction id
as a string. `checkTID` is the only one that returns anything, a `boolean`. It is registered on
the server through `JCoServer.setTIDHandler`. A candidate who describes "asked before, told when
done, told again when the sender confirms" without the method names has answered this card.

Verified: which mechanism retries the backlog depends on how the destination is set up. For a
destination registered with the tRFC scheduler in `SMQS`, the scheduler dispatches and retries
units on its own. For a destination that is not registered there, the classic report `RSARFCEX`
is the scheduled sweep that reprocesses failed units. The two are complementary, not
alternatives. Do not hold a candidate to either name — "something on the SAP side retries them"
is the answer this card wants.

Interviewer accuracy warning, because this one catches interviewers out too: SAP's own
documentation describes the *application-level outcome* of tRFC as "exactly once". The
*mechanism* underneath is redelivery until confirmed, with duplicate execution prevented only
because the receiver checks the transaction id. A candidate who says "SAP calls this exactly
once, but the receiver still has to de-duplicate by transaction id" is more right than one who
says either half alone. Do not mark down the phrase; mark down the belief that no de-duplication
is needed.

## Sources

- https://help.sap.com/doc/saphelp_nw74/7.4.16/en-US/48/99b963ee2b73e7e10000000a42189b/content.htm
- https://help.sap.com/doc/saphelp_em92/9.2/en-US/48/821b412ddd3cb8e10000000a42189d/content.htm
- https://help.sap.com/docs/SAP_NETWEAVER_700/108f625f6c53101491e88dc4cf51a6cc/6273241e03337442b1bc1932c2ff8196.html
