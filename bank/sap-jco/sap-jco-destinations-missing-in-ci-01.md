---
id: sap-jco-destinations-missing-in-ci-01
schema_version: 1
title: The destination is found on a laptop and not in CI
category: sap-jco
topic: destinations
level: junior
tags: [configuration, operations, integration]
time_estimate_min: 5
order: 20
links:
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
- Points out the non-production account should not have been able to do damage anyway.

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

The default provider reads `<destinationName>.jcoDestination` from the working directory. Most
production setups replace it; a candidate who only knows the file is fine at this level.

## Sources

- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
