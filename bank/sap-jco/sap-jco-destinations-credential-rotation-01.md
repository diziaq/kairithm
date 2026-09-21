---
id: sap-jco-destinations-credential-rotation-01
schema_version: 2
title: The SAP password now rotates every thirty days
category: sap-jco
topic: destinations
level: senior
tags: [security, operations, failure-modes]
time_estimate_min: 8
order: 140
links:
  related: [sap-jco-repository-metadata-locked-down-prod-01]
---

## Ask

Security has decided the SAP service account password rotates every thirty days and must not sit
in a file on disk. Six of your services talk to SAP through JCo. How do the credentials get in,
and what breaks the first time it rotates?

## Tests

Whether the candidate knows how JCo takes configuration from the application, and can predict the
failure mode of a rotation against a cache and a shared account.

## Ideal minimal answer

Supply the properties through your own destination data provider reading the secret store, and
tell JCo the entry changed, because it caches it. Credentials are presented only when a
connection is opened, so after a rotation the connections already in the pool keep working while
new logons fail — unless SAP tears those sessions down, which I would check — and repeated
failures can lock a shared account.

## Listen for

- JCo resolves a destination through a destination data provider; you supply your own so the
  properties come from the secret store instead of a file
- Only one such provider can be registered per JVM, so this is a startup concern and it collides
  with any framework in the same process that registers its own
- JCo caches the destination data; after a rotation the cache still holds the old password unless
  the provider tells JCo the entry changed
- Existing pooled connections keep working while every new logon fails, because the password is
  presented once when the connection is opened and not on each call — which makes the outage look
  intermittent and delays diagnosis
- Repeated failed logons with a stale password can lock the SAP user, depending on how the system
  is configured — and if all six services share one account, all six go down together
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
- Expects a messy partial failure rather than a clean outage, and can say why a connection that
  is already open might behave differently from one being established.
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

Verified, replacing the previous flag on account locking: `login/fails_to_user_lock` sets the
number of consecutive failed logons before a user is locked. It is a configurable integer, the
current default is 5 where older releases defaulted to 12, and by default the lock clears at
midnight. So "the account can lock, and I would ask what the policy is here" is the correct
answer; a candidate quoting a specific number as universal is wrong, and so is an interviewer
expecting one.

Verified: JCo caches destination configuration. A provider that implements event support tells
JCo an entry changed through `DestinationDataEventListener` (`updated` / `deleted`); where the
provider does not, the JCo runtime re-checks cached configuration periodically instead. No public
documentation gives a fixed interval for that fallback, so do not let the candidate — or
yourself — depend on a number. Note this is destination *configuration* caching, which is a
different thing from the pool's idle-connection expiry settings; candidates conflate the two.

Verified in the decompiled JCo 3.1.14, and the previous flag is removed: on the client side, an
open pooled connection is reused without a new logon. `com.sap.conn.jco.rt.PoolingFactory.getClient`
calls `connect()` only when the connection is not already connected — the guard is
`if ((client.state & 2) == 0)` — and `com.sap.conn.jco.rt.ClientConnection.connect()` is where the
credentials are presented, through `RfcApi.RfcOpen(this.logonParams)`. So the logon happens once
per physical connection, at open, and never again while that connection lives. After a password
change, connections already open in the pool keep working; only a new `RfcOpen` presents the
credentials and fails. The messy partial failure the `senior` band asks for is therefore the
correct prediction, not a guess.

The one thing the client jar cannot settle, and the interviewer should not assert: whether the
SAP system itself invalidates an existing session when the password is changed. If it does, the
partial-failure window closes immediately and the outage looks total. A candidate who predicts a
clean total outage has not said anything wrong; a candidate who says "the already-open ones
should survive unless SAP tears the sessions down, and I would check that" has said the better
thing.

Verified: only one `DestinationDataProvider` may be registered per JVM.
`com.sap.conn.jco.rt.RuntimeEnvironment.setDestinationDataProvider` holds it in a static field and
throws `IllegalStateException("DestinationDataProvider already registered [...]")` on a second
attempt, which is precisely the collision with an in-process framework that the second
`## Listen for` bullet describes. `com.sap.conn.jco.ext.DestinationDataEventListener` declares
exactly `updated(String)` and `deleted(String)`, and a provider advertises whether it will use
them through `DestinationDataProvider.supportsEvents()`.

## Sources

- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
- https://help.sap.com/docs/SAP_NETWEAVER_AS_ABAP_751_IP/f7dd32926c1c4fcf889a4303d833a22b/4ac3f18f8c352470e10000000a42189c.html
- http://www.novell.com/documentation/ncmp_sap10/sap_user_jco3/data/bldfbln.html
