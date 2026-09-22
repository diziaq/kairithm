---
id: java-runtime-container-memory-limit-01
schema_version: 2
title: Killed at 2 GB with a heap that never passed 900 MB
category: java
topic: runtime-behaviour
level: senior
tags: [memory, operations, failure-modes, observability]
time_estimate_min: 9
order: 640
links:
  related: [java-gc-pause-budget-01, java-performance-parallel-stream-sweep-01]
---

## Ask

A pod running a JDK 21 service is killed by the platform about once a week for exceeding its 2 GB
limit. The heap never went above 900 MB against an `-Xmx` of 1500 MB, and there is no
out-of-memory error anywhere in the log. The team's proposal is to raise the heap to 1800 MB so
it has more room. What do you tell them?

## Tests

Whether the candidate can separate what the maximum heap bounds from what the platform is
measuring, and name the parts of a running process that sit outside the heap.

## Ideal minimal answer

The limit is on everything the process has resident and the maximum heap bounds one part of it.
Thread stacks, class metadata, compiled code, buffers allocated outside the heap and the
collector's own structures are all extra, and heap the runtime has committed is counted even
where nothing is using it. Raising the maximum makes it worse. Measure the rest, and leave room
under the limit.

## Listen for

- Says the platform kills on resident memory, and the maximum heap is a bound on one component of
  that, not on the process
- Lists what else the process holds: one stack per thread, class metadata, the compiler's output,
  buffers allocated outside the heap, the collector's own bookkeeping, and whatever native code
  the libraries call
- Distinguishes used heap from committed heap: the graph the team is looking at shows the first,
  the platform counts the second, and the runtime is slow to hand pages back
- Says the proposal moves in the wrong direction, because a larger maximum lets the runtime commit
  more of exactly the thing that is already too big
- Points out there is no out-of-memory error because the runtime never ran out of anything; it was
  killed from outside, which is a different event with different evidence
- Wants the parts measured rather than guessed, and names a way to get the breakdown
- Sets the maximum from the limit with the rest of the footprint subtracted, and says roughly what
  fraction that leaves

## Expected knowledge

- A modern runtime reads the container's limits and sizes the heap from them when no maximum is
  given
- Memory reserved is not memory committed, and committed is not the same as in use

## Strong signals

- Asks how many threads the process runs, and multiplies by the stack size before anything else
- Knows that with no explicit maximum the runtime takes roughly a quarter of the limit, and that
  this is why the well-intentioned explicit figure is often worse than nothing
- Says which collector is in use and whether it returns unused pages, because the answer changes
  the advice
- Asks whether buffers allocated outside the heap are bounded at all, and where their ceiling
  comes from when nobody sets one
- Treats the weekly cadence as a growth signal and wants the resident figure over days, not at the
  moment of death

## Weak signals

- Raises the maximum heap, or the limit, without measuring anything
- Says the runtime cannot exceed its maximum, so the platform must be wrong
- Looks for a leak on the heap, having been told the heap is fine
- Adds a periodic restart and closes the ticket
- Lists five possible sources with fair descriptions and will not say which to measure first

## Answer bands

### mid

- Says the process uses memory beyond the heap and the limit counts all of it.
- Names two or three of the other consumers.
- Says raising the maximum will not help, without being able to say why it makes it worse.

### senior

- Separates resident memory from heap of their own accord, and says the runtime was killed
  rather than giving up.
- Distinguishes committed from used and explains why the team's graph looked innocent.
- Names a way to get the breakdown and says what they expect it to show.
- Sets the maximum by subtracting a measured remainder from the limit, rather than by feel.

### lead

- Decides what the pod's limit should be and what the maximum heap should be, together, with
  numbers.
- Says what happens to this service under the same change on a machine with four times the cores,
  and why that matters.
- Puts the resident figure and the kill reason where the on-call can see them, and says what
  replaces the heap graph as the signal.
- Writes the rule down for the other services on the cluster instead of fixing this one.

## Follow-ups

- There is nothing in the log at all — the process simply disappears mid-request. Does that narrow
  it for you?
  probes: killed from outside versus the runtime giving up, and where each leaves evidence
- The service reads large files through a library that maps them into the address space. Does that
  turn up anywhere you have been looking?
  probes: allocations outside the heap, and that the usual graphs do not show them
- A second service on the same cluster leaves the heap size unset entirely. Is that safer or
  worse?
  probes: whether they know the runtime reads the limit and what fraction it takes by default
- What do you want in place so that the next one of these takes ten minutes instead of a week?
  probes: a breakdown of the native side, resident memory over time, and the recorded kill reason

## Sources

- https://docs.oracle.com/en/java/javase/21/docs/specs/man/java.html
- https://docs.oracle.com/en/java/javase/21/docs/specs/man/jcmd.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Runtime.html
- https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- https://bugs.openjdk.org/browse/JDK-8230305

## Notes

The runtime side, from the `java` tool reference: `-XX:+UseContainerSupport` "allows the VM to
determine the amount of memory and number of processors that are available to a Java process
running in docker containers. It uses this information to allocate system resources. The default
for this flag is true." `-Xlog:os+container=trace` prints what it decided, and is the fastest way
to settle an argument about what the runtime thinks its limit is.

The defaults for the percentage flags are not printed in the tool reference; read them off the
runtime in question with `java -XX:+PrintFlagsFinal -version`. On a current JDK they come out as
`MaxRAMPercentage` 25.0, `MinRAMPercentage` 50.0 and `InitialRAMPercentage` 1.5625. A quarter of
the limit is the figure behind the third follow-up: a service with no explicit maximum on a 2 GB
pod gets a 512 MB heap, which is frequently *safer* than the 1500 MB somebody typed in, and
occasionally far too small. The point is that the number came from somewhere, not that either
value is right.

Version pin worth knowing: container awareness reads cgroup limits, and cgroup v2 support arrived
in JDK 15 under JDK-8230305 and was backported to 11.0.16 and 8u372. A service on an older
runtime on a cgroup v2 host reads the *host's* memory and sizes itself for a machine it does not
have. That is a different fault with the same ending.

`-XX:MaxDirectMemorySize` is documented as: "If not set, the flag is ignored and the JVM chooses
the size for NIO direct-buffer allocations automatically." In practice that ceiling tracks the
maximum heap, so raising the heap raises a second budget as well — which is the concrete reason
the team's proposal makes it worse rather than merely failing to help.

Figures to release when asked, and credit the asking: 220 live threads at 1 MB of stack each;
metadata around 180 MB; code cache around 160 MB; a mapping library the service uses for report
templates; the collector is G1; the pod's kill reason is recorded and nobody has looked at it.

The CPU side of container awareness is a real question too — a quota shapes what the runtime
reports as the processor count and with it the collector's thread counts and the shared pool —
but it already surfaces on the parallel streams card, so keep this one on memory. If a candidate
raises it, take it as a strong signal and steer back.
