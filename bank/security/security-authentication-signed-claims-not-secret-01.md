---
id: security-authentication-signed-claims-not-secret-01
schema_version: 2
title: Two new claims in the login token, because it is signed
category: security
topic: authentication
level: junior
tags: [security, api-design, correctness]
time_estimate_min: 6
order: 110
links:
  deeper: [security-authentication-refresh-token-not-rotated-01]
  related: [microservices-api-evolution-renamed-field-broke-consumer-01]
---

## Ask

A pull request adds two claims to our login token: the customer's date of birth, and an internal
risk band. The comment says "safe to include, the token is signed". The mobile app will read the
risk band to decide which screens to show. What do you say in review?

## Tests

Whether the candidate knows that a signature fixes what a token says and not who can read it, and
can act on that rather than repeat it.

## Ideal minimal answer

The signature stops the customer changing the token, not reading it. Anyone holding it can decode
both new values, and so can anything the token gets written into. So the date of birth should not
go in there. Reading the risk band to pick a screen is fine as long as the server decides again
for itself.

## Listen for

- Says the payload is only encoded, so whoever holds the token can read both new values
- Separates what the signature buys — the values cannot be altered without the check failing —
  from keeping them private
- Names a place the token gets written down: a proxy log, an error report, device storage, a
  ticket a customer pasted it into
- Treats the risk band in the app as a display choice, and says the server still decides

## Expected knowledge

- A token is sent on every request and is readable by whoever holds it
- Signing and encrypting are different operations with different purposes

## Strong signals

- Asks why the risk band has to be in the token at all, rather than fetched when the screen needs it
- Points out a token cannot be taken back once issued, so the two values stay live until it expires
- Asks who else already reads this token, because the claims become a contract the moment they ship

## Weak signals

- Says the token is encrypted, or that the encoding makes it private
- Proposes encrypting the whole token instead of asking why the data is in it
- Treats the app not showing the risk band as the thing that keeps it private
- Says only our own apps ever see the token

## Answer bands

### weak

- Agrees both claims are safe because the token is signed.
- Says the contents are encrypted.
- Cannot say what a holder of the token can see.

### junior

- Decodes the payload, or says plainly that whoever holds the token can read both values.
- Says the date of birth does not belong in there.
- Keeps the signature as protection against the values being altered, not against being read.

### mid

- Names a place the token is written down where the two values would now sit as well, once asked.
- Says the server checks the risk band itself rather than trusting the screen the app picked.
- Asks what the risk band is doing in the token in the first place.

## Follow-ups

- Somebody on the call asks you to prove your point in ten seconds, with a real token in front of
  you. What do you do?
  probes: whether they can decode the payload themselves rather than argue from memory
- The customer edits the risk band in the token and sends the request again. What happens?
  probes: that integrity still holds, and whether they conflate that with privacy
- Someone points out the token already carries the customer's own id and their role. Why are these
  two different?
  probes: telling data the holder already knows from data they are not meant to have

## Sources

- https://www.rfc-editor.org/rfc/rfc7519#section-12
- https://www.rfc-editor.org/rfc/rfc8725#section-3
- https://owasp.org/Top10/2025/A07_2025-Authentication_Failures/

## Notes

RFC 7519 section 12 is the direct authority: "A JWT may contain privacy-sensitive information.
When this is the case, measures MUST be taken to prevent disclosure of this information to
unintended parties", and it names omitting the information as the simplest of those measures. A
signature is integrity only — the claims are base64url-encoded, not encrypted; encryption needs a
separate construction (JWE), which RFC 8725 treats as a deliberate choice rather than a default.

The candidate who says "so let's encrypt the token" has answered a different question. The one to
reward asks why the risk band is in the token at all.

Two claims are not equivalent here, and a good candidate separates them: the customer's own id and
role are things the customer already knows, so putting them in a readable token costs nothing. The
date of birth and an internal risk band are not.
