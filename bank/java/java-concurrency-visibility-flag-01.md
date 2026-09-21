---
id: java-concurrency-visibility-flag-01
schema_version: 2
title: A flag one thread writes and another never sees
category: java
topic: concurrency
level: senior
tags: [correctness, failure-modes, memory-model]
time_estimate_min: 7
order: 20
links:
  related: [kafka-delivery-exactly-once-claim-01]
---

## Ask

A worker loop polls a plain `boolean stop` field. Another thread sets it to `true`. In production
the worker sometimes runs on for minutes afterwards, and attaching a debugger makes it stop
immediately. What is going on, and what does marking the field `volatile` change?

## Tests

Whether the candidate reasons about the Java memory model as a set of rules the compiler and the
hardware are allowed to exploit, rather than as a description of what usually happens.

## Ideal minimal answer

Nothing obliges the reading thread to observe the store, so the loop may hoist the read out and
spin on a register; that is a guarantee the model withholds, not something the hardware happens
to do. `volatile` forces the load and orders it against the store, publishing everything written
before it — but leaves a read-modify-write divisible.

## Listen for

- Nothing forces the reading thread to observe the store; the loop can legally hoist the read out
  and spin on a register or a cached line
- `volatile` establishes an ordering edge between the store and any subsequent load of that field
- That edge covers everything written before the store, not only the field itself
- The debugger changes the answer because it perturbs optimisation, so it is evidence about the
  tooling, not about the fault
- `volatile` does not make a read-modify-write indivisible

## Expected knowledge

- happens-before, and that it is a guarantee rather than an observation
- The difference between a field being stale and a field being torn
- `AtomicBoolean`, `synchronized`, and what each one costs

## Strong signals

- Distinguishes "I could not reproduce it" from "it cannot happen"
- Mentions that the same defect is invisible on x86 and obvious on a weaker architecture
- Knows the store is a release and the load an acquire, and what that buys for the surrounding
  writes

## Weak signals

- "The compiler has a bug"
- Treats `volatile` as a lighter lock that also covers compound updates
- Says the field is cached in the CPU and stops there, with no rule that says when it is refreshed
- Proposes a `sleep` in the loop as the fix, and is satisfied when that appears to work

## Answer bands

### weak

- Blames the JVM, the compiler or the operating system scheduler.
- Cannot say what the reading thread is allowed to do with a repeated field access.
- Treats the debugger making it work as proof the code is fine.

### junior

- Says the writing thread's change is not picked up by the reader.
- Knows `volatile` is the keyword that fixes this particular loop.
- Cannot say what rule makes it work, or what else it covers.

### mid

- Explains that the read may be hoisted out of the loop, so the field is fetched once.
- States that `volatile` forces the load each time and orders it against the store.
- Notes that `volatile` would not save a `count++` in the same loop.

### senior

- Frames it as a guarantee the model grants, not behaviour the hardware happens to show.
- Explains that the ordering edge also publishes the writes that preceded the store.
- Reasons about why the fault is invisible on one architecture and routine on another.
- Treats an unreproducible failure as unresolved rather than absent.

### lead

- Chooses between `volatile`, an atomic type and an interrupt-based shutdown against stated
  constraints, and says what each costs the next maintainer.
- Points out that a team cannot review its way to correctness here and names what it would take
  to catch this class of fault in CI.
- Connects it to how the service is shut down and drained as a whole, not to one loop.

## Follow-ups

- The same loop also keeps a running tally that it bumps on each pass. Does your fix cover that
  too?
  probes: whether they keep ordering and indivisibility separate
- Your colleague cannot reproduce it on their machine and wants to close the ticket. What do you
  say?
  probes: guarantee versus observation; architecture differences
- Six months later someone removes the keyword because it "looked like a leftover". How would
  anyone find out before a customer does?
  probes: testability and the maintenance cost of the chosen mechanism

## Notes

The card is about reasoning from the model, not about the keyword. A candidate who says
`volatile` in the first sentence and then cannot say what it orders has not answered it.
