---
id: general-trade-offs-ship-the-shortcut-01
schema_version: 2
title: Hit the date with a shortcut, or miss it by three weeks
category: general
topic: trade-offs
level: lead
tags: [technical-debt, operations, collaboration]
time_estimate_min: 8
order: 210
links:
  related: [database-schema-design-soft-delete-policy-01]
---

## Ask

Your team can hit the launch date by hard-coding something you know will have to be pulled apart
again within six months, or miss the date by three weeks and build it properly. The date has
been announced to customers. What do you do, and what do you say to whom?

## Tests

Whether the candidate can make a shortcut a deliberate, priced and visible decision instead of
either refusing on principle or agreeing in silence.

## Ideal minimal answer

Puts the choice to whoever owns the date as a trade between hitting it and a named future cost,
rather than deciding alone. Says what would make them refuse outright — money, or data written
in a shape that cannot be taken back — keeps the shortcut behind one boundary, and gives the
repayment an owner and a slot.

## Listen for

- Asks what the date is actually made of: a contract, a conference, a marketing email, a guess
- Asks what breaks if the shortcut ships — is it ugly, or is it a correctness or safety risk
- Looks for a third shape: a smaller launch, fewer customers on day one, a manual process behind
  the scenes
- Says the choice belongs to the business, but only once the business has been told the price in
  terms it understands
- Makes the repayment concrete: what, by when, on whose backlog — not "we'll clean it up later"
- Considers who carries the shortcut afterwards, and whether it will be the same people

## Strong signals

- Distinguishes the debt they can live with from the kind that is hard to unwind — data written
  in the wrong shape, an interface customers start depending on
- Writes the decision down where the next person will find it, with the reason, not just the code
- Says what evidence would make them refuse outright rather than trade

## Weak signals

- Always build it properly, with no reference to what the date is worth
- Always ship it, and assumes the cleanup will happen because everyone agrees it should
- Takes the decision alone and does not tell anyone what was traded away
- Calls the shortcut temporary with no date attached

## Answer bands

### mid

- Explains the choice to their manager and asks for a decision.
- Suggests the shortcut with a ticket raised to fix it afterwards.
- Names one or two concrete risks of shipping as it is.

### senior

- Asks what the date is protecting, and looks for a smaller version that protects the same thing.
- Separates cosmetic debt from the kind that leaks into data or into a public surface.
- States the price of the shortcut in time and risk, and puts the decision in front of the person
  who owns the date.
- Gives the repayment an owner and a slot, not an intention.

### lead

- Frames it for the business as a trade between a date and a known future cost, and lets them
  choose with that in hand.
- Names the conditions under which they would refuse — customer data, money, something that
  cannot be taken back.
- Contains the shortcut so it lives behind one boundary and can be removed without touching
  everything.
- Says how the team will be protected from carrying it forever, and what they will drop to pay
  it back.

## Follow-ups

- Six months later the work has not been undone and the team says there was never room. What was
  wrong with your plan?
  probes: whether they ever secured the capacity, or only the promise
- The shortcut means a handful of values are typed into the code and an operator has to redeploy
  to change them. How much does that worry you?
  probes: whether they can grade the severity of debt rather than treat it all alike
- Your most senior engineer refuses to write it and says it is unprofessional. What do you do?
  probes: handling disagreement about a decision that is not theirs, without steamrolling it
