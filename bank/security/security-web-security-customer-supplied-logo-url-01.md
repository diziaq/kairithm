---
id: security-web-security-customer-supplied-logo-url-01
schema_version: 2
title: The customer pastes in the URL of their own logo
category: security
topic: web-security
level: senior
tags: [security, failure-modes, operations]
time_estimate_min: 10
order: 154
links:
  related: [microservices-failure-handling-cascade-slow-dependency-01]
---

## Ask

A customer pastes the URL of their company logo into our settings page. Our service fetches it and
stores a copy. It has been live for a year and we run on EC2. What is the first thing you want to
know?

## Tests

Whether the candidate immediately asks what the server can reach that the customer cannot, and
can name a defence that survives a mistake in the checks.

## Ideal minimal answer

What our server can reach from where it sits that the customer cannot: the instance's own metadata
endpoint, internal admin pages with no login, database ports. The fetch runs inside our network
with our identity. So resolve the name, refuse private and loopback ranges, connect to the address
you checked, and do not follow redirects blindly.

## Listen for

- Asks straight away what the server can reach from where it sits that the customer cannot
- Names the metadata endpoint on the instance and what it hands out — the instance role's keys
- Names internal targets beyond that: an admin page with no login, a health endpoint, a database
  port, another tenant's service
- Resolves the name, checks the result against private, loopback and link-local ranges, then
  connects to that same result rather than the name again
- Says a redirect moves the target after the check, so redirects are refused or re-checked
- Requires the version of the metadata endpoint that demands a token first, and says the older one
  has to be switched off for that to matter
- Puts the fetching code where it cannot reach anything internal, as the defence that survives a
  mistake in the checks

## Expected knowledge

- A server on EC2 can read its own role keys from a fixed local URL
- A name can point somewhere else the second time it is looked up

## Strong signals

- Asks what the instance role is permitted to do, because that is the ceiling on the damage
- Says the check and the connection have to use the same result, and names doing it twice as the
  bug
- Asks whether the stored copy is served back to other customers, which is a separate problem
- Names switching the older metadata endpoint off, not just defending against it
- Asks how they would find out whether this has already been used in the past year

## Weak signals

- Checks the URL's shape — scheme, extension, size cap — and calls it done
- Blocks one well-known number by string match
- Talks about the logo being a malicious file rather than about where the fetch goes
- Lists the defences accurately and will not say which one ships first
- Recounts a past incident without saying what happens to this service

## Answer bands

### mid

- Says a customer can make our server fetch something we did not intend, once asked what the URL
  could point at.
- Names one internal thing the server could be pointed at.

### senior

- Opens on what the server can reach from inside that the customer cannot, without waiting to be
  asked.
- Names the keys the instance itself can hand over, and what an attacker does with them next.
- Says the name has to be turned into an address, checked, and then connected to directly, and why
  checking the name alone is not enough.
- Treats a redirect as a way past the check.

### lead

- Picks the order: what ships today, what ships this quarter, and what the fetching code's network
  is allowed to touch at all.
- Says how they would find out whether this has already happened in the past year.
- Names what the instance role may do as the bound on the damage, and reduces it.
- Says who is told, and what the customers are told, if it has.

## Follow-ups

- The pull request checks the URL starts with https, ends in .png, and caps the download at two
  megabytes. Are we done?
  probes: whether checking the shape is being mistaken for a control
- We block the one well-known internal number. The customer's own DNS answers with it a second
  later. What went wrong?
  probes: the gap between the check and the connection
- It has been live for a year. How do you find out if anybody has already done this?
  probes: going looking for evidence rather than only patching forward
- Which single change would you ship tonight?
  probes: whether they will choose, and whether the choice survives a mistake elsewhere

## Sources

- https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-metadata-v2-how-it-works.html
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-options.html
- https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/
- https://www.rfc-editor.org/rfc/rfc4193
- https://www.rfc-editor.org/rfc/rfc3927

## Notes

Server-side request forgery is no longer its own category: the OWASP Top 10 2025 folded it into
A01, Broken Access Control. Do not quote it as A10, which is where the 2021 list had it.

Ranges to refuse, with the correct prefixes: `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`,
`192.168.0.0/16`, `169.254.0.0/16` (link-local, RFC 3927 — this is the one that covers
`169.254.169.254`), and for IPv6 `::1/128` and `fc00::/7`. The unique-local prefix is `fc00::/7`,
not `fd00::/8`; a candidate who says either is fine, but do not let a wrong figure stand as if it
were checked. AWS also serves metadata over IPv6 at `fd00:ec2::254` on Nitro instances, so a
blocklist built only from IPv4 literals has a hole.

On IMDSv2, the mechanics matter because the mitigation depends on them. The caller must first
`PUT` to `http://169.254.169.254/latest/api/token` with an `X-aws-ec2-metadata-token-ttl-seconds`
header, then pass the returned token in `X-aws-ec2-metadata-token` on each `GET`. A `PUT` carrying
an `X-Forwarded-For` header is rejected, and the response hop limit defaults to 1. That is
precisely what a naive fetch cannot do: it issues a `GET` with no token, and gets a 401 — but only
once the instance is configured to *require* tokens. By default an instance accepts both versions,
so "we're on IMDSv2" is worth one more question: is IMDSv1 turned off?

The answer that survives everything else being wrong is the last bullet in `Listen for`: run the
fetching code somewhere with no route to internal infrastructure. Every parsing and resolution
check on this list has been bypassed in the wild; a network with nothing to reach has not.
