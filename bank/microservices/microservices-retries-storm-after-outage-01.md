---
id: microservices-retries-storm-after-outage-01
schema_version: 1
title: The dependency comes back and is knocked over again
category: microservices
topic: retries
level: junior
tags: [retries, failure-modes, operations, performance]
time_estimate_min: 6
order: 80
links:
  deeper: [microservices-retries-layered-multiplication-01]
---

## Ask

A service you depend on goes down for thirty seconds. When it comes back it falls over again
within a second, and this time it stays down. Every caller retries three times on failure. What
happened?

## Tests

Whether the candidate can see that the callers' own recovery behaviour is the thing that finishes
off the dependency.

## Listen for

- All the callers were failing at once, so they all come back at the same instant; the recovery
  traffic is a spike, not the normal rate
- Three attempts per caller multiplies the offered load at exactly the moment there is least
  capacity
- A restarted service starts cold — empty caches, fresh connections — so it can take less than
  usual, not more
- Spreads the callers out by waiting a growing and randomised amount between attempts
- Stops calling something known to be failing, and lets a small number of probes decide when to
  resume

## Expected knowledge

- A caller that retries turns one failed request into several
- Callers that all fail together also all recover together

## Strong signals

- Points out that the retries never stopped during the outage, so the queue of pending work grew
  the whole time
- Notes that a fixed wait makes everyone line up on the same second rather than fixing anything

## Weak signals

- Blames the dependency's capacity and leaves the callers out of the story
- Suggests more retries, or a longer fixed wait, as the fix
- Says the dependency should just scale up before it restarts

## Answer bands

### weak

- Says the dependency is simply too weak and needs bigger machines.
- Does not connect the callers' behaviour to the second outage.
- Cannot say why it survived normal traffic but not the recovery.

### junior

- States that all the callers hit it simultaneously when it came back.
- Connects the three attempts per caller to the size of that spike.
- Proposes waiting longer between attempts.

### mid

- Adds randomness so callers do not synchronise, and explains why a fixed wait would not.
- Wants calls to stop entirely while the dependency is known bad, with a controlled way to resume.
- Distinguishes requests worth retrying from ones nobody is waiting for any more.

## Follow-ups

- The team's fix is a one-second wait between attempts, deployed everywhere. What happens at the
  next outage?
  probes: whether they see the synchronised wave; randomised spacing
- Which calls would you not repeat at all?
  probes: whether a repeat is safe; work whose caller has already given up
- Your caller stopped waiting after two seconds but your attempts run for ten. Who is that work
  for?
  probes: deadline awareness and wasted capacity

## Sources

- https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
