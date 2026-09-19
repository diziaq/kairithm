---
id: java-memory-model-double-checked-locking-01
schema_version: 1
title: A lock removed from the fast path, and a month in production
category: java
topic: memory-model
level: senior
tags: [correctness, failure-modes, performance]
time_estimate_min: 8
order: 210
---

## Ask

Someone rewrites a `synchronized getInstance()` because it showed up in a profile: they add a null
check outside the lock, keep the check inside as well, and leave the field a plain reference. Every
test passes and it has been live for a month. What do you do with the change?

## Tests

Whether the candidate can argue that a construct is broken from what the model permits, while the
evidence in front of them says it works.

## Listen for

- A thread can be handed a reference to an object that is not finished, and then read defaults out
  of it while the field itself is not null
- The write that publishes the reference can become visible before the writes that fill the object in
- Marking the field `volatile` makes the outer check legal, because the publishing write and the
  unlocked read are then ordered against each other
- Names the alternative that gets laziness from class initialisation, where the JVM does the locking
  and the code contains none
- Asks whether the deferral is needed at all, and whether the profile that motivated it was real

## Expected knowledge

- What the lock was providing before the change: mutual exclusion and ordering, not just exclusion
- An uncontended lock is not the cost people assume, so the premise deserves a measurement

## Strong signals

- Says a month in production is not evidence, and can say why the fault is rarely seen on a common
  server architecture
- Prefers the holder idiom or eager creation over repairing the double check, and argues the simpler
  construct is worth more than the cleverness
- Asks what the constructor actually does before agreeing the work is worth deferring at all

## Weak signals

- Approves it because the tests pass and it is faster
- Adds the keyword when asked but cannot say what it orders
- Says the outer check is fine because reference assignment cannot be torn

## Answer bands

### mid

- Recognises the shape and says it is unsafe without the keyword on the field.
- Explains that another thread can see a non-null field too early.
- Cannot say precisely what that thread then reads, or why the tests pass.

### senior

- Describes the partially built object concretely: the field is set, the contents are not there yet.
- Explains what the keyword orders and why that closes the hole.
- Treats the month of uptime as a statement about the hardware and the load, not about correctness.
- Offers the simpler construction and says why it is preferable to a correct double check.

### lead

- Asks for the measurement behind the change and is willing to reject it on those grounds alone.
- Says what happens if construction fails halfway, and who retries.
- Goes beyond the single review: makes the safe form the obvious one, so the next person does not
  have to know this.

## Follow-ups

- The object being built reads three files and opens a socket. Does that change what you suggest?
  probes: whether deferral is earning anything, and what a failed build leaves behind for the next
  caller
- The author asks you to show them a failing test. What do you say?
  probes: guarantee versus observation; inability to provoke it is not a defence
- A month later the same shape turns up in four more classes. What do you do beyond this review?
  probes: review versus mechanism; making the safe form the default

## Sources

- https://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html
- https://docs.oracle.com/javase/specs/jls/se21/html/jls-12.html#jls-12.4.2
