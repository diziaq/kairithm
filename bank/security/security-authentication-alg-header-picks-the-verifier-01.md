---
id: security-authentication-alg-header-picks-the-verifier-01
schema_version: 2
title: The token header chooses how the token is checked
category: security
topic: authentication
level: lead
tags: [security, correctness, testing, ownership]
time_estimate_min: 12
order: 116
links:
  related: [general-code-review-approved-then-outage-01]
---

## Ask

You are reviewing a shared verify helper. It reads the algorithm named in the token header and
picks the matching check, so the service accepts HMAC tokens from the legacy issuer and RSA ones
from the new issuer. Both paths have tests and both pass. What do you say?

## Tests

Whether the candidate can construct the substitution attack from the code in front of them, and
turn it into a fix, a rollout and a test.

## Ideal minimal answer

Whoever sends the token chooses which branch runs. Take the new issuer's published RSA public key,
use its bytes as the HMAC secret, sign a token claiming to be anybody, and the helper accepts it.
The key id has to select the key and the check together, one algorithm per key, with the header
never consulted for that choice.

## Listen for

- Names who is in control: the sender decides which branch of the helper executes
- Builds the forged token concretely — the public key's bytes standing in as the shared secret,
  signed by the attacker, accepted as the new issuer's
- Says the public key is published on purpose, so nothing has leaked; the mistake is using a public
  value where a secret is expected
- Binds the choice on the server: the key id selects the key, and each key is tied to exactly one
  algorithm
- Says why the tests passed — each one fed the branch its own fixture named, and none sent a token
  naming the other branch
- Decides what happens to the two issuers in flight, and how the change ships without locking
  anybody out

## Expected knowledge

- A token header names an algorithm and usually a key id
- One key means one algorithm, and the pairing has to be checked when the check runs

## Strong signals

- Writes the malicious token out rather than describing the category of bug
- Asks what else calls this helper, because it is shared, and how every caller is found
- Adds the test that a token naming the other algorithm is rejected, not only that each good path
  works
- Gives the legacy issuer a retirement date rather than "eventually"
- Asks whether anything else in the estate keys off a value the caller supplied

## Weak signals

- Says both algorithms are strong, so accepting either is safe
- Treats it as harmless because the public key was never secret
- Asks for a list of accepted algorithms but still lets the token choose from the list
- Lists the options and will not say what the review comment is
- Blocks the pull request without saying what the author should do instead

## Answer bands

### mid

- Says the token should not decide how it is checked.
- Names a fixed set of accepted algorithms as the fix, once asked.

### senior

- Builds the forged token step by step, unprompted, naming what plays the part of the secret.
- Ties the choice to the key rather than to a list, so one key only ever means one thing.
- Says why the existing tests could not have caught it.

### lead

- Decides the review outcome and the order things ship in: the binding first, then the old
  issuer's retirement.
- Says how every other caller of the shared helper is found and covered.
- Names the test that would have failed, and makes it the guard on the fix.
- Says what happens to tokens already in flight when the change lands.

## Follow-ups

- The author replies that the key is public, so there is nothing secret to steal. What is your
  answer?
  probes: whether they see a public value being used where a secret is expected
- You propose a fixed list of what you accept, and the legacy issuer is on that list. Are you safe?
  probes: that a list the sender still picks from changes nothing
- The change ships and a batch job starts failing at two in the morning. What did you not think
  about?
  probes: issuers and clients still signing the old way, and the order of the rollout
- Both tests were green. What test do you write?
  probes: the negative case — a token naming one thing, offered against a key meant for another

## Sources

- https://www.rfc-editor.org/rfc/rfc8725#section-2.1
- https://www.rfc-editor.org/rfc/rfc8725#section-3.1
- https://www.rfc-editor.org/rfc/rfc7515#section-10.7
- https://owasp.org/Top10/2025/A04_2025-Cryptographic_Failures/

## Notes

RFC 8725 section 2.1 describes this attack in the same shape the card does: an "RS256" token
changed to "HS256" so the verifier will "validate the signature using HMAC-SHA256 and using the
RSA public key as the HMAC shared secret". Section 3.1 gives the fix in two parts, and both
matter: libraries "MUST enable the caller to specify a supported set of algorithms and MUST NOT
use any other algorithms", and separately "each key MUST be used with exactly one algorithm, and
this MUST be checked when the cryptographic operation is performed". RFC 7515 section 10.7 covers
the same ground as algorithm substitution.

The second part is where candidates stop too early. An allow-list containing both HMAC and RSA
does not fix this card's helper — both are legitimately in use here, so both are on the list, and
the sender still chooses. What closes it is the key: resolve the key id first, and the key's own
record says which algorithm it may be used with. The header is then only a claim to be checked
against that, never an input to the decision.

Worth holding the candidate to the rollout. Pinning per key id breaks any issuer or client still
signing the old way, and the legacy issuer in the question is by definition still live. A lead
answer sequences it: publish the key-to-algorithm mapping for both issuers, deploy the binding,
then retire the legacy key on a date.
