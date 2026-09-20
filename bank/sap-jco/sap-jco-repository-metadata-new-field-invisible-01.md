---
id: sap-jco-repository-metadata-new-field-invisible-01
schema_version: 1
title: A new field that only a restart makes visible
category: sap-jco
topic: repository-metadata
level: mid
tags: [caching, operations, failure-modes]
time_estimate_min: 6
order: 80
links:
  deeper: [sap-jco-repository-metadata-locked-down-prod-01]
---

## Ask

An ABAP developer adds a field to a function module's interface and proves it works in SAP. Your
Java service, up for a week, insists the field does not exist — and a restart fixes it. Why?

## Tests

Whether the candidate knows JCo builds calls from interface metadata it fetched remotely and
cached, and can act on that without reaching for a redeploy.

## Listen for

- JCo has to know the interface before it can build the call, and it reads that from SAP once
- The description is cached per repository behind the destination for the life of the process,
  so a week-old process holds a week-old interface
- A restart rebuilds the cache, which is why it looks like a deployment problem
- It can be refreshed without a restart: clear the repository, or drop the one template that
  changed
- The metadata is a remote call to SAP, not something shipped inside the jar

## Expected knowledge

- `JCoDestination.getRepository()` and the function template it hands out
- `JCoRepository.clear()`, and `removeFunctionTemplateFromCache(String)` for a single template

## Strong signals

- Wants the refresh to be a deliberate, small action — an admin endpoint or a flag — rather than
  rolling every pod
- Says that an interface change is a breaking change for a running consumer and belongs in a
  release conversation, not in a Tuesday transport
- Asks whether the field was added as optional, and what happens to the running version if it was
  not

## Weak signals

- Thinks JCo re-reads the interface on every call
- Concludes the only answer is to redeploy
- Blames the transport and stops there

## Answer bands

### weak

- Has no explanation beyond "restarting fixed it".
- Assumes the client library reads the interface fresh each time.

### junior

- Says the interface description is cached and the cache was old.
- Knows a restart is one way to pick it up.

### mid

- Says where the cache lives and how long it lives for.
- Refreshes it without a restart and says which call does that.
- Notices this is a coordination problem between the two teams, not only a technical one.

### senior

- Treats the cache as deliberate — the alternative is a remote lookup per call — and weighs the
  refresh against that.
- Says how a changed interface should be rolled out so no running consumer breaks.
- Points out the same cache is what a per-call destination throws away, and what that costs.

## Follow-ups

- Rolling every instance takes twenty minutes and the change is urgent. What else could you do?
  probes: whether they know the refresh can be targeted, and whether they would build a control
  for it
- Why would a client library hold on to that at all, instead of asking each time?
  probes: the cost of the lookup, and why the design is a deliberate trade
- The ABAP side now wants to change the type of an existing field. What do you ask for?
  probes: compatibility, coordination, and who breaks first

## Notes

If a candidate says "I would just redeploy", ask what they would do if the service could not be
restarted during business hours. That is where the interesting answer starts.

Verified: `JCoRepository.clear()` empties both the function template cache and the record
metadata cache. The targeted call is `removeFunctionTemplateFromCache(String functionName)`, with
`removeRecordMetaDataFromCache` and `removeClassMetaDataFromCache` alongside it. Do not test the
spelling — a candidate who knows a single template can be dropped without clearing everything has
made the point.

## Sources

- https://github.com/cemeng/sap-integration/blob/master/sapjco3-darwinintel64-3.0.14/javadoc/com/sap/conn/jco/JCoRepository.html
- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
