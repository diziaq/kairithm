---
id: sap-jco-repository-metadata-locked-down-prod-01
schema_version: 2
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

## Ideal minimal answer

JCo reads the interface from SAP with its own RFC calls to metadata function modules before it
can build the call; that is the unfamiliar name, and those calls need `S_RFC` of their own,
which production's trimmed role does not grant. The description is cached per system for the
life of the process, so it failed on the first call; ask for that one entry, not a wider role.

## Listen for

- Before JCo can build a call it fetches the interface description from SAP, and it does that
  with its own remote calls to metadata function modules
- Those calls need RFC authorisation in their own right, so a production role trimmed to "just
  the agreed function group" locks them out
- QA and production differing in roles is the ordinary cause of "but it works in QA"
- The ask is a specific `S_RFC` entry for the metadata lookups, not a broader role — or a
  separate destination and user for repository queries
- The lookups cost roundtrips, which is why they happen once per system and are then cached for
  the life of the process — so the cost, and the failure, land on the first call and not later
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
- Connects the caching to the startup cost, and to why this surfaced on the very first call
  rather than intermittently.

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

Verified against the decompiled JCo 3.1.14, replacing the previous flag on the metadata function
modules. The premise is sound: JCo really does make its own RFC calls to read interface
descriptions, and the name in the error genuinely varies.

`com.sap.conn.jco.rt.AbapRepository` builds one of two helpers. The classic one,
`AbapRepository.DDICHelper`, calls `RFC_GET_FUNCTION_INTERFACE`, `DDIF_FIELDINFO_GET`,
`FUNCTION_IMPORT_INTERFACE` and `RFC_GET_STRUCTURE_DEFINITION` — several roundtrips per function.
The optimised one, `AbapRepository.TurboDDICHelper`, uses the single call `RFC_METADATA_GET`
(template built in `com.sap.conn.jco.rt.StaticFunctionTemplates.createRFC_METADATA_GETTemplate`).

Correction to what this card previously said: the optimisation is **on by default** in 3.1, not
opt-in. `com.sap.conn.jco.rt.JCoRuntime` seeds `jco.use_repository_roundtrip_optimization` with
`"1"`, and `AbapRepository.createDDICHelper` takes the classic path only when that property is
explicitly `"0"`. Otherwise it consults `RfcDestination.hasEntryAndSupportsTurboRepository`, which
reads the per-destination override `jco.destination.repository_roundtrip_optimization`, and where
neither is set it uses the single-roundtrip path for any backend of release 7.40 or higher and
probes the backend for `RFC_METADATA_GET` below that. Practical consequence for this card: on a
current landscape the name in the authorisation error is most likely `RFC_METADATA_GET`, and the
older names appear only where the optimisation has been switched off or the backend is old.

The function group `SDIFRUNTIME` shows up in exactly this kind of failure, but that is an ABAP-side
fact and is not visible in the jar. Still do not test names — the mechanism is the point.

Verified: `S_RFC` carries the fields `RFC_TYPE`, `RFC_NAME` and `ACTVT`, where `ACTVT` only ever
takes the value for execute. Function-group granularity is the normal usage; single-function
granularity is also possible but rarely used. On newer releases UCON, the unified connectivity
framework, adds a separate allow-list layer on top of `S_RFC` rather than changing it — if a
candidate raises UCON, that is a strong signal, not a confusion.

Verified in JCo 3.1.14, and the previous flag is removed. Describing the interface locally is
unchanged from 3.0: `com.sap.conn.jco.JCo.createCustomRepository(String name)` returns a
`JCoCustomRepository`, whose whole interface is `addFunctionTemplateToCache`,
`addRecordMetaDataToCache`, `addClassMetaDataToCache`, `setDestination`, `setQueryMode` and the
nested `QueryMode` enum. `setDestination` is what serves a cache miss from the backend;
`com.sap.conn.jco.JCoCustomDestination.setRepositoryDestination` points a destination's metadata
lookups elsewhere. `com.sap.conn.jco.JCoDestination` still has `getRepository()` and no
`setRepository` — grepping 3.1.14, `setRepository` exists only on `JCoServer`.

The separate-repository-user option in `## Listen for` is real:
`com.sap.conn.jco.ext.DestinationDataProvider` carries `jco.destination.repository_destination`
alongside `jco.destination.repository.user` and `jco.destination.repository.passwd` — note the
inconsistent punctuation, underscore in the first and a dot in the others — and `JCoDestination`
exposes `getRepositoryUser()`. Note
that `com.sap.conn.jco.rt.RepositoryManager.getRepository` caches by system key —
`ConnectionAttributes.getSystemKey()` is the system id plus the installation number — so several
destinations pointing at the same SAP system share one metadata cache rather than one each.

## Sources

- https://help.sap.com/doc/saphelp_snc700_ehp01/7.0.1/en-US/60/305140c770cd01e10000000a155106/content.htm?no_cache=true
- https://github.com/cemeng/sap-integration/blob/master/sapjco3-darwinintel64-3.0.14/javadoc/releasenotes.html
- https://github.com/cemeng/sap-integration/blob/master/sapjco3-darwinintel64-3.0.14/javadoc/com/sap/conn/jco/JCoCustomRepository.html
- https://www.ibm.com/support/pages/webmethods-knowlegebase-wmsap-jco-error-no-rfc-authorization-function-module-rfcmetadataget-1806159
