---
id: sap-jco-work-processes-dialog-timeout-01
schema_version: 1
title: The extract that now dies after ten minutes
category: sap-jco
topic: work-processes
level: mid
tags: [performance, failure-modes, operations]
time_estimate_min: 7
order: 110
links:
  deeper: [sap-jco-work-processes-integration-starves-users-01]
---

## Ask

An extract that used to take four minutes now dies after about ten with the connection closed on
you, and the SAP team mentions there is a dump. Your first instinct is to ask Basis to raise the
timeout. Talk me through it.

## Tests

Whether the candidate knows an external RFC call runs inside a dialog work process with a
runtime limit, and treats that limit as a design constraint rather than a setting to raise.

## Listen for

- The call is executed by a dialog work process, and a dialog work process has a maximum runtime
  — `rdisp/max_wprun_time`, commonly ten minutes — after which the session is terminated and a
  dump is written
- That parameter is system-wide: raising it for this interface raises it for every dialog user,
  which makes it a Basis policy decision, not a fix
- The real answer is to stop doing multi-minute work in one call: chunk the extract on a stable
  key and make several calls
- Long-running work belongs in background processing, which is not subject to that limit
- Notices the trigger — the data grew — and that the interface was never designed to grow

## Expected knowledge

- Dialog and background work processes are different pools with different rules
- A terminated ABAP session leaves a short dump on the SAP side

## Strong signals

- Chunks on a key range rather than an offset, so the run is stable while data changes underneath
- Says what happens to a chunk that fails halfway and how the run picks up from there
- Asks what the consumer actually needs before agreeing that everything must come in one call

## Weak signals

- Raises the timeout and considers the ticket closed
- Adds a client-side retry of the whole ten-minute call
- Thinks the connection was dropped by the network

## Answer bands

### weak

- Blames the network, or retries the same call and hopes.
- Cannot say what inside SAP gave up, or why at that particular point.

### junior

- Knows there is a limit on how long the SAP side will run this and that it was hit.
- Suggests asking for more time, or splitting the work, without being able to choose.

### mid

- Names the limit and where it applies, and why changing it affects everyone.
- Splits the extract into chunks and says how the chunks are cut.
- Says which kind of processing this work should have been in from the start.

### senior

- Treats growth as the root cause and designs for the next tenfold, not for today.
- Makes the run resumable and says what a half-finished run leaves behind.
- Brings the capacity conversation to Basis with numbers rather than with a request.

## Follow-ups

- Basis agree to double it. What have you bought, and what have you spent?
  probes: whether they see the system-wide cost and the postponed failure
- You split it into fifty chunks and two of them fail. What does the job report?
  probes: partial success, resumability, and what the consumer is told
- The same job, run as a scheduled task inside SAP, has never hit this. Why not?
  probes: whether they know the two kinds of processing have different rules

## Notes

The default for `rdisp/max_wprun_time` is commonly 600 seconds but is site-specific; the point is
that a limit exists and is shared, not its value. Newer kernels expose additional parameters for
the same purpose — do not fail a candidate on the parameter name.
