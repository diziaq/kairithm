---
id: sap-jco-repository-metadata-locked-down-prod-01
schema_version: 1
title: Production refuses a function module nobody called
category: sap-jco
topic: repository-metadata
level: senior
tags: [security, operations, integration]
time_estimate_min: 8
order: 150
---

## Ask

Your integration works in QA. In production the very first call fails before it reaches the
business function at all, with an authorisation error naming a function module nobody on your
team has ever heard of. What is going on, and what do you ask for?

## Tests

Whether the candidate knows JCo makes its own remote calls to read interface descriptions, and
can turn that into a precise authorisation request instead of a demand for a wider role.

## Listen for

- Before JCo can build a call it fetches the interface description from SAP, and it does that
  with its own remote calls to metadata function modules
- Those calls need RFC authorisation in their own right, so a production role trimmed to "just
  the agreed function group" locks them out
- QA and production differing in roles is the ordinary cause of "but it works in QA"
- The ask is a specific `S_RFC` entry for the metadata lookups, not a broader role — or a
  separate destination and user for repository queries
- The lookups cost roundtrips, which is why they happen once and are cached, and why a per-call
  destination pays for them again and again
- If metadata reads will never be permitted, the interface can be described locally instead, and
  then you own keeping that description in step with the ABAP side

## Expected knowledge

- `S_RFC` protects RFC access at function group granularity
- `jco.destination.repository_destination` lets metadata queries use a different destination

## Strong signals

- Asks for the exact missing entry from the authorisation trace rather than guessing
- Refuses a blanket role as the quick fix and says what it would cost the audit
- Says what goes wrong with a locally described interface when the ABAP side changes, and how
  they would detect it
- Notices this failed at the first call in production, so it is a landscape difference, not a
  data problem

## Weak signals

- Asks for wide authorisations to unblock the release
- Believes the interface description ships with the client library
- Cannot explain why a function module they never call appears in their error

## Answer bands

### mid

- Recognises it as an authorisation difference between the environments and escalates it.
- Knows the client needs something from SAP before the real call.

### senior

- Explains what the extra call is for and why it happens once rather than every time.
- Requests a narrow, specific authorisation and can justify each part of it.
- Offers the separate-repository-user option and says when it is the right shape.
- Connects the caching to the startup cost and to the per-call-destination anti-pattern.

### lead

- Makes the landscape difference the finding: roles diverge, and the release process should
  surface that before the go-live window.
- Weighs describing the interface locally against the authorisation conversation, in ownership
  cost, not in convenience.
- Sets up how the team will learn about ABAP interface changes rather than discovering them.

## Follow-ups

- Basis offer to grant the role they use in QA. What do you say?
  probes: whether they will take the easy path through an audit boundary
- The security team will not allow any of those lookups at all, ever. Now what?
  probes: describing the interface on the client side, and what that costs later
- Six months on, the team on the other side change a field. Which of your two options notices,
  and when?
  probes: the maintenance cost of owning the description

## Notes

NEEDS-REVIEW — unverified claim about the exact metadata function modules. Newer systems use a
single-roundtrip metadata call; older ones use several individual lookups, and the names differ
by release. Accept any answer that has the mechanism right and do not test names.

NEEDS-REVIEW — unverified claim about how a locally described interface is wired into a
destination in current JCo versions. The capability exists; the exact API is version-dependent.

## Sources

- https://www.ibm.com/support/pages/webmethods-knowlegebase-wmsap-jco-error-no-rfc-authorization-function-module-rfcmetadataget-1806159
- https://javadoc.io/static/com.sap.cloud/neo-java-web-api/2.42.18/com/sap/conn/jco/JCoCustomRepository.html
