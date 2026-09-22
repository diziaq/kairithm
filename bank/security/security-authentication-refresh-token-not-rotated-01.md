---
id: security-authentication-refresh-token-not-rotated-01
schema_version: 2
title: A stolen laptop and a ninety-day refresh token
category: security
topic: authentication
level: mid
tags: [security, operations, failure-modes, observability]
time_estimate_min: 8
order: 112
links:
  deeper: [security-authentication-lockout-outlives-the-token-01]
  related: [microservices-idempotency-key-scope-and-lifetime-01]
---

## Ask

Our access tokens last fifteen minutes. The refresh token that renews them lasts ninety days and
can be used over and over. A customer's laptop is stolen. Walk me through what the thief has, and
what you would change.

## Tests

Whether the candidate identifies which of the two credentials actually matters, and can turn theft
of it into something the system notices.

## Ideal minimal answer

The long one is the real credential: the thief mints a fresh access token every fifteen minutes
for ninety days, and nothing distinguishes them from the customer. Hand back a new refresh token
on every use and retire the old one, so a retired one arriving again tells you somebody has a
copy, and end the whole chain when it does.

## Listen for

- Says the short access token lifetime buys nothing while the long one can be reused
- Names the long-lived one as the credential worth stealing, and says its use looks exactly like
  the real customer
- Proposes handing back a new one on each use and retiring the previous one
- Notices that a retired one arriving again means two parties hold a copy, and says what the
  server does then — end the whole chain, not just that one
- Names the cost: an app that never receives the reply, or two copies of it racing, gets signed
  out and has to log in again

## Expected knowledge

- The long-lived token is exchanged at the issuer for a new short-lived one
- Anything the server can retire has to be looked up when it is presented

## Strong signals

- Says the server cannot tell which of the two parties presented the retired one, so it has to end
  the chain and make both log in again
- Asks what the app does when the exchange succeeds but the reply is lost, and stores the new one
  before it uses it
- Wants the event to reach somebody: a retired one arriving is an alert, not a silent rejection
- Asks what else should end the chain — a password change, a sign-out, a support lock

## Weak signals

- Points at the fifteen minutes as the answer and stops
- Lists retirement, device binding and shorter lifetimes with accurate trade-offs and will not
  pick one
- Tells the story of a past breach without saying what they would change here
- Cuts the ninety days to a day and treats the login prompt as free

## Answer bands

### weak

- Says the damage is capped at fifteen minutes.
- Cannot say what the thief does once the access token dies.

### junior

- Says the thief keeps getting new access tokens for as long as the long one lives.
- Suggests shortening the ninety days, or being able to delete it on the server.

### mid

- Proposes replacing the long-lived one on every use and retiring the previous one.
- Says what the server should do when a retired one is presented, once asked.
- Names one way a legitimate app gets caught by that.

### senior

- Raises the double use as the detection before being asked, not only as the fix.
- Says the server cannot tell thief from customer, ends the whole chain, and says who is told.
- Sets the lifetime from what an account is worth here rather than from a round number.

## Follow-ups

- You make the long one single-use. The phone sends it, the reply is lost on the train, and it
  sends it again. What does the customer see?
  probes: the legitimate client caught by rotation, and whether they price that against the gain
- The stolen copy and the real laptop are both in use for a week. What in your system notices?
  probes: reuse as an observable event, and what fires when it happens
- Your CEO asks how long a stolen laptop stays useful. What number do you give, and what does it
  depend on?
  probes: stating the window as a product decision rather than reading a setting

## Sources

- https://www.rfc-editor.org/rfc/rfc9700#section-4.14
- https://www.rfc-editor.org/rfc/rfc7009
- https://www.rfc-editor.org/rfc/rfc8705
- https://owasp.org/Top10/2025/A07_2025-Authentication_Failures/

## Notes

RFC 9700 section 4.14.2 requires one of two mechanisms for public clients: sender-constrained
refresh tokens (RFC 8705 or RFC 9449), or rotation. On rotation it is precise about the limit of
what you learn: "The authorization server cannot determine which party submitted the invalid
refresh token, but it will revoke the active refresh token. This stops the attack at the cost of
forcing the legitimate client to obtain a fresh authorization grant."

That cost is the honest half of the answer, and it is where a candidate who has shipped this
shows. A mobile client that posts the exchange, never receives the reply, and retries with the old
value looks exactly like an attacker. Real implementations either persist the new value before
using it, or allow a short grace window on the immediately previous value — which weakens the
detection. Either choice is defensible; not knowing the problem exists is not.

The fifteen-minute access token is a red herring the candidate is meant to see through: it bounds
nothing while the credential that mints it is reusable for three months.
