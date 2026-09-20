---
id: sap-jco-troubleshooting-first-call-after-idle-01
schema_version: 1
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

## Listen for

- The shape of the failure is the evidence: it is always the first call after a long quiet
  period, so the suspect is something that happens while nothing is in flight
- The pooled connections were opened yesterday and left open; something on the path — a firewall,
  a load balancer, a NAT device — drops a TCP connection that has been idle too long, and neither
  end is told
- The Java side only finds out when it tries to use that socket, which is exactly why the failure
  lands on the first call and the retry, on a freshly opened connection, succeeds
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
- Says what the service should record so the next occurrence is answerable without the SAP or
  network teams.
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

Verified: the two pool settings behind the second half of the answer are
`jco.destination.expiration_time`, the time in milliseconds after which an idle pooled connection
may be closed, and `jco.destination.expiration_check_period`, the interval in milliseconds at
which the checker thread looks for expired connections. Both matter: setting the first below the
firewall's idle timeout achieves nothing if the second is longer than the gap it is meant to
close. A candidate who spots that there are two numbers, not one, is ahead.

Verified: JCo has sent CPIC keepalive pings to the gateway during long-running RFC client calls
since 3.0.14, specifically to stop network devices closing the socket under an in-flight call.
That is a different case from a connection sitting unused in the pool overnight — do not let the
two be conflated, and note it means a candidate on a modern JCo will not have seen the in-flight
variant of this symptom.

NEEDS-REVIEW — confirmed as genuinely unverifiable rather than merely unchecked. Whether JCo
tests that a pooled connection is still alive before handing it out, or only discovers the dead
socket when the call is sent, is not stated in any reachable documentation, and no property
governing such a check could be found. The documented behaviour is only the idle expiry above.
Do not hold a candidate to either version; the observable behaviour in the field is that the
first call fails, which is all the card needs.

## Sources

- https://github.com/cemeng/sap-integration/blob/master/sapjco3-darwinintel64-3.0.14/javadoc/releasenotes.html
- https://support.sap.com/content/dam/support/en_us/library/ssp/products/connectors/jco/jco_30_documentation_en.pdf
- SAP KBA 2005477, "Configurable SAP JCo pooling parameters" — names every pool property, but the
  full text is behind an S-user login, so it is cited by number rather than linked.
