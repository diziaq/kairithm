---
id: sap-jco-troubleshooting-first-call-after-idle-01
schema_version: 2
title: The first call of the morning always fails
category: sap-jco
topic: troubleshooting
level: mid
tags: [failure-modes, retries, operations]
time_estimate_min: 7
order: 95
links:
  deeper: [sap-jco-troubleshooting-works-for-abap-dev-01]
  related: [sap-jco-rfc-fundamentals-timeout-unknown-outcome-01]
---

## Ask

Every morning the first call into SAP fails with a communication error, and the same call a
second later works. It never happens during the day. The SAP team say they see nothing at all on
their side at that time. What is happening, and what do you change?

## Tests

Whether the candidate can get from a time-of-day pattern to a connection that died while nobody
was using it, and can say which calls they would let a machine repeat.

## Ideal minimal answer

The pool handed out a connection opened yesterday whose socket something on the path — a
firewall or NAT device — dropped while it was idle, so the Java side only finds out when it
tries to use it and the retry succeeds. Get the real idle timeout from whoever owns that device
and expire pooled connections well before it; only repeat calls that are harmless to run twice.

## Listen for

- The shape of the failure is the evidence: it is always the first call after a long quiet
  period, so the suspect is something that happens while nothing is in flight
- The pooled connections were opened yesterday and left open; something on the path — a firewall,
  a load balancer, a NAT device — drops a TCP connection that has been idle too long, and neither
  end is told
- By default the Java side only finds out when it tries to use that socket, which is exactly why
  the failure lands on the first call and the retry, on a freshly opened connection, succeeds
- There is a setting that makes the pool probe the far side before handing a connection over, and
  it is off unless somebody turned it on — that is a third change worth weighing, not a free win
- "Nothing on their side" is consistent with that: the request never reached a work process, so
  there is nothing for them to find
- Two changes, not one: get the real idle timeout of every device on the path from whoever owns
  it, and make the pool discard idle connections well before that
- A bounded retry on a failure of this kind is reasonable, but only where a repeat is harmless —
  a read yes, a posting whose outcome is unknown not automatically
- Separates a call that never got accepted from one that died after SAP had it; only the first
  can be repeated without asking a question first

## Expected knowledge

- A `JCoDestination` hands out connections from a pool and keeps them open between calls
- Idle connections in the pool are closed after a configurable time, and how often that is
  enforced is a second setting
- Whether a pooled connection is checked before it is handed out is itself configurable, and the
  default is not to check

## Strong signals

- Asks for the idle timeout of the devices between the two systems before touching any setting
- Asks whether it also happens after a quiet lunchtime, to confirm it is idleness and not a clock
- Says that wrapping a posting in a silent repeat is how a business ends up with two postings
- Wants the pool setting and the network rule recorded together, because the next firewall change
  breaks this again

## Weak signals

- Wraps every call in a blanket retry and closes the ticket
- Blames SAP because the word SAP is in the error
- Restarts the service every morning, or enlarges the pool, as the remedy
- Tells the story of a firewall dropping idle connections at a previous job, and never says what
  they would change about this pool

## Answer bands

### junior

- Notices it is the first call after a long gap and guesses the connection is no longer usable.
- Suggests repeating the call, without saying which calls that is safe for.

### mid

- Explains that a pooled connection can be dead while the pool still believes it is open, and
  names the network path as the likely cause.
- Expires idle connections sooner than whatever closes them, and asks the network owner for the
  actual number rather than picking one.
- Restricts the automatic repeat to calls that can run twice without consequence.

### senior

- Separates a failure before the call was accepted from one after, and handles them differently.
- Says, without waiting to be asked, what the service should record so the next occurrence is
  answerable without the SAP or network teams.
- Keeps the pool setting and the firewall rule tied together, and names where that is written
  down and who reviews it.

## Follow-ups

- Somebody proposes the service simply tries every failed call a second time. Which of your calls
  would you let it do that to?
  probes: whether a repeat is safe, and the posting whose fate is unknown
