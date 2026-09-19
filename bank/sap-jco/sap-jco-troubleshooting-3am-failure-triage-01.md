---
id: sap-jco-troubleshooting-3am-failure-triage-01
schema_version: 1
title: One line in the log and an SAP team waiting
category: sap-jco
topic: troubleshooting
level: junior
tags: [observability, operations, failure-modes]
time_estimate_min: 6
order: 60
links:
  deeper: [sap-jco-troubleshooting-works-for-abap-dev-01]
---

## Ask

The nightly interface died at three in the morning with a `JCoException` and one line in the log.
It is now nine, you own the Java side, and the SAP team is asking what you need from them. What
do you do first, and what do you send them?

## Tests

Whether the candidate can turn a single failure line into a routed, evidenced request instead of
"SAP was down", and whether they think about re-running before they do it.

## Listen for

- Reads the whole exception, not the first line: the group and key say whether it was a logon
  refusal, a communication failure, an error raised by the function module, or an ABAP runtime
  error
- Those four point at different owners — credentials and authorisations, network and gateway,
  the data, the ABAP code
- Sends something searchable: timestamp with timezone, the system and client, the user the job
  logs on as, the function module, and the short dump reference if there is one
- Checks whether it still fails now, and whether it failed the same way earlier in the week
- Asks whether the job is safe to re-run before re-running it

## Expected knowledge

- `JCoException` carries a group and a key, not just a message
- Short dumps are visible on the SAP side in `ST22`

## Strong signals

- Notices the log only had one line, and says what they would add so the next occurrence is
  answerable without a conversation
- Asks what the job had already sent before it died

## Weak signals

- "SAP was down" with no evidence
- Re-runs immediately and cannot say what the first run got as far as
- Escalates without a timestamp, a user or a function module name

## Answer bands

### weak

- Forwards the stack trace with no context and waits.
- Re-runs the job as the first action, with no idea what it did the first time.

### junior

- Separates a connection problem from a refusal from an error inside SAP.
- Collects the details the other team will ask for before asking them.

### mid

- Routes the ticket to the right owner from the error class and says why.
- Establishes whether it is reproducible now before escalating, and says what the re-run risks.
- Names what is missing from the log and fixes that as part of the ticket.

## Follow-ups

- The SAP team come back and say they see nothing at all on their side at that time. What does
  that tell you?
  probes: reaching the system versus being let in, and where the evidence lives
- The job did half its work before it died. What do you want to know before you start it again?
  probes: partial progress and whether a repeat is safe
- It happens again the next night, and the night after, always at the same minute. What now?
  probes: looking for a scheduled cause rather than a random one

## Notes

Transaction-code recall is not the point. A candidate who says "there will be a dump, ask them
for it" without naming `ST22` has answered well.
