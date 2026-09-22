---
id: sap-jco-destinations-missing-in-ci-01
schema_version: 2
title: The destination is found on a laptop and not in CI
category: sap-jco
topic: destinations
level: junior
tags: [configuration, operations, integration]
time_estimate_min: 5
order: 20
links:
  related: [spring-configuration-property-precedence-01]
  deeper: [sap-jco-destinations-credential-rotation-01]
---

## Ask

Your integration runs on your laptop but the pipeline fails saying the destination cannot be
found — and when a colleague patched that last week, the tests ran for an hour against the
production system. How does JCo work out which system a destination name points at, and how would
you set this up so that second part cannot happen again?

## Tests

Whether the candidate knows that a destination name is only a lookup key resolved from
environment-specific configuration, and treats pointing at the wrong system as a real risk.

## Ideal minimal answer

The destination name is only a lookup key: the host, system number, client, user and password
come from configuration on the machine that runs the code, and the pipeline has none. Deliver
that configuration per environment with the secret from outside the repository, and give each
environment its own destination name so a test run cannot point at production.

## Listen for

- The name is resolved by a destination data provider; out of the box that means a properties
  file named after the destination, sitting on the machine that runs the code
- The properties carry host, system number, client, user and password — the name itself means
  nothing
- The pipeline fails because that file is not there, so the fix is configuration delivery, not
  code
- Credentials do not belong in the repository, so the two environments were always going to
  differ; the question is how the difference is managed
- Naming two environments the same way is exactly how a test run ends up in production

## Expected knowledge

- `jco.client.ashost`, `jco.client.sysnr`, `jco.client.client`, `jco.client.user`
- `JCoDestinationManager.getDestination(name)` takes a name, not a host

## Strong signals

- Names the client number as the field that separates two systems that can share a host
- Wants the service to report which system it connected to at startup, so a wrong target is
  visible in the first log line rather than in the data
- Asks whether the technical user in the non-production system is even allowed to write

## Weak signals

- Thinks the destination name itself identifies the system
- Would fix it by committing the file
- Has no answer for how anyone would notice they were pointed at the wrong system
- Recounts how a run against the wrong system was caught at a previous job and never says what
  to change here

## Answer bands

### weak

- Cannot say where the connection details come from at all.
- Proposes hard-coding the host in the code.

### junior

- Says the details live in configuration outside the code and the pipeline is missing it.
- Names some of the fields that identify the target system.

### mid

- Describes how the configuration is delivered per environment and where the secret comes from.
- Makes the target system visible at startup, and can say what would have caught the production
  accident before an hour had passed.
- Points out before being asked that the non-production account should not have been able to do
  damage anyway.

## Follow-ups

- The file is there and the details look right, but the logon is refused. What are the first two
  things you separate?
  probes: reaching the system versus being allowed in
- Somebody copies the file from the test box to get a local run working. What have they now got on
  their laptop?
  probes: credential handling, and whether they see the copy as a leak
- How would the team find out on the day it happens, rather than a week later?
  probes: whether they instrument the target system as an observable fact

## Notes

Verified in the decompiled JCo 3.1.14: the built-in provider is
`com.sap.conn.jco.rt.PropertyFileDestinationDataProvider`, whose `DESTFILE_SUFFIX` is the literal
`".jcoDestination"`, so the file it looks for is `<destinationName>.jcoDestination` in the
directory it was given. Most production setups replace it with their own
`com.sap.conn.jco.ext.DestinationDataProvider`; a candidate who only knows the file is fine at
this level.

Verified, and worth knowing before running the first follow-up: a mistyped property is not an
error. `com.sap.conn.jco.rt.RfcDestination.getIntProperty` and `getLongProperty` catch every
exception and silently return the default. So "the details look right" is exactly the situation
where a wrong value produces default behaviour rather than a complaint.

## Sources

- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf

- https://github.com/rafaelfvalim/JcoAbapDojo/blob/main/ABAP_AS1.jcoDestination
