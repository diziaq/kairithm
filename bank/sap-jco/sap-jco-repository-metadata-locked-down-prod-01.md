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

Verified, replacing the previous flag on the metadata function modules. JCo's own release notes
state that it normally calls several function modules to assemble the description of one
function and its structures, and that `RFC_METADATA_GET` — introduced by SAP Note 1456826, in
function group `RFC_METADATA` — reduces that to a single roundtrip. JCo uses it only if the
backend has it and the property `jco.use_repository_roundtrip_optimization` is set. The older
multi-roundtrip path involves function modules such as `RFC_GET_FUNCTION_INTERFACE` and
`DDIF_FIELDINFO_GET`, and the function group `SDIFRUNTIME` is one that shows up in exactly this
kind of authorisation failure. So the card's premise is sound and the name in the error genuinely
does vary. Still do not test names — the mechanism is the point, and the exact release in which
each backend gained `RFC_METADATA_GET` is not publicly pinned down.

Verified: `S_RFC` carries the fields `RFC_TYPE`, `RFC_NAME` and `ACTVT`, where `ACTVT` only ever
takes the value for execute. Function-group granularity is the normal usage; single-function
granularity is also possible but rarely used. On newer releases UCON, the unified connectivity
framework, adds a separate allow-list layer on top of `S_RFC` rather than changing it — if a
candidate raises UCON, that is a strong signal, not a confusion.

NEEDS-REVIEW — narrowed. The API for describing an interface locally is confirmed for JCo 3.0.x:
`JCo.createCustomRepository(name)`, then `addFunctionTemplateToCache(...)`, with
`JCoCustomRepository.setDestination(...)` for cache misses and
`JCoCustomDestination.setRepositoryDestination(...)` to point a destination elsewhere. Note there
is no `setRepository` on a plain `JCoDestination` — only a getter. What could not be confirmed is
that this is unchanged in JCo 3.1, because the 3.1 documentation ships only inside the SDK
download behind an S-user login. Treat the capability as certain and the exact call sequence as
"check against the version in use".

## Sources

- https://help.sap.com/doc/saphelp_snc700_ehp01/7.0.1/en-US/60/305140c770cd01e10000000a155106/content.htm?no_cache=true
- https://github.com/cemeng/sap-integration/blob/master/sapjco3-darwinintel64-3.0.14/javadoc/releasenotes.html
- https://github.com/cemeng/sap-integration/blob/master/sapjco3-darwinintel64-3.0.14/javadoc/com/sap/conn/jco/JCoCustomRepository.html
- https://www.ibm.com/support/pages/webmethods-knowlegebase-wmsap-jco-error-no-rfc-authorization-function-module-rfcmetadataget-1806159
