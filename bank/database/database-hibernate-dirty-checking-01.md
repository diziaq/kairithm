---
id: database-hibernate-dirty-checking-01
schema_version: 2
title: The save call nobody needed, until they did
category: database
topic: hibernate
level: junior
tags: [correctness, transactions, failure-modes]
time_estimate_min: 6
order: 410
links:
  related: [spring-transactions-partial-save-01]
  deeper: [database-hibernate-entity-identity-01]
---

## Ask

A colleague deleted the `save()` call from a service method that loads a customer, sets a new
phone number and returns. The tests pass and the number still changes in the database, so they
are removing it everywhere. In a second method — same three lines — the change is now lost.
What is different about the two?

## Tests

Whether the candidate knows that a loaded row is watched for the length of the unit of work and
written back without being asked, and can say what puts an object outside that watching.

## Ideal minimal answer

In the first method the customer is still held by an open unit of work, so the change is
compared against the loaded values and written; in the second the object is outside any open
unit of work, so nobody compares it and the change is lost.

## Listen for

- While the unit of work is open, the loaded object is compared against the values it was read
  with, and a difference becomes an update
- In the second method the object is no longer held by an open unit of work, so nobody compares
  it and nobody writes it
- The update is sent at the end of the unit of work, not on the line that set the field
- Says the deleted call was doing nothing in the first method and is the only thing that helps in
  the second
- Does not claim that a setter reaches the database

## Expected knowledge

- That the unit of work has a start and an end, and the write happens at the end
- What it means for an object to be held by one, or not
- Hibernate 6 and Jakarta Persistence behave the same way here as older versions did

## Strong signals

- Asks where the boundary is declared before answering, rather than assuming it is the method
- Says what is in the row if the method throws after the field is set
- Notices that a method meant only to read can still send an update this way, and calls that a
  hazard rather than a convenience

## Weak signals

- "It saves everything by itself" with no boundary anywhere in the answer
- Puts the call back everywhere to be safe and cannot say what it does in the first method
- Believes the update is sent when the setter runs
- Says the second method needs a bigger timeout or a retry

## Answer bands

### weak

- Says the framework writes things on its own and cannot say when.
- Cannot explain why the same three lines lose the change in the second method.
- Suggests a retry or a longer timeout.

### junior

- Says the first object is still held by an open unit of work, so the change is picked up.
- Says the second one is outside it, so nothing writes the change.

### mid

- Places the write at the end of the unit of work rather than at the assignment.
- Says without being asked that the deleted call was doing nothing in the first method and is
  required in the second.
- Points out that a method meant only to read can still cause an update, and what that risks.
- Asks where the boundary actually starts and ends before trusting either method.

## Follow-ups

- The first method throws after it sets the number but before it returns. What is in the row?
  probes: the write is tied to the end of the unit of work, not to the line of code
- Your colleague puts the call back in both methods to be safe. What does it do in the first one
  now?
  probes: whether they know the call is a no-op on an object already being watched
- In the second method the object arrived from the web layer as JSON. When you put the call back,
  which columns get written?
  probes: the whole row goes, including fields the caller never looked at, over someone else's edit

## Sources

- https://docs.jboss.org/hibernate/orm/6.4/userguide/html_single/Hibernate_User_Guide.html#pc

## Notes

The first method works because the entity is managed and the change is flushed at commit; the
second is operating on a detached instance. A candidate who says "dirty checking" and then cannot
say when the statement is sent has not answered it. The third follow-up opens the door to the
whole-row overwrite without naming it.
