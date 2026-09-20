---
id: sap-jco-stateful-sessions-context-required-01
schema_version: 1
title: The save reports success and the change is gone
category: sap-jco
topic: stateful-sessions
level: senior
tags: [transactions, consistency, correctness, concurrency]
time_estimate_min: 9
order: 160
links:
  deeper: [sap-jco-stateful-sessions-leaked-contexts-01]
---

## Ask

A two-step sequence works in test and fails about one time in fifty in production: the first call
locks and changes a document, the second call saves it. In production the second call reports
success and the change is not there. What is different in production?

## Tests

Whether the candidate knows that pooled calls are independent sessions in SAP, and can explain
why that turns a correctness bug into a concurrency-dependent one.

## Listen for

- Each call takes whatever connection the pool gives it, so the two calls can land on two
  different connections and therefore two different sessions in SAP
- The work registered by the first call belongs to its own session; a save issued from another
  session has nothing to save, which is why it reports success and nothing happens
- Test had one user and one connection, so the two calls almost always got the same one;
  production has concurrency, which is what makes it one in fifty
- The fix is to declare the sequence stateful — `JCoContext.begin(destination)` before it and
  `JCoContext.end(destination)` in a `finally` — so every call in that scope uses the same
  connection
- The same reasoning covers a lock taken in one call and relied on in the next, and any value
  the function group kept between calls

## Expected knowledge

- Changes made through this kind of interface are registered and applied when the work is
  committed
- A lock belongs to the session that took it

## Strong signals

- Says the bracket has to cover the error paths too, or the connection is never given back
- Points out a stateful sequence takes its connection out of circulation for its whole life, so
  it should be short and rare rather than the default
- Notes the scope is tied to the thread that opened it, so handing the sequence to another
  thread breaks it in the same way
- Asks how such a rare failure would ever have been caught in test, and answers it

## Weak signals

- Blames network flakiness or SAP for a one-in-fifty failure
- Adds a retry of the second call
- Believes any two calls to the same destination are automatically in the same session

## Answer bands

### mid

- Suspects the two calls are not related to each other on the SAP side.
- Knows there is a way to tie a sequence of calls together and names roughly what it does.

### senior

- Explains the pool handing out independent connections and why that means independent sessions.
- Explains why the second call reports success while doing nothing.
- Accounts for the one-in-fifty rate from the concurrency difference between the environments.
- Brackets the sequence correctly, including the failure path.

### lead

- Puts the bracket in one place so no caller can forget it, rather than trusting a convention.
- Weighs the cost of holding a connection against the correctness it buys, and keeps the default
  path stateless.
- Says how the team would catch the next instance of this class of bug before production.

## Follow-ups

- Why would this be almost impossible to reproduce on a developer machine?
  probes: whether they can connect the rate to the number of connections in play
- The middle of the sequence throws. What has to happen, and what happens if it does not?
  probes: releasing what was reserved, and the leak that follows
- The team wants to run the two steps from different threads for speed. What do you tell them?
  probes: the scope being bound to one thread and one connection
- What stops this from being the default for every call?
  probes: the cost of reserving a connection for a whole sequence

## Notes

Verified: `JCoContext.begin(destination)` starts a stateful call sequence, and the same physical
connection is reserved for exclusive use by that sequence until it ends — which is what keeps the
ABAP session, and therefore the registered changes and the locks, alive across the two calls.
Contexts nest: `end` has to be called as many times as `begin` was, and the connection is
released only when the outermost one ends.

Verified: the scope is bound to the calling thread by default. In a managed environment where a
unit of work may move between threads, an application registers a `SessionReferenceProvider`
through `Environment.registerSessionReferenceProvider`, and JCo then asks that provider whether
the session is still alive rather than relying on the thread. This resolves the question the
previous review flag left open — a candidate who says "it follows the thread unless you tell JCo
otherwise" is correct.

## Sources

- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
- https://github.com/cemeng/sap-integration/blob/master/sapjco3-darwinintel64-3.0.14/javadoc/com/sap/conn/jco/JCoContext.html
