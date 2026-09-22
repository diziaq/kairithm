---
id: http-pagination-jump-to-page-five-hundred-01
schema_version: 2
title: A total on every page, and jump to page five hundred
category: http
topic: pagination
level: senior
tags: [performance, api-design, scalability]
time_estimate_min: 10
order: 150
---

## Ask

You own a public list endpoint over a table of eighty million rows. Your largest integrator is
asking for two things: an exact total on every page, and the ability to jump straight to page
five hundred. Both are in their renewal conversation. What do you offer them, what do you
refuse, and how do you have that conversation?

## Tests

Whether the candidate can price two requests that look reasonable, offer something that solves
the integrator's actual problem, and say no to the rest with a reason the integrator can act on.

## Ideal minimal answer

Both ask the server to produce rows it will then throw away, and the cost grows with depth
rather than with page size. Offer a cursor that walks forward cheaply and a total that is
approximate or capped instead of exact. Then ask what page five hundred is for — it is usually
an export, which wants a different endpoint entirely.

## Listen for

- Both requests make the server compute rows it discards; the cost is in the depth, not the page
- An exact total is a full scan of the filtered set on every request, and it is out of date the
  moment it is returned
- Offers alternatives rather than a flat no: an estimate, a capped count, a count computed once
  for a query rather than on every page
- Asks what the integrator is actually doing, because a request for page five hundred is almost
  always an export or a search they cannot express
- Offers the shape that fits that: a bulk path, a filter that narrows the set, or a job that
  produces a file
- States what the cursor contract has to promise — opaque, tied to the sort and the filter — and
  what happens when either changes
- Prices the refusal in the integrator's terms: what they have to change and how long they get

## Expected knowledge

- A deep position still computes and discards everything before it
- A carried-forward key can only move relative to a known row, so it cannot land on an arbitrary
  position

## Strong signals

- Insists the cursor token is opaque so the encoding can change later, and that it is rejected
  rather than silently misinterpreted when the sort or filter changes
- Sets a maximum page size and a maximum depth, and returns a clear error past it rather than a
  slow answer
- Separates the count from the list so a caller who does not need it does not pay for it
- Points out what one page-five-hundred request does to everyone else, not just to itself
- Asks whether an estimate from the planner's own statistics would satisfy the real need, and
  says how wrong it can be

## Weak signals

- Agrees to both and proposes an index
- Caches the total with no statement of how stale it is allowed to be
- Offers a cursor without saying what it is bound to
- Says "use a cursor" and stops
- Refuses both without offering anything the integrator can take back to their team
- Prices both requests fairly and never says which one the integrator is actually getting

## Answer bands

### mid

- Explains why a deep position and an exact total are both expensive.
- Proposes a cursor for the list.

### senior

- Offers a specific alternative for each request — a capped or estimated total, a bulk path —
  rather than only refusing.
- States what the cursor is tied to and what invalidates it.
- Puts limits on depth and page size and says what the caller gets when they exceed them.
- Asks what the integrator is really doing before designing anything.

### lead

- Runs the renewal conversation: what is offered, what is not, what it would cost to support,
  and by when.
- Decides what the API promises long term and what it will not be forced into by one customer.
- Weighs the cost of maintaining a second, bulk-shaped path against the cost of not having one.

## Follow-ups

- They tell you their screen has a page-number control and product will not change it.
  probes: whether they can carry the constraint into a design — bounded depth, a capped total —
  instead of capitulating or refusing flatly
- You ship the cursor. Three months later you add a new sort option. What happens to a token
  somebody issued last week?
  probes: the token is bound to the sort and filter; how it is invalidated rather than
  misread
- Someone caches the total for five minutes. Who notices first?
  probes: the total disagreeing with the rows on the page in front of the user
- The integrator's real job turns out to be a nightly copy of everything you have.
  probes: offering a different shape of endpoint, and what it costs to run

## Sources

- https://www.postgresql.org/docs/current/queries-limit.html
- https://www.postgresql.org/docs/current/catalog-pg-class.html
- https://www.postgresql.org/docs/current/using-explain.html

## Notes

Figures to release if asked: eighty million rows, growing by about 200,000 a day; page size 50
by default and 200 maximum; the integrator issues about 4,000 list requests an hour; the filtered
sets they use range from a few hundred rows to twenty million; the renewal is in six weeks.

Both requests are the same problem seen twice: the server must materialise everything ahead of
the answer. A cursor makes the list cheap and removes the ability to jump; an estimate makes the
total cheap and removes exactness. There is no scheme that keeps all four of cheap, exact, deep
and stable, and the card is looking for a candidate who says that plainly and then chooses.

`pg_class.reltuples` gives a planner estimate for a whole table at essentially no cost, and
`EXPLAIN` gives an estimated row count for a filtered query; both are approximations maintained
by analyse, and how wrong they are depends on how recently that ran. Offering one of these is a
strong answer as long as the candidate says it is an estimate and does not present it as a count.

The weakest strong-sounding answer here is "add an index". An index changes how rows are found;
it does not stop the server walking past half a million of them to reach a position.
