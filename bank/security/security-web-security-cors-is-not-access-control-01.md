---
id: security-web-security-cors-is-not-access-control-01
schema_version: 2
title: The finding was closed because CORS only allows our origin
category: security
topic: web-security
level: mid
tags: [security, api-design, correctness]
time_estimate_min: 8
order: 152
links:
  related: [microservices-idempotency-double-click-order-01]
---

## Ask

A pentest report says an internal API is reachable with no authentication. The team's reply is
that the CORS policy only allows our own origin, so nobody else can call it, and the lead has
closed the finding. What do you do?

## Tests

Whether the candidate knows which party enforces that policy and on which requests, and will say
so to a lead who has already decided.

## Ideal minimal answer

Reopen it. That policy is enforced by the browser, on reads a page's script makes to another
origin. Anything that is not a browser — curl, one of our own backends, a phone app, a scanner —
never consults it and gets the data. Show it with one command, then make the API require an
authenticated caller.

## Listen for

- Says who enforces it: the browser, on behalf of a page, and only for calls a script makes
- Says anything that is not a browser never looks at it — a shell, a service, a phone app, a
  scanner
- Offers to demonstrate it in one command rather than argue about it
- Separates the two things: the missing authentication is the bug, the policy is unrelated to it
- Notes the request usually reaches the server anyway, and what is withheld is the reply reaching
  the script

## Expected knowledge

- The policy is sent back in headers and enforced by the client, not the server
- A tight list of permitted origins adds no check on the server

## Strong signals

- Runs the request from a terminal in the meeting and shows the body coming back
- Points out that even from a page the call is still made; only reading the reply is blocked
- Asks what else in the estate rests on the same belief, and whether other internal APIs do
- Says what the finding should be reopened as, and who has to sign it off
- Asks who the API is meant to serve at all, because "internal" is doing a lot of work here

## Weak signals

- Accepts the reply and moves on
- Proposes a narrower list of permitted origins as the fix
- Says the API is internal, so only our own systems can reach it
- Tells the story of a past pentest without saying what happens to this report
- Argues the point in the abstract when a terminal is available

## Answer bands

### weak

- Accepts that the policy keeps other callers out.
- Proposes a narrower list as the fix.

### mid

- Says the rule is enforced by the client and does nothing for a call made outside one.
- Says the missing authentication is the real finding and should be reopened.

### senior

- Offers to demonstrate it from a terminal before the argument goes any further.
- Notes unprompted that the call still reaches the server even from a page, and that what is
  withheld is only the reply.
- Asks what else rests on the same belief, and gets the finding reopened as the right thing.

## Follow-ups

- The team says only our own web app is meant to call it. How do you show that is not what stops
  anybody?
  probes: whether they can produce a caller that never consults the policy
- One of our phone apps calls the same API. Which of these rules has it ever obeyed?
  probes: that the rule lives in one kind of client only
- So what should the report have said?
  probes: naming the missing check as the finding, separately from the policy

## Sources

- https://fetch.spec.whatwg.org/#http-cors-protocol
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS
- https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/

## Notes

The policy is a relaxation, not a restriction. The browser's default is that a script on one
origin may not read a response from another; the response headers are how a server opts to allow
specific origins to do so. Nothing about it is enforced anywhere but in the browser, on behalf of
a page, and only for the reads it governs.

Two details separate a candidate who has actually debugged this:

- For a simple request there is no preflight — the request is sent, the server processes it and
  any side effect happens. The browser then withholds the response from the script. "Blocked by
  CORS" in a console does not mean the server did not act.
- A restrictive policy is still worth having, because it protects *our users' browsers* from other
  sites reading their authenticated responses. It just answers a different question from the one
  the pentest asked. A candidate who says "so the policy is pointless" has overcorrected.

The soft part of this card is the lead having already closed the finding, and it is deliberate.
The answer worth a senior band is a demonstration, not a debate.
