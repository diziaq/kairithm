---
id: security-authentication-lockout-outlives-the-token-01
schema_version: 2
title: Support needs to lock an account instantly
category: security
topic: authentication
level: senior
tags: [security, operations, failure-modes, consistency]
time_estimate_min: 10
order: 114
links:
  deeper: [security-authentication-alg-header-picks-the-verifier-01]
  related: [microservices-consistency-two-services-disagree-01]
---

## Ask

Support needs to lock an account the moment fraud calls. Our gateway checks the token's signature
with a local key and never calls the issuer; tokens last twenty-four hours. A pull request changes
that to fifteen minutes and closes the ticket. Is it done?

## Tests

Whether the candidate sees that offline verification traded away revocation, and can price the
ways of buying it back instead of shrinking a number.

## Ideal minimal answer

Locking the account changes nothing at the gateway until the token runs out, so "instantly" is
still up to fifteen minutes. Getting shorter means putting state back in the path: a list the
gateway consults, or asking the issuer per request, or moving the lock to the point where tokens
are renewed. Pick one and say what it costs.

## Listen for

- Says plainly that nothing done to the account has any effect at the gateway until the token runs
  out, because the gateway asks nobody
- Turns the fifteen minutes into the promise support is actually able to make
- Prices the options: a short-lived token plus a renewal step that can be refused, a list the
  gateway consults, or asking the issuer on every request
- Notes each of those puts state and a live dependency back in the request path, which is what
  checking locally was bought to avoid
- Says a list of stopped tokens stays small, because an entry can be dropped once that token would
  have run out anyway
- Picks one for this system and names what would change their mind

## Expected knowledge

- A signed token is checked with a key, so the check needs nothing from the issuer
- A shorter lifetime means more traffic to whatever issues tokens

## Strong signals

- Asks what "instantly" has to mean before designing anything: a number somebody is held to, or a
  feeling
- Points out the renewal step is already a call to the issuer, so it is the cheapest place to put
  the lock
- Notices the gateway now has a dependency that can fail, and says what it does then, open or
  closed, and who decided that
- Separates the cases — a stolen session, a leaver, a fraud lock — and gives them different urgency
- Asks what the customer sees at the moment the lock takes effect mid-session

## Weak signals

- Treats a shorter lifetime as revocation
- Lists the three approaches accurately and will not choose
- Adds a lookup to every request without saying what it costs or what happens when it is not there
- Recounts a past incident without saying what they would do about this one
- Proposes one-minute tokens without costing the traffic that creates

## Answer bands

### mid

- Says a shorter lifetime shrinks the window but does not close it.
- Names one way to stop a token early, once asked.

### senior

- States the promise support can actually make with this design, in minutes.
- Raises the cost of each option in the request path of their own accord: an extra call, a
  shared store, a dependency that can fail.
- Says what the gateway does when that store or the issuer cannot be reached.
- Bounds the list of stopped tokens rather than letting it grow forever.

### lead

- Picks one design for this system and says what would change the choice.
- Separates the urgent cases from the rest and gives them different machinery.
- Says who is paged when the new dependency in the request path fails, and what happens meanwhile.
- Writes down what support may promise a caller, and holds the design to it.

## Follow-ups

- Support says a minute is fine and an hour is not. What does that tell you that you did not have
  before?
  probes: whether the requirement drives the design rather than a round number
- You add a list the gateway reads on every request. It is down for four minutes. What does the
  gateway do?
  probes: failing open versus failing closed, and who is allowed to make that call
- A regulator asks whether a locked account can still act on the system. What do you show them?
  probes: whether the answer is evidence rather than a configuration value
- The fifteen-minute change is already merged. What does it cost you, and is it worth keeping?
  probes: renewal traffic and issuer load, and whether the change was free

## Sources

- https://www.rfc-editor.org/rfc/rfc7662
- https://www.rfc-editor.org/rfc/rfc7009
- https://www.rfc-editor.org/rfc/rfc9700#section-4.14
- https://owasp.org/Top10/2025/A07_2025-Authentication_Failures/

## Notes

The whole point of verifying a signed token with a local key is that the gateway needs nothing
from anyone. Revocation is the bill for that. There are exactly three families of answer and each
reintroduces something:

- **Short access token plus a refusable renewal.** The lock lands at the renewal call, which is
  already a round trip to the issuer, so it adds nothing to the hot path. The floor on "instantly"
  becomes the access token lifetime. Cheapest and usually right.
- **A list of stopped tokens the gateway consults.** Sub-second, at the price of a store in the
  request path and a decision about what to do when it is unavailable. Bounded, because an entry
  can be discarded once the token's own expiry has passed — that is the detail that separates
  somebody who has built it.
- **Introspection per request** (RFC 7662). Exact, and the most expensive: a network call on every
  request and an issuer that is now on the critical path for all traffic.

A candidate who only shrinks the number has not noticed that fifteen minutes is still a promise
somebody has to keep. A candidate who adds a lookup to every request and does not mention what
happens when it fails has moved the outage rather than removed it.
