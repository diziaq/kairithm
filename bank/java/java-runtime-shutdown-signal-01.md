---
id: java-runtime-shutdown-signal-01
schema_version: 1
title: Thirty seconds between the signal and the exit
category: java
topic: runtime-behaviour
level: senior
tags: [operations, idempotency, failure-modes]
time_estimate_min: 8
order: 1010
---

## Ask

On every deploy the platform sends the process a termination signal and kills it thirty seconds
later. Since the last release, deploys leave truncated responses in the logs and a handful of jobs
get processed twice. Walk me through what the runtime does between the signal and the exit, and what
you would add.

## Tests

Whether the candidate knows what the runtime actually guarantees on the way out, and can design a
drain that does not depend on luck.

## Listen for

- The signal starts the sequence: registered hooks are started as threads, all at once, in no
  defined order, and the process leaves when they are done or when the platform runs out of patience
- A hard kill, or a halt called from inside, runs none of that, so the design has to survive nothing
  running at all
- Work in flight has to be finished or handed back: stop accepting, let the executor finish with a
  bounded wait, then stop for real
- A job done twice means the unit of work is not replayable; a tidy exit reduces how often that
  happens without removing the requirement
- Threads that are not marked as background keep the process alive by themselves, which is a
  different mechanism and interacts with the hooks
- The order against the load balancer matters: stop being routed to before starting to drain, or
  every deploy drops requests

## Expected knowledge

- Registering a hook, and that the code inside one must be short, must not assume any other hook,
  and must not wait forever
- A grace period is a deadline, and everything has to fit inside it

## Strong signals

- Points out that thirty seconds has to exceed the longest request plus the drain, and checks
  whether it does
- Says the double processing must be fixed on its own merits, because a crash produces it too
- Mentions that logging, metrics and trace exporters are shutting down as well, so the evidence
  about the exit is the first thing to vanish

## Weak signals

- Adds a hook that does a long clean-up and assumes it completes
- Relies on an object's own clean-up when it is collected
- Treats the duplicate jobs as fixed once the drain works

## Answer bands

### mid

- Knows a hook can be registered and runs on the signal.
- Suggests stopping new work and waiting for current work.
- Does not raise the hard kill, the ordering, or the duplicates as a separate problem.

### senior

- Describes the sequence accurately, including that hooks run together and in no defined order.
- Says what happens when the platform kills the process at the deadline, and designs for it.
- Orders the steps against routing, so the instance is taken out before it drains.
- Separates the truncated responses from the duplicate jobs and treats them as two defects.

### lead

- Requires the unit of work to survive being replayed, independent of the exit path.
- Sets the grace period from a measured distribution rather than accepting the platform default.
- Says how the team would notice this regressing on a future release.

## Follow-ups

- The machine loses power instead. Which parts of your answer still hold?
  probes: designing for the case where nothing at all runs on the way out
- One pool thread is in the middle of a thirty-minute export when the signal arrives. What do you
  want to happen?
  probes: cooperative interruption, splitting long work, checkpointing
- After your change the count of jobs done twice drops but does not reach zero. Are you finished?
  probes: whether replayability is held as a separate requirement from the drain

## Sources

- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Runtime.html#addShutdownHook(java.lang.Thread)
