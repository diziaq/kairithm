---
id: sap-jco-destinations-credential-rotation-01
schema_version: 1
title: The SAP password now rotates every thirty days
category: sap-jco
topic: destinations
level: senior
tags: [security, operations, failure-modes]
time_estimate_min: 8
order: 140
---

## Ask

Security has decided the SAP service account password rotates every thirty days and must not sit
in a file on disk. Six of your services talk to SAP through JCo. How do the credentials get in,
and what breaks the first time it rotates?

## Tests

Whether the candidate knows how JCo takes configuration from the application, and can predict the
failure mode of a rotation against a cache and a shared account.

## Listen for

- JCo resolves a destination through a destination data provider; you supply your own so the
  properties come from the secret store instead of a file
- Only one such provider can be registered per JVM, so this is a startup concern and it collides
  with any framework in the same process that registers its own
- JCo caches the destination data; after a rotation the cache still holds the old password unless
  the provider tells JCo the entry changed
- Existing pooled connections may keep working while every new logon fails, which makes the
  outage look intermittent and delays diagnosis
- Repeated failed logons with a stale password lock the SAP user — and if all six services share
  one account, all six go down together
- Rotation has to be coordinated with Basis; changing the password in the vault alone changes
  nothing in SAP

## Expected knowledge

- `DestinationDataProvider` and the event listener JCo offers for changed or deleted entries
- Where connections are cached and for how long

## Strong signals

- One technical user per consuming service, so one bad rotation does not take out the landscape
- A startup self-check that fails the deployment loudly rather than failing at three in the
  morning
- Wants the rotation rehearsed in a lower environment before it is switched on in production
- Asks what happens to in-flight calls at the moment of rotation

## Weak signals

- Puts the password in an environment variable and calls the requirement met
- Assumes JCo notices the file or the vault changing by itself
- Plans to restart all services on every rotation without saying what that does to running work

## Answer bands

### mid

- Supplies the credentials from outside the code and knows a restart picks up the new value.
- Sees that a wrong password repeated will lock the account.

### senior

- Names where JCo takes configuration from and what has to happen for a change to take effect.
- Predicts the intermittent phase where old connections work and new logons fail.
- Separates the account model from the mechanism, and argues for accounts that fail
  independently.
- Says who has to be involved on the SAP side and in what order the change happens.

### lead

- Designs the rollout so a failed rotation is detected in minutes and can be undone.
- Weighs one shared account against many, in operational cost as well as blast radius.
- Says what the team must not have to do by hand at three in the morning, and builds for that.

## Follow-ups

- The rotation happens at midday and half the calls keep working for twenty minutes. Explain
  that to the incident channel.
  probes: cached entries and already-open connections versus new logons
- The account is locked and three other teams are also down. What went wrong before today?
  probes: shared identity and blast radius, not the rotation itself
- How would you prove this works before the first real rotation?
  probes: rehearsal, and whether they test the failure path

## Notes

NEEDS-REVIEW — unverified claim about account locking: whether and after how many failures a user
is locked is governed by system policy and differs per landscape. Treat "the account can lock" as
the point, not a specific threshold.

## Sources

- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
