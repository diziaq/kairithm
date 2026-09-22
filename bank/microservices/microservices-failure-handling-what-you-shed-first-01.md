---
id: microservices-failure-handling-what-you-shed-first-01
schema_version: 2
title: Sixty per cent of the traffic, and it is 11:40 on Black Friday
category: microservices
topic: failure-handling
level: lead
tags: [failure-modes, operations, ownership, capacity]
time_estimate_min: 11
order: 610
links:
  shallower: [microservices-failure-handling-cascade-slow-dependency-01]
  related: [microservices-scalability-one-tenant-dominates-01]
---

## Ask

Black Friday, 11:40. The database behind everything is at its limit and you can serve about sixty
per cent of the traffic; the rest has to be turned away. Behind that one database sit checkout,
browse, search, order history, partner webhooks and finance's nightly export. What goes first,
and who hears it from you?

## Tests

Whether the candidate will choose whose requests are refused, say what the refusal is based on,
and name the people told before and during it — rather than describing a mechanism and stopping.

## Ideal minimal answer

Checkout and payment callbacks are last; the export, order history and recommendations go first,
and browse and search degrade to cached answers before they are refused. The rule is what the
request is worth against what it costs, decided now and enforced at the edge so a refusal costs
nothing. Partners under contract, support and finance are told by me, not by their monitoring.

## Listen for

- Actually picks an order and says what each class is being traded for — not "we would shed
  non-critical traffic"
- Puts the revenue path last: a shopper mid-checkout and the payment provider's callbacks
- Sees that the export and the reports can be deferred rather than lost, and says when they run
  instead
- Degrades before refusing where there is a cheaper answer: cached or stale browse and search
  results beat an error
- Refuses at the edge, cheaply, before the request has spent any of the database it is trying to
  protect
- Says what the refused client actually receives and what it should do — a refusal it can act on,
  with a wait, and not one that invites an immediate repeat
- Names the people told: partners with a contract, support and the account team, finance for the
  export, a status page for everyone else
- Notices the classification should have been agreed before today, and says who signs it off
- Knows that a shed request which comes straight back as a repeat has not been shed at all

## Expected knowledge

- Turning work away is a legitimate response when the alternative is failing everyone
- A refusal has to be cheaper to serve than the work it replaces, or it makes things worse
- Not every request is worth the same to the business, and somebody outside engineering owns that
  ranking

## Strong signals

- Asks what fraction of checkouts start at search before deciding search is expendable
- Separates the traffic that earns money today from the traffic that is contractually promised,
  and says which wins at 11:41
- Says what the export being late costs and to whom, rather than treating anything internal as
  free to drop
- Has a view on who is allowed to make this call at 11:40 without waking anyone, and what gets
  escalated
- Writes down what was refused so the numbers can be reconciled afterwards

## Weak signals

- Describes a mechanism for refusing traffic and never says which traffic
- Refuses by customer rather than by what the request is for, without noticing the difference
- Drops the largest source of traffic because it is the largest
- Turns off everything internal first on the grounds that no customer sees it
- Lists three plans with fair trade-offs and will not commit to one
- Tells the story of last year's Black Friday without deciding anything about this one

## Answer bands

### mid

- Names a sensible first thing to drop, usually the internal one, and protects checkout.
- Can describe a way to turn traffic away once asked how it would be enforced.
- Does not say what the refused caller sees, and does not mention telling anyone.

### senior

- Orders the whole list unprompted and gives the reason for each position rather than one rule.
- Chooses degrading over refusing where a cheaper answer exists, and says what the shopper sees.
- Puts the refusal where it costs nothing, and explains why refusing deep in the stack would not
  have helped.
- Raises that refusals must not invite immediate repeats, and says how the client is told to wait.

### lead

- Commits to an order under the constraints given, including the case where a contractual
  obligation and the revenue path are in conflict, and says which loses.
- Names each group told, by whom and when — partners, support, finance, the status page — and
  does not leave it to their monitoring.
- Says who is authorised to make the call in the moment and what has to be escalated instead.
- Turns it into something agreed in advance: classes of traffic, an owner per class, and the
  conversation with the commercial side that has to happen before next November.
- Accounts for the aftermath: what was refused, who is owed an explanation, and what is
  reconciled.

## Follow-ups

- You stop the export and finance cannot close the day. Whose call was that?
  probes: whether the decision has a named owner, and whether it was socialised before the day
- Partner traffic is under a contract with penalties. Consumer checkout is the money. Which do
  you turn away at 11:41?
  probes: forcing a choice between a promise and revenue, out loud
- Everything you turn away comes straight back, because every client repeats on failure. What now?
  probes: refusals must be cheap and must discourage the immediate repeat
- You want this to be a switch next year rather than an argument. What has to be written down,
  and who signs it?
  probes: agreed classes with owners, and what customers were actually promised

## Sources

- https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/
- https://sre.google/sre-book/handling-overload/
- https://www.rfc-editor.org/rfc/rfc6585#section-4

## Notes

Figures to release when asked: browse is half the traffic and search a fifth; a quarter of
completed checkouts begin at search; order history is under a tenth and drives support calls;
partner webhooks are 2% of traffic and sit under a 99.5% contract with penalties; the export
feeds finance's daily close and can run at 03:00 instead.

The card is failed by a candidate who describes a shedding mechanism beautifully and never ranks
the six things in front of them. It is passed by one who ranks them, and cleared at lead by one
who also names the humans told and the pre-agreed version of the decision.
