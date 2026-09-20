---
id: database-consistency-quorum-dashboard-disagrees-01
schema_version: 1
title: Two panels on one dashboard disagree
category: database
topic: consistency
level: lead
tags: [consistency, correctness, operations, observability]
time_estimate_min: 14
order: 221
links:
  related: [microservices-observability-dashboards-green-users-angry-01]
---

## Ask

A finance dashboard shows a balance in one panel and the payments that make it up in another.
Twice a week they disagree, always by one recent payment. The store keeps three copies; a write
returns as soon as one copy has it, and a read is served by whichever copy answers first. What do
you change, and what do you tell finance?

## Tests

Whether the candidate can reason about how many copies must take part before an answer is
guaranteed current, and still see that two separate reads are not one view of the data whatever
that setting is.

## Listen for

- Works out that a write confirmed by one copy and a read answered by one copy need not share a
  copy, so the read can legitimately be older than the write
- States the condition that removes it — the set read and the set written have to overlap, which
  with three copies means two and two
- Prices it: more copies on the write path is slower and stops working sooner when machines are
  down, and asks whether finance wants to pay that
- Sees the second and separate problem: the two panels are two reads at two moments, so even with
  overlap they can straddle a payment
- Fixes the panel problem where it lives — one read that returns both figures, or a read pinned
  to a single point in time, or a total derived from the list already on the screen
- Asks what the page is for: somebody watching a trend, or somebody signing a number
- Says what to show when the figures may be behind — a timestamp, an "as of", a refresh — rather
  than a confident wrong number

## Expected knowledge

- With three copies, a read consulting two and a write confirmed by two must share at least one
  copy, and that shared copy holds the newest confirmed value
- Overlap guarantees a read sees the newest confirmed value; it does not turn two separate reads
  into one moment in time
- Demanding more copies on either path costs latency and reduces how many machines may be lost
- PostgreSQL offers a quorum on the write side — `synchronous_standby_names = 'ANY 1 (...)'` —
  but has no quorum read; the tunable-both-sides model belongs to Dynamo-style stores

## Strong signals

- Notices that moving the write path from one copy to two changes the failure behaviour and not
  only the speed, and asks what a rolling restart does
- Asks whether any write is ever confirmed and then lost, which is a different and worse problem
  than being late
- Proposes measuring the disagreement continuously instead of waiting for finance to report it
- Says which figures on the page are allowed to be approximate and which are not, and makes the
  page say so
- Asks whether the balance is stored or computed, because the two panels may not even read the
  same thing

## Weak signals

- Recites the three-letter trade-off theorem and stops there
- Sends all reads to one designated copy without saying what happens when it is down
- Puts a cache in front, which makes both panels older
- Treats the two panels as though they were one read
- Promises finance that it will be fixed, with no statement of what is now guaranteed

## Answer bands

### mid

- Says the copy answering the read may not be the copy that took the write.
- Proposes involving more copies, or reading from one fixed place.

### senior

- States the overlap condition and works it out for three copies with real numbers.
- Says what the stricter setting costs in latency and in machines it can afford to lose.
- Separates being behind from the fact that the panels are two reads at two moments.
- Names how the second problem is fixed, and it is not a setting.

### lead

- Decides which figures on that page carry a guarantee and which do not, and gets finance to
  agree in those words.
- Records the guarantee per endpoint where the next team will find it, rather than as one global
  switch.
- Chooses what the page shows while the figures may be behind, and treats that as a product call.
- Commits to measuring the gap, and names the threshold at which somebody is woken up.

## Follow-ups

- You tighten both paths so two copies take part. During a rolling restart one machine is out for
  six minutes. What breaks?
  probes: the availability cost, and whether they thought about the maintenance window
- Both panels are correct at the instant each is served, and they still disagree. Explain that to
  finance.
  probes: two reads at two moments are not one view, whatever the setting says
- Finance say they will accept a figure up to a minute old, provided they know it is. What do you
  build?
  probes: turning a weak guarantee into something the interface states rather than hides
- The same page is used at month end to sign off a statement. Does your answer change?
  probes: guarantees per use rather than per system, and whether they will say no to this job

## Sources

- https://www.postgresql.org/docs/current/warm-standby.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html
- https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf

## Notes

Never let this become a recital of the availability theorem. The card is about arithmetic over
copies and about a user interface that shows two answers from two moments.

Figures to release when asked, and credit the asking:

- Three copies, all in one region. About two payments a second at peak.
- The balance panel reads a stored total; the list panel queries the payment rows. The two panels
  fire two requests, roughly 300 ms apart.
- Disagreements are always one payment and always resolve on refresh.
- Nobody measures how far behind any copy is.

The second panel problem is the better half of the card. Even with read and write sets that
overlap, two requests issued 300 ms apart can fall either side of a write, so no setting removes
it — the fix is one request, or one point in time, or computing the total from the rows being
shown. A candidate who only reaches the arithmetic is senior; a candidate who reaches the second
problem, and then asks finance what the page is for, is the lead answer.

Engine pin: the read-and-write tunables come from Dynamo-style stores; DynamoDB exposes it as
eventually consistent versus strongly consistent reads rather than as numbers. PostgreSQL's
`synchronous_standby_names = 'ANY k (...)'` is a genuine write quorum, but PostgreSQL has no
matching read quorum — a read on a standby is whatever that standby has applied. Do not let a
candidate claim quorum arithmetic for a PostgreSQL replica set without that caveat.
