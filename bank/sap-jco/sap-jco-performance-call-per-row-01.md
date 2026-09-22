---
id: sap-jco-performance-call-per-row-01
schema_version: 2
title: Fifty thousand rows, fifty thousand calls, six hours
category: sap-jco
topic: performance
level: mid
tags: [performance, throughput, integration]
time_estimate_min: 7
order: 120
links:
  related: [java-performance-parallel-stream-sweep-01]
  deeper: [sap-jco-performance-nightly-bulk-extract-01]
---

## Ask

A nightly job reads fifty thousand rows from a database and calls the same function module in SAP
once per row. It takes six hours. Where is the time going, and what do you change?

## Tests

Whether the candidate reasons about per-call cost and roundtrips before reaching for threads, and
knows the limits on both of the obvious fixes.

## Ideal minimal answer

Fifty thousand sequential roundtrips: the time is per-call overhead and latency, not payload, so
measure one call first and split it into network versus work inside SAP. Then send many rows per
call through a table parameter, choosing a batch size that trades roundtrips against memory, the
runtime limit and one bad row spoiling a batch; parallelism helps only up to a ceiling the SAP
side owns.

## Listen for

- Fifty thousand sequential roundtrips: the cost is dominated by per-call overhead and latency,
  not by the size of the payload
- Wants a measurement first — how long is one call, and how much of that is network versus work
  inside SAP
- The fix with the biggest effect is usually batching: most interfaces of this kind take a table
  parameter, so send many rows per call
- Batch size is a trade: too small keeps the roundtrips, too big costs memory on both sides,
  risks the runtime limit, and makes one bad row spoil a whole batch
- Parallelism is the other axis and its ceiling is set by the SAP side's capacity, not by the
  size of your thread pool
- Asks whether the same rows are re-sent every night, or only the changed ones

## Expected knowledge

- A table parameter carries many rows in one call
- Each call occupies a work process in SAP for its duration

## Strong signals

- Asks whether the target reports per-row results, so a batch can partially succeed and be
  reported on
- Designs the run to be restartable, because a six-hour job will be interrupted eventually
- Says what the acceptable runtime actually is before optimising, and stops when it is met

## Weak signals

- Goes straight to a thread pool of two hundred with no thought for what is on the other side
- Assumes the network is the problem without measuring
- Asks the ABAP team to make the function module faster before knowing where the time is
- Explains batching and parallelism with accurate trade-offs, and will not say which change they
  would make first

## Answer bands

### weak

- Offers "make it multi-threaded" as the whole answer.
- Cannot say what a single call costs or how they would find out.

### junior

- Sees the per-row loop as the problem and suggests sending more per call.
- Knows more threads might help but cannot bound it.

### mid

- Separates per-call overhead from payload and measures one call before changing anything.
- Picks a batch size and can argue both directions of the trade.
- Knows the parallel path has a ceiling on the SAP side and asks who owns it.

### senior

- Puts a number on the target and stops when it is reached.
- Raises partial failure inside a batch before the question is put to them, so one row does not
  lose the other four hundred ninety-nine.
- Makes the run resumable and says what the second attempt must not repeat.

## Follow-ups

- You batch five hundred rows per call and one row in the batch is rejected. What happens to the
  rest of that batch?
  probes: partial failure, and whether the interface reports per row
- You add twenty threads and it gets slower. What would you look at?
  probes: the ceiling on the far side rather than in their own code
- The job is killed at hour four. What does the next run do?
  probes: restartability and whether repeats are safe

## Notes

A good answer treats "six hours" as a fact to be explained, not a problem to be attacked. The
candidate who asks for the cost of one call before proposing anything is already ahead.

## Sources

- https://help.sap.com/doc/abapdocu_751_index_htm/7.51/en-US/abenrfc_dialog.htm
- https://help.sap.com/doc/abapdocu_751_index_htm/7.51/en-US/abenapp_server_resources.htm
