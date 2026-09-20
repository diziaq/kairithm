---
id: java-jvm-class-identity-plugin-01
schema_version: 1
title: Cannot cast OrderDto to OrderDto
category: java
topic: jvm-internals
level: senior
tags: [failure-modes, operations, packaging]
time_estimate_min: 8
order: 310
---

## Ask

A plugin-based application throws `ClassCastException: com.acme.OrderDto cannot be cast to
com.acme.OrderDto` when a plugin hands an object back to the host. Nobody can see anything wrong
with the code. What is happening, and what do you change?

## Tests

Whether the candidate knows what makes two classes the same class at runtime, and can turn that into
a rule about how things are built and shipped.

## Listen for

- A class is identified by its name together with the loader that defined it, so the same bytes
  loaded twice give two unrelated types
- The shared type is both on the host's path and inside the plugin's jar, and the plugin's loader
  defined its own copy
- The fix is in the build: the shared contract lives in one place, is loaded by the parent, and is
  not bundled into the plugin
- Delegation order decides which copy wins; a loader that prefers its own will take its own even
  when the parent already has one
- Diagnose by printing the loader behind each object's class, rather than by reading the message
  again
- Static state, registries and caches inside the duplicated type now exist twice

## Expected knowledge

- Delegation to the parent loader, and that plugin systems and application servers deliberately
  break it
- A cast is decided against the loaded type, not against the printed name

## Strong signals

- Talks about which dependencies are marked as provided at build time as the real control point
- Mentions the same shape when a common jar is relocated into two places
- Wants the build to fail on this rather than discovering it at runtime

## Weak signals

- Casts through `Object`, or reaches for reflection or serialisation to get around it
- Blames the IDE or a stale build directory
- Says the path is wrong, with no account of which copy wins and why

## Answer bands

### mid

- Says the type has been loaded twice and the two are not interchangeable.
- Points at the plugin jar containing something it should be getting from the host.
- Fixes it by removing the duplicate, without being able to say what decides which one is used.

### senior

- States what identifies a type at runtime and derives the whole symptom from it.
- Explains how delegation order produced the duplicate in this particular arrangement.
- Diagnoses from the loaders behind each object rather than guessing at the build.
- Moves the fix into the build: one artifact for the contract, marked so it is not bundled.

### lead

- Draws the line between what a plugin may bring and what the host owns, and writes it down.
- Adds a check that fails the build on a duplicated shared type.
- Raises what else the duplication broke quietly, such as state that is now held twice.

## Follow-ups

- The plugin's build file pulls the shared jar in as an ordinary dependency and ships everything in
  one fat file. Where does that leave you?
  probes: dependency scope and relocation as the root cause, not the cast
- The host reloads plugins without restarting, and after twenty reloads it runs out of memory. What
  connects the two problems?
  probes: retained loaders and everything they defined; one stray reference pinning the old one
- How would the build stop this reaching production next time?
  probes: enforcing scope, duplicate-class checks, making it a failure rather than a convention

## Sources

- https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-5.html#jvms-5.3
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/ClassLoader.html
