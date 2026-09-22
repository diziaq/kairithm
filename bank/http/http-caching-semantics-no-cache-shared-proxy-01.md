---
id: http-caching-semantics-no-cache-shared-proxy-01
schema_version: 2
title: Someone else's invoices
category: http
topic: caching-semantics
level: junior
tags: [correctness, api-design, failure-modes]
time_estimate_min: 6
order: 135
links:
  deeper: [http-caching-semantics-validator-lost-update-01]
---

## Ask

A page listing a customer's own invoices is served with `Cache-Control: no-cache`. A customer on
a corporate network reports seeing a different customer's invoices. Nothing in the application
logs looks unusual. What does that header actually ask for, and what should the response have
said instead?

## Tests

Whether the candidate knows that `no-cache` permits storage, and can pick the directive that
matches the intention rather than the one whose name sounds right.

## Ideal minimal answer

`no-cache` does not mean do not cache. It allows a cache to keep the response and requires it to
check back with the server before reusing it. Nothing in it says the response belongs to one
person, so a shared cache on the way may hold one copy and hand it to someone else. Send
`no-store`, or at least `private`.

## Listen for

- `no-cache` permits storing; what it forbids is reuse without going back to the origin first
- `no-store` is the directive that says do not keep it anywhere
- `private` tells a shared cache it belongs to one user while still letting the browser keep it
- What a cache reuses is decided by the address, plus whatever the response said the answer
  varies on; the session cookie is not part of that unless you say so
- Names the shared cache in the path — a corporate proxy, a content network, a reverse proxy in
  front of the app — as the thing that can hold one copy for many people
- Wants to see the actual response headers and reproduce it through a proxy rather than guess

## Expected knowledge

- A cache can sit between the browser and the server and be owned by neither
- What identifies a stored response is the address it was fetched from, unless the response says
  otherwise

## Strong signals

- Asks what else in the path stores responses — a content network, a reverse proxy, the
  framework's own
- Notices the application logs would show nothing, because the request never reached the
  application
- Says the same directive in a request means something different from the same directive in a
  response
- Asks whether the page should have been at a per-customer address at all

## Weak signals

- Treats `no-cache` and `no-store` as the same thing
- Adds every directive at once and cannot say what each contributes
- Blames the browser or the customer's network
- Says "add a random query parameter"

## Answer bands

### weak

- Reads `no-cache` as "do not cache" and cannot explain the report.
- Suggests clearing the browser cache.

### junior

- Says `no-cache` still allows the response to be kept, and that it only forces a check before
  reuse.
- Names `no-store`, or `private`, as what should have been sent, and says which one and why.

### mid

- Distinguishes what a shared cache may do from what the browser may do, and picks accordingly.
- Says the address alone decides what gets reused unless the response declares what changes the
  answer.
- Points at the proxy as the place to reproduce it, and notes that the server's logs will not
  show it.

## Follow-ups

- The same response also sets a session cookie. Does that change what a cache in the middle is
  allowed to do with it?
  probes: whether they know a cookie-carried session is invisible to the caching rules, unlike
  the header form of credentials
- The team changes it so the cache has to check with the server before every reuse. Is the
  problem gone?
  probes: that storing is the exposure, and that a check can pass on a validator which is not
  per-user
- The same page comes back in English or in German depending on what the reader's client asks
  for. What has to be true for a cache in the middle to get that right?
  probes: declaring which request headers change the answer

## Sources

- https://www.rfc-editor.org/rfc/rfc9111.html#section-5.2.2.4
- https://www.rfc-editor.org/rfc/rfc9111.html#section-5.2.2.5
- https://www.rfc-editor.org/rfc/rfc9111.html#section-5.2.2.7
- https://www.rfc-editor.org/rfc/rfc9111.html#section-3.5
- https://www.rfc-editor.org/rfc/rfc9110.html#section-12.5.5

## Notes

The wording, verified against RFC 9111. `no-cache` (§5.2.2.4): the response "MUST NOT be used to
satisfy any other request without forwarding it for validation" — storage is allowed, reuse
without revalidation is not. `no-store` (§5.2.2.5): "a cache MUST NOT store any part of either
the immediate request or the response". `private` (§5.2.2.7): "a shared cache MUST NOT store the
response (i.e., the response is intended for a single user)".

The detail that makes this a real incident rather than a quiz: §3.5 restricts what a shared cache
may do with a response to a request carrying an `Authorization` header field. It says nothing
about a session cookie. A cookie-authenticated page is, as far as any intermediary is concerned,
just a page at an address — so unless the response says `private` or `no-store`, or declares what
the answer varies on, one stored copy can legitimately serve everybody. This is the argument to
have ready if a candidate insists that revalidation alone would have saved them.

Figures to release if asked: the page is at `/invoices` for every customer, the session is a
cookie, and the customer's employer runs a caching proxy for all outbound traffic.