- Six months later the same shape comes back, right after a change on the network. What would you
  want in place so that costs an hour instead of a week?
  probes: recording enough detail, and keeping the two timeouts in step
- The SAP team offer to search their logs again for that exact minute. Is that worth their time?
  probes: whether the candidate has realised the request never arrived

## Notes

Verified in the decompiled JCo 3.1.14. The two pool settings behind the second half of the answer
are `jco.destination.expiration_time`, the milliseconds an idle pooled connection may sit before
it may be closed, and `jco.destination.expiration_check_period`, the interval at which the sweep
runs. Both default to 60000 ms in `com.sap.conn.jco.rt.RfcDestination.setProperties`. The sweep is
`com.sap.conn.jco.rt.PoolingFactory.isTimedOut`, driven by `com.sap.conn.jco.rt.PoolTimeoutChecker`
on the shared task scheduler, and it walks only the idle list, comparing each connection's
`last_active_timestamp`. So a connection's real lifetime after going idle is somewhere between
`expiration_time` and `expiration_time + expiration_check_period` — which is exactly why setting
the first below the firewall's idle timeout achieves nothing if the second is longer than the gap
it is meant to close. A candidate who spots that there are two numbers, not one, is ahead.

Verified, and this replaces the previous flag: **JCo can test a pooled connection before handing
it out, and by default it does not.** The property is `jco.destination.pool_check_connection`
(`com.sap.conn.jco.ext.DestinationDataProvider.JCO_POOL_CHECK_CONNECTION`). `RfcDestination`
reads it through `JCoRuntime.toBoolean`, which returns `false` for a missing value, so the check
is off unless configured. When it is on, `PoolingFactory.getClient` applies it only to a
connection taken from the idle list — never to one it has just created — and a candidate that is
valid and passes `isAlive()` but fails `isPartnerReachable()` is disconnected, deallocated, and
the loop takes the next one.

The two checks are not the same thing, and the distinction is the good part of this card.
`com.sap.conn.jco.rt.AbstractConnection.isAlive()` is `rfcHandle.RfcIsValidHandle()`, a purely
local test of the handle — it cannot see a socket a firewall dropped. `isPartnerReachable()`
goes through `com.sap.conn.rfc.engine.RfcIoOpenCntl` to
`com.sap.conn.rfc.driver.CpicDriver.isPartnerReachable`, which issues `SAP_CMKEEPALIVE(200)` — a
real round trip to the partner. So with the defaults a socket dropped overnight is discovered on
the first real call; with the check enabled JCo pings first and silently swaps the dead connection
out, at the cost of a round trip on every pooled hand-out. That is a genuine third option
alongside the expiry setting and the firewall rule, and a candidate who asks for it should be
asked what the extra round trip costs at their call rate.

Correction to what this card previously said about keepalives. The properties exist —
`jco.cpic_keep_alive_period` defaults to 300 and `jco.cpic_keep_alive_timeout` to 100 in
`com.sap.conn.jco.rt.JCoRuntime`, and the period must be 0 or in `[10..86400]`. But in 3.1.14 they
are pushed into the native layer through a method called
`com.sap.conn.rfc.api.RfcRuntime.setupRegKeepAlive`, and the read budget derived from them,
`CpicDriver.maxReadTimeoutInMillis`, is consumed only by
`com.sap.conn.rfc.driver.RfcTypeRegisterCpic` — the **registered server** connection type. The
client type, `RfcTypeDirectCpic`, does not use it. Whether the native CPIC library also pings on
an outbound client conversation is not visible from the Java side, so do not tell a candidate
that client calls are protected by it. What the card needs stands either way: a keepalive during
an in-flight call is a different case from a connection sitting unused in the pool overnight, and
the two should not be conflated.

## Sources

- https://github.com/cemeng/sap-integration/blob/master/sapjco3-darwinintel64-3.0.14/javadoc/releasenotes.html
- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
- SAP KBA 2005477, "Configurable SAP JCo pooling parameters" — names every pool property, but the
  full text is behind an S-user login, so it is cited by number rather than linked.
