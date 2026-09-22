---
id: http-protocol-choice-latency-floor-sydney-01
schema_version: 2
title: A hundred and fifty milliseconds to Sydney
category: http
topic: protocol-choice
level: senior
tags: [performance, api-design, scalability]
time_estimate_min: 10
order: 155
links:
  deeper: [http-protocol-choice-live-prices-transport-01]
  related: [general-requirements-instant-and-always-current-01]
---

## Ask

Product wants the ninety-fifth percentile under 150 ms for the Sydney office. The service runs
only in Frankfurt. One proposal on the table is a larger instance type; another is switching the
API to HTTP/3. The page currently makes four calls, each waiting for the one before it. What do
you tell product?

## Tests

Whether the candidate reaches for arithmetic before optimisation, and can tell a stakeholder a
target is unreachable while still offering the levers that exist.

## Ideal minimal answer

Sydney to Frankfurt is about 16,500 km, and light in fibre covers roughly 200 km per
millisecond, so one round trip cannot come in under about 165 ms before any server work at all —
and the page spends four of them one after another. Neither proposal reaches 150 ms. Cut the
sequential trips and put something near Sydney.

## Listen for

- Does the arithmetic out loud: distance, speed of light in glass, a floor on the round trip
- Concludes the target is unreachable from Frankfurt whatever happens on the server, and says so
  plainly rather than hedging
- Counts what the page actually spends, and separates the trips that must be sequential from the
  ones that could go together
- Separates the first visit — name lookup, connection, handshake — from the steady state on a
  connection already open
- Says what a newer protocol actually buys: fewer setup trips, no stall behind one lost packet.
  It does not shorten the path
- Names the levers that exist: serve from the region, cache nearer the user, collapse four calls
  into one, do the work before the user asks
- Asks where the 150 ms came from and what it is measured against

## Expected knowledge

- A round trip has a floor set by distance and the speed of light in fibre
- Opening a connection costs round trips before the first request is even sent

## Strong signals

- Points out a warm connection removes the setup trips entirely, so the first page load and the
  tenth are two different problems with two different answers
- Notices that four sequential calls is a decision somebody made, and asks why they cannot be
  issued together — the cheapest three-quarters of the fix
- Asks what actually has to be in Sydney: reads may be servable from a replica or a cache while
  writes stay where they are
- Brings it back to what the user is waiting for, and asks whether the office would accept a
  page that paints in stages

## Weak signals

- Agrees to the larger instance
- Offers the protocol change as the fix
- Says "put a content network in front of it" without saying what is cacheable
- Argues about whether it is 160 or 170 ms instead of noticing it is over the target either way
- Promises to try and report back

## Answer bands

### mid

- Says distance is the dominant cost and that a bigger machine will not help.
- Suggests serving from somewhere closer.

### senior

- Produces the floor with a figure and a method, not just an assertion.
- Counts the sequential trips and multiplies.
- Says exactly what a protocol change buys and what it cannot buy.
- Gives product a number that is achievable, rather than only rejecting theirs.

### lead

- Reframes the requirement: what the office actually needs, against what was written down.
- Prices each real lever — a regional deployment, an edge cache, fewer calls — and recommends an
  order.
- Names what the business gives up under each, including consistency across regions.

## Follow-ups

- Give me a number. What is the best you could do for that office without moving anything?
  probes: whether they will commit to arithmetic, and separate a warm connection from a cold one
- Half the page is identical for everyone in that office. Does that change what you promise?
  probes: what is cacheable, where it lives, and how stale it may be
- You put a read copy in Sydney and writes still go to Frankfurt. What does the user see in the
  second after they save something?
  probes: reading your own write across a long link
- The four calls become one. How much did you actually buy?
  probes: three round trips is most of the win, and it is a change to the API rather than to
  infrastructure

## Sources

- https://www.rfc-editor.org/rfc/rfc8446.html#section-2
- https://www.rfc-editor.org/rfc/rfc9000.html#section-7
- https://www.rfc-editor.org/rfc/rfc9114.html
- https://www.itu.int/rec/T-REC-G.652

## Notes

The arithmetic, to hold a candidate to. Sydney to Frankfurt is about 16,500 km great circle.
Single-mode fibre has a group index around 1.47, so light travels roughly 204,000 km/s in it —
call it 200 km per millisecond. That gives about 82 ms one way and 165 ms for a round trip on a
perfectly straight path. Real submarine routes are considerably longer than the great circle, so
measured round trips between those two cities run well over 200 ms. Either figure is over the
target; a candidate arguing about which one has missed the point.

Cold start costs round trips before the request: a name lookup, then the transport handshake,
then the encryption handshake — three, with TLS 1.3 over TCP. QUIC folds the transport and
encryption handshakes together, so HTTP/3 saves one of them, and a resumed connection can save
another. That is the whole of what the protocol proposal buys: one or two round trips on the
first visit, and nothing at all on a warm connection.

Four sequential calls at ~250 ms each is about a second, and is the largest single item on the
page. Making them concurrent, or collapsing them into one endpoint, is worth more than
everything else on the list and does not require any infrastructure. A candidate who never
counts the four has not answered.
