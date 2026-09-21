---
id: sap-jco-work-processes-dialog-timeout-01
schema_version: 2
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

## Ideal minimal answer

The call runs in a dialog work process, which has a maximum runtime — commonly ten minutes —
after which the session is terminated and a dump written; that limit is instance-wide, so
raising it is a Basis decision affecting every dialog user. Chunk the extract on a stable key
range into calls well inside it, or move the work to background processing, which is not bound
by it.

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

Verified: `rdisp/max_wprun_time` is the maximum uninterrupted runtime of a dialog step, the
common default is 600 seconds, it applies instance-wide, and exceeding it terminates the session
with a `TIME_OUT` short dump visible in `ST22`. Background work processes are not subject to it,
which is the whole basis of the third follow-up.

Verified, and the reason not to test the parameter name: from kernel 7.40 the limit moved to
priority-based parameters — `rdisp/scheduler/prio_high/max_runtime`,
`rdisp/scheduler/prio_normal/max_runtime` and `rdisp/scheduler/prio_low/max_runtime` — with
`rdisp/max_wprun_time` taking precedence where it is still set, and it is removed from the kernel
altogether as of `SAP_BASIS` 755. A candidate on a recent system may correctly not recognise the
classic name. Accept "there is a runtime limit on the dialog side and Basis owns it".

## Sources

- https://help.sap.com/doc/abapdocu_751_index_htm/7.51/en-US/abenapp_server_resources.htm
- https://help.sap.com/doc/abapdocu_751_index_htm/7.51/en-US/abenrfc_dialog.htm
- https://help.sap.com/doc/saphelp_nw73ehp1/7.31.19/en-us/4b/2b3c3e8eb51780e10000000a42189c/content.htm
