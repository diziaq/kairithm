---
id: sap-jco-troubleshooting-works-for-abap-dev-01
schema_version: 1
title: It works when the ABAP developer runs it
category: sap-jco
topic: troubleshooting
level: senior
tags: [security, observability, failure-modes]
time_estimate_min: 8
order: 180
---

## Ask

The ABAP developer runs the function module by hand with exactly your input and gets the right
answer. Your call, same system, same minute, comes back empty. Where do you look?

## Tests

Whether the candidate treats "works for me" as a difference in execution context to be found,
and knows which differences produce a silent empty result rather than an error.

## Listen for

- It is not the same execution: a different user, possibly a different client, and a different
  set of authorisations
- The interface user needs RFC access to the function group and the business authorisations the
  code checks inside — a developer's role hides both
- Checks inside the code often answer "no data" rather than raising, which is exactly the
  symptom seen
- Other axes worth separating: client number, logon language and its effect on keys and texts,
  user-specific defaults the dialog user has, and the exact value that went over the wire
- The way to settle it is to reproduce under the interface user, or to trace the authorisation
  check, rather than to compare opinions

## Expected knowledge

- `S_RFC` governs which function groups a user may call remotely
- An authorisation trace exists on the SAP side and shows the failed check

## Strong signals

- Asks for the trace and the exact failed check, then requests only that
- Says that granting a wide role to test is how a landscape ends up with wide roles in
  production
- Separates "returned nothing" from "was not allowed to see anything" and says how to tell which
- Asks whether the two runs really used the same client, because that single digit explains a
  lot of these

## Weak signals

- Concludes the data is missing because the call returned nothing
- Asks for the developer's own role to be copied to the technical user
- Keeps re-running the same call hoping for a different result

## Answer bands

### mid

- Notices the two runs use different users and asks about authorisations.
- Wants to see the call reproduced under the interface user.

### senior

- Lists the axes on which the two executions differ and eliminates them in a sensible order.
- Explains why an authorisation problem can present as an empty result rather than an error.
- Comes back with a specific, minimal request for the SAP team rather than a broad one.
- Uses a trace as evidence instead of arguing from symptoms.

### lead

- Treats the difference between environments and roles as the underlying defect and fixes the
  process that allowed it.
- Sets up how interface users get their access defined and reviewed, so this stops recurring.
- Says what should be logged by the interface so the next occurrence is answerable without the
  ABAP team.

## Follow-ups

- The trace is clean and it still returns nothing. What is left on your list?
  probes: client, language, the exact value sent, and user-specific defaults
- The developer offers to give your user the same role they have. What do you say?
  probes: least privilege, and what that role would carry into production
- How would you make the difference between the two runs visible without having to ask the other
  team?
  probes: logging the identity, target and inputs of every call

## Notes

The core insight is that an authorisation failure inside application code frequently manifests as
a missing row rather than an exception. A candidate who only reaches for connectivity has not
answered this card.
