---
id: java-exceptions-swallowed-in-loop-01
schema_version: 2
title: Ten thousand invoices, and a log line that says nothing
category: java
topic: exceptions
level: junior
tags: [failure-modes, observability, correctness]
time_estimate_min: 5
order: 500
links:
  deeper: [java-exceptions-lost-in-cleanup-01]
  related: [microservices-messaging-poison-message-blocks-01]
---

## Ask

You are reviewing a nightly job. It loops over ten thousand invoices, and inside the loop it has
`try { send(invoice); } catch (Exception e) { log.error("failed to send"); }`. At the end it logs
"sent 10000 invoices" and exits successfully. What do you say in the review?

## Tests

Whether the candidate can see what a caught failure hides — from the operator, from tomorrow's run
and from the customer waiting for the invoice.

## Ideal minimal answer

Says the caught object is never handed to the logger, so there is no cause and no stack trace,
and the line does not say which invoice. Points out that the closing count of ten thousand is
not true and the job still exits successfully, and wants the failed invoices recorded somewhere
rather than only logged.

## Listen for

- The log line carries nothing usable: not which invoice, not why, and no stack trace, because the
  caught object is never passed to the logger
- The closing count is a lie; nothing in the output distinguishes ten thousand sent from none
- Catching everything also catches the programming errors, so a null dereference inside `send` looks
  exactly like a refused connection
- Whether to carry on or stop is a decision someone has to take deliberately; both are defensible,
  silence is not
- Wants the failures recorded somewhere that a later run can act on, not only written to a log

## Expected knowledge

- The logger produces a stack trace when the caught object is handed to it
- The difference between one item failing and the run failing

## Strong signals

- Asks what happens tomorrow night to the invoices that failed tonight
- Separates failures that will fail again from ones that might not
- Points out the job exits successfully, so nothing will ever alert

## Weak signals

- "You should never catch that type" as a rule, with no account of the damage here
- Adds the stack trace and considers the review finished
- Rethrows everything so one bad invoice stops the run, without saying that is a choice

## Answer bands

### weak

- Comments on formatting or on the log level and stops.
- Says the code looks fine because failures are being handled.
- Cannot say what an operator would see the next morning.

### junior

- Says the log line should include the cause and which invoice failed.
- Notices that the final count does not reflect what happened.
- Suggests reporting the failures somewhere rather than only logging them.

### mid

- Separates a bug in the job from a failure of one invoice, and treats them differently.
- Says continuing is a decision and names what the job should report when it does.
- Wants the failed items retained so the next run or an operator can act, and wants the exit status
  to reflect reality.

## Follow-ups

- Two hundred of them fail tonight. What happens tomorrow night?
  probes: whether failures are recorded anywhere a later run can pick them up
- One fails because the invoice has no customer at all, another because the mail server refused the
  connection. Same treatment?
  probes: separating a bug from a temporary fault, and whether sending again makes sense
- Nobody reads the log. How does anyone find out?
  probes: exit status, alerting, and counts that mean something

## Notes

A junior who only says "log the exception object" has half of it. The other half is that the run
reports success, which is the part that keeps this invisible for months.
