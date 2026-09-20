---
id: sap-jco-rfc-fundamentals-blocking-call-01
schema_version: 1
title: A ninety-second RFC call behind a REST endpoint
category: sap-jco
topic: rfc-fundamentals
level: junior
tags: [integration, performance, failure-modes]
time_estimate_min: 5
order: 10
links:
  deeper: [sap-jco-rfc-fundamentals-timeout-unknown-outcome-01]
---

## Ask

Your REST endpoint calls a function module in SAP through JCo, and that call reliably takes
ninety seconds to come back. What is your Java thread doing for those ninety seconds, and what is
the SAP system doing?

## Tests

Whether the candidate sees a synchronous RFC as one request that ties up a finite resource on
both sides at the same time, rather than as a method call that is simply slow.

## Listen for

- The calling thread is blocked for the whole ninety seconds; nothing in JCo makes the call
  asynchronous on its own
- On the SAP side the request is executed by a dialog work process, which is occupied until the
  function module returns — the same pool of processes interactive users are served from
- Both sides have a finite number of those, so concurrency is what turns a slow call into an
  outage
- There is no partial result: you get everything when the function module finishes, or you get an
  error

## Expected knowledge

- A `JCoDestination` call is request and response over the network
- A thread pool and a servlet container have a fixed number of threads

## Strong signals

- Asks who is waiting at the other end — a person in a browser, or a batch job that does not care
- Points out that the client in front may give up long before SAP does, while the SAP side carries
  on working

## Weak signals

- Believes JCo hands the call off and returns immediately
- Answers only "raise the timeout" without asking what the ninety seconds are spent on
- Cannot name anything that is consumed inside SAP while the call runs

## Answer bands

### weak

- Treats it as an ordinary slow method and has nothing to say about the SAP side.
- Suggests adding a retry, without noticing the first call is still running.

### junior

- Says the thread waits and cannot serve anything else until the call returns.
- Says SAP is executing the function module for that time and gives the result at the end.

### mid

- Works out what runs out first when several requests arrive together, and names the limit on
  each side.
- Separates the fix into two: make the call faster, or stop making the user wait on it.
- Notes that a client giving up does not free the work already running in SAP.

## Follow-ups

- Ten users hit that endpoint in the same minute. What runs out first?
  probes: whether they see a shared, finite resource on both sides rather than one slow call
- The page in front gives up after thirty seconds and the user presses the button again. What is
  running in SAP now?
  probes: abandoned work, and duplicate submissions from impatient users
- Someone proposes returning straight away and doing the call in the background. What does the
  user see instead, and what do you now owe them?
  probes: where the result goes, and who tracks whether it ever arrived

## Notes

The card is about resource ownership, not about JCo syntax. A candidate who only says "it blocks"
has answered half of it; the SAP half is the half that costs money.

Interviewer background: the call in this scenario is a synchronous RFC — sRFC — where the caller
waits for the result and nothing is stored or forwarded anywhere. That is exactly what separates
it from the transactional calls in the tRFC topic, where the return is an acknowledgement that
the unit was recorded. Do not hand the candidate either term.

Verified: a synchronous inbound RFC from an external client is executed in a dialog work process
by default. That is why the work-processes topic, where the dialog runtime limit lives, is the
natural place to take a candidate who answers this one well.

## Sources

- https://help.sap.com/doc/abapdocu_751_index_htm/7.51/en-US/abenrfc_dialog.htm
- https://help.sap.com/doc/abapdocu_751_index_htm/7.51/en-US/abenapp_server_resources.htm
