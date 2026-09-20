---
id: java-collections-shared-map-cache-01
schema_version: 1
title: The lookup table that worked for a year
category: java
topic: collections
level: mid
tags: [correctness, failure-modes, consistency]
time_estimate_min: 7
order: 110
links:
  deeper: [java-collections-comparator-contract-01]
  related: [java-memory-model-config-swap-01]
---

## Ask

A service keeps a lookup table in a plain `HashMap` field. Request threads read it; a scheduled
task puts a few fresh entries into it every minute. It has run like that for a year. Last month a
lookup returned null for a code that is definitely there, and a request thread got stuck spinning
inside the map. What do you change, and what do you tell the team about the year it worked?

## Tests

Whether the candidate treats an unsynchronised shared structure as undefined behaviour rather than
as a risk that the absence of incidents has already measured for them.

## Listen for

- Reading while another thread is restructuring the map is not defined; a reader can be walking
  internal state that is halfway through being rewritten
- A year without symptoms is not evidence — the window is microseconds wide and only has to be hit
  once
- Names a fix and what it costs: a map built for concurrent use, or building a fresh read-only map
  each minute and swapping a single reference
- If the reference is swapped, that reference itself has to be published so readers see it
- With a concurrent map, knows that looking then putting across two calls is still a race, and
  reaches for the single-call form

## Expected knowledge

- `ConcurrentHashMap`, and which of its operations are atomic as a unit
- The exception you get for modifying while iterating is a best-effort check, not protection

## Strong signals

- Prefers rebuilding and swapping when reads vastly outnumber writes, and says why
- Asks whether readers can tolerate a table that is up to a minute behind, and makes that an
  explicit decision rather than an accident
- Points out that wrapping the map in a synchronising wrapper still leaves iteration unsafe

## Weak signals

- Puts `synchronized` around every access with no mention of what it costs on the read path
- Believes the fail-fast exception protects the map
- Concludes it is fine because it has run for a year, or because the refresh is small

## Answer bands

### weak

- Treats the null result as a data problem and looks at the source of the table.
- Says threads are involved so it is hard to predict, with no account of what the map is doing.
- Adds a retry around the lookup.

### junior

- Identifies that two threads use the map without coordination and that one of them changes it.
- Suggests a thread-safe map or a lock, without separating reads from writes.
- Accepts that the year of quiet running proves nothing once this is pointed out.

### mid

- Explains that a reader can observe the internal state mid-rewrite, not merely a stale value.
- Chooses between a concurrent map and a swapped read-only copy on the read-to-write ratio.
- Notes that the sequence of look-then-put is not made safe by the map being thread-safe.

### senior

- Frames the year of uptime as a sampling artefact and refuses to treat it as evidence.
- Makes the tolerated lag an explicit, written decision with the people who own the data.
- Says how the change would be verified given the symptom appears twice a month, and does not
  promise a test that proves absence.

## Follow-ups

- The refresh replaces about five entries out of four thousand. Does that change what you'd pick?
  probes: swapping the whole thing versus mutating entries; read-to-write ratio driving the choice
- Suppose the team says readers may be up to a minute behind. What becomes easier?
  probes: whether staleness is treated as a negotiable requirement rather than a defect
- You ship your fix. Given the symptom shows up twice a month, how does anyone know it was the fix?
  probes: rare timing faults; evidence versus absence of evidence

## Notes

The rates, if the candidate asks: the null result has happened twice in the last month and the
spinning thread once, against roughly four thousand entries with about five refreshed a minute. A
candidate who asks how often before deciding how serious it is has earned the numbers — and the
answer "twice" should not make it less serious, which is the point of the last follow-up.

The infinite loop on resize that people quote is a Java 7 story; Java 8 changed how a bucket is
split. Neither version promises anything about a map mutated without coordination, so "that bug was
fixed" is the wrong lesson to draw. The javadoc simply says access must be synchronised externally.

## Sources

- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/HashMap.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html
