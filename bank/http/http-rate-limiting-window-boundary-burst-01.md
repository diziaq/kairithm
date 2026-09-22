---
id: http-rate-limiting-window-boundary-burst-01
schema_version: 2
title: A hundred a minute, two hundred in three seconds
category: http
topic: rate-limiting
level: mid
tags: [api-design, failure-modes, performance]
time_estimate_min: 8
order: 120
links:
  deeper: [http-rate-limiting-counter-per-instance-01]
---

## Ask

Your API allows a partner 100 requests a minute, counted per clock minute. One partner sent 100
at 11:59:58 and another 100 at 12:00:01. Your service saw 200 requests in three seconds and fell
over. Operations wants the allowance cut to 50. What do you tell them?

## Tests

Whether the candidate can separate how fast a caller may go from how much they may do at once,
and see that the failure is in where the count resets rather than in its size.

## Ideal minimal answer

Counting into a fixed clock window lets a caller spend a whole allowance at the end of one and a
whole allowance at the start of the next, so the peak is twice the number no matter which number
you pick — halving it halves the peak and the sustained rate together. Count over a window that
moves with the request, or hand allowance out continuously.

## Listen for

- The problem is where the window resets, not how big it is; lowering the number lowers both the
  burst and the legitimate throughput
- Spells out the boundary case: a full allowance at the end and a full allowance at the start,
  twice the nominal rate across the join
- Describes a count taken over the trailing period rather than one that resets on the clock
- Describes handing out allowance continuously and letting a caller accumulate a little, so how
  fast and how much at once become two separate numbers
- Says what the API returns when it refuses, and that the refusal should tell the caller when to
  come back
- Notices the storage difference: one integer per window, against keeping timestamps or a
  running estimate

## Expected knowledge

- A refusal carries a status the caller can act on, and a field saying how long to wait
- The service protects itself from what arrives per second, not per minute

## Strong signals

- Asks what the backend can actually absorb in a second, and sets the burst from that rather
  than from a round number
- Offers the smoothed approximation — weighting the previous window by how far into the current
  one you are — as a cheap middle ground, and says what it gets wrong
- Points out the partner is almost certainly looping with no pacing, and asks whether the client
  can be fixed as well as the server
- Distinguishes protecting the service from enforcing a commercial quota, because the two want
  different behaviour at the boundary

## Weak signals

- Lowers the number
- Proposes the same fixed window over a shorter period and thinks the boundary is gone
- Closes the connection or returns a 500 rather than a refusal the caller can act on
- Describes the scheme purely in terms of a library or product name
- Describes all three schemes with fair trade-offs and will not say which one to ship

## Answer bands

### weak

- Agrees with cutting the allowance.
- Cannot say why 100 a minute permitted 200 in three seconds.

### junior

- Explains the boundary: the counter resets and the caller starts again immediately.
- Says a smaller number would not remove the effect.

### mid

- Describes at least one scheme that does not reset on the clock, and how it counts.
- Separates the sustained rate from the maximum burst as two settings.
- Says what the caller receives on a refusal, once asked what a turned-away partner does next.

### senior

- Sets the burst from what the service can absorb, with a figure.
- Weighs the schemes against each other on memory, accuracy at the boundary, and what they cost
  per request.
- Brings up unasked what the caller does with a refusal, and what happens if it ignores it.

## Follow-ups

- The partner is turned away and comes straight back, in a loop, a thousand times a second. Now
  what?
  probes: whether a refusal is cheap, whether the caller honours what it was told, and what you
  do when it does not
- One of your callers is a batch that legitimately needs to send a thousand rows once an hour.
  Does your scheme serve it?
  probes: burst as a deliberate parameter, or a separate path for bulk work
- Two of your endpoints cost a millisecond and one costs four seconds. Is one number enough?
  probes: weighting by cost rather than counting requests

## Sources

- https://www.rfc-editor.org/rfc/rfc6585.html#section-4
- https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3
- https://www.rfc-editor.org/rfc/rfc2697.html
- https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-ratelimit-headers

## Notes

Figures to release if asked: 100 requests a minute per key, 40 partners, the service saturates at
about 150 requests a second, a refusal costs roughly 0.2 ms to produce, and the partner's job
runs hourly and sends everything as fast as it can.

The three schemes, plainly: a fixed window is one counter reset on the clock and admits up to
twice the limit across a boundary; a sliding window counts over the trailing period, either
exactly by keeping timestamps or approximately by weighting the previous window's count; a token
bucket refills continuously at the rate and caps at the bucket size, which makes the burst an
explicit, separately chosen number. RFC 2697's committed information rate and committed burst
size are the same two parameters under other names, and are a useful thing to point at when a
candidate insists one number is enough.

The status code is defined in RFC 6585 §4, which says a 429 "MAY include a Retry-After header
indicating how long to wait" and that responses with it "MUST NOT be stored by a cache". The
`RateLimit` and `RateLimit-Policy` header fields are still an IETF draft, not a published RFC —
do not let a card or an interviewer present them as a standard.
