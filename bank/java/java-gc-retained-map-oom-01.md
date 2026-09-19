---
id: java-gc-retained-map-oom-01
schema_version: 1
title: Out of memory every four days, eight with twice the heap
category: java
topic: garbage-collection
level: mid
tags: [memory, failure-modes, operations]
time_estimate_min: 7
order: 400
links:
  deeper: [java-gc-pause-budget-01]
---

## Ask

A service is killed and restarted by its platform every four days after an out-of-memory error.
Doubling the heap moved it to eight days. A heap dump shows nine million entries in a `static Map`
keyed by session id. Someone proposes switching it to a `WeakHashMap`. Talk me through it.

## Tests

Whether the candidate reasons about what keeps an object alive, and can say whether a weakly
referencing structure actually breaks the chain in this particular case.

## Listen for

- The collector cannot take away anything still reachable; a static field is a root, so nothing in
  that map is eligible
- Doubling the heap bought time in proportion to the growth rate, which is the signature of
  retention rather than of a heap that is merely too small
- The weak variant only helps while nothing else holds the key; if the value holds its own key, or
  the key is held elsewhere, the entry stays
- Asks what is supposed to take entries out and when — the real fix is a bound and a removal rule,
  or deleting on session end
- Wants the dump read by what each root retains, not by which objects are biggest

## Expected knowledge

- Reachability from roots, and that "nobody uses this any more" is not something the collector can
  observe
- The difference between a leak and a live set that is simply larger than the heap

## Strong signals

- Asks what the entries are worth: a cache with no measured hit rate is a leak with a good reputation
- Notes that weak entries are cleared whenever the collector gets to them, so they are not a bound
- Checks whether the keys can be matched at all, since removal depends on it

## Weak signals

- Calls for an explicit collection or a bigger maximum heap as the fix
- "Java manages memory, so it cannot leak"
- Accepts the weak variant without asking what the values point at

## Answer bands

### weak

- Suggests more heap, or restarting on a schedule.
- Describes the collector as unpredictable and leaves it there.
- Accepts the proposal because weak sounds like the opposite of leaking.

### junior

- Says the map keeps growing and nothing removes entries, so the objects stay alive.
- Knows a static field keeps its contents reachable.
- Cannot say whether the proposed replacement would help here.

### mid

- Uses the four-to-eight-day figure as evidence of unbounded growth rather than of an undersized
  heap.
- Explains the condition under which the weak variant helps, and asks what the values hold.
- Proposes a bounded structure with an explicit removal rule, and asks who owns eviction.

### senior

- Asks what the map is for before choosing a structure, and is prepared to delete it.
- Reads the dump by retention, and can say which root to cut.
- Adds a way to see the growth before the next failure rather than after it.

## Follow-ups

- Each value in that map holds on to the key it was filed under. Where does that leave the proposal?
  probes: the path from value back to key keeping the entry alive
- The team says it is a cache, not a leak. What would you want before accepting that?
  probes: a bound, an eviction rule, a hit rate — a cache is only a cache if it can forget
- The dump was taken at the moment of the crash. Is that the one you want?
  probes: growth over time as the signal; sampling before the failure

## Sources

- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/WeakHashMap.html
