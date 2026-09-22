---
id: microservices-messaging-poison-message-blocks-01
schema_version: 2
title: One bad message stops the queue for an hour
category: microservices
topic: messaging
level: junior
tags: [messaging, failure-modes, operations, correctness]
time_estimate_min: 6
order: 100
links:
  related: [kafka-retries-blocking-loop-01]
  deeper: [microservices-messaging-outbox-dual-write-01]
---

## Ask

One message on your queue makes the consumer throw an exception every single time it is handled.
The consumer picks it up, fails, puts it back, and picks it up again. Nothing else has been
processed for an hour. What do you do in the next ten minutes, and what do you change afterwards?

## Tests

Whether the candidate separates unblocking the flow from discarding data, and knows that a
failing handler must have a bounded number of attempts.

## Ideal minimal answer

Get that one message out of the path so the rest flow again, and keep it somewhere it can be
inspected rather than deleting it. Then cap how many times any message is tried, so one that can
never succeed stops holding up the queue, and make sure somebody is told the set-aside pile is
not empty.

## Listen for

- Get the offending message out of the path of the good ones, first
- Keeps it rather than dropping it: it goes somewhere it can be inspected and put back later
- A cap on attempts per message, so one that can never succeed stops holding up the rest
- Someone has to be told the set-aside pile is not empty, or it becomes a silent data loss
- Distinguishes a message that will never succeed from one failing because the database is down
  right now — the second should not be set aside

## Expected knowledge

- A consumer that fails and does not acknowledge will usually be handed the same message again
- Setting a message aside is an operational decision, not an error-handling detail

## Strong signals

- Asks whether other messages behind it are now stale or out of order when the flow resumes
- Wants the failure recorded with enough context to reproduce it without the message itself

## Weak signals

- Catches the exception and swallows it
- Deletes the message manually and considers the matter closed
- Adds more attempts, or a longer wait, with no cap
- Tells how a stuck queue was cleared at a previous job and never says what to do in the next ten
  minutes

## Answer bands

### weak

- Suggests catching everything and continuing, with no record of what was skipped.
- Deletes the message and moves on.
- Cannot say what should happen the next time one arrives.

### junior

- Moves the message out of the way and keeps it somewhere.
- Adds a limit on how many times a message is tried.
- Says somebody needs to look at the ones that were set aside.

### mid

- Separates a message that is permanently unhandleable from one failing for a temporary reason,
  and treats them differently.
- Gives the set-aside pile an owner, an alarm and a way back into the flow.
- Notices, before anyone raises it, what the hour of backlog does to everything behind it when
  processing resumes.

## Follow-ups

- You move it aside. Three months later there are forty thousand of them. What went wrong?
  probes: whether the set-aside place has an owner, an alarm and a route back
- The database was down for five minutes and now every message from that window has been set
  aside. Was that right?
  probes: distinguishing a bad message from a bad moment
- It fails because the producer sent nothing where your code needed a value. Whose problem is it?
  probes: contract and validation at the producing edge rather than the consuming one

## Notes

Keep this at the pattern level. If the candidate starts discussing one broker's configuration
surface, steer them back to what should happen to the message and who finds out.
