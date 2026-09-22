---
id: general-trade-offs-retry-the-payment-01
schema_version: 2
title: Retry the payment call, or let the user press again
category: general
topic: trade-offs
level: mid
tags: [retries, idempotency, failure-modes, correctness]
time_estimate_min: 8
order: 100
links:
  related: [sap-jco-trfc-sm58-backlog-01]
  deeper: [general-trade-offs-window-or-dual-write-01]
---

## Ask

Your call to the payment provider times out about once in a thousand requests. One colleague
wants the service to send it again automatically; another says fail the request and let the
customer press the button a second time. Which side do you take, and what would change your
mind?

## Tests

Whether the candidate reasons about what a repeat does on the other side of a timeout, rather
than choosing between two policies on general principle.

## Ideal minimal answer

Says a timeout leaves the outcome unknown, so the money may already have moved, and that the
customer pressing again is the same repeat. Asks whether the provider will accept a reference
that makes a second attempt harmless, weighs a double charge against a lost sale, and puts
spacing and a cap on the attempts.

## Listen for

- Asks what a timeout actually means here: the request may have been carried out and the answer
  lost
- Asks whether the provider will treat a second attempt as the same payment or as another one
- Asks for a way to name the attempt so the provider can recognise it, and whether the provider
  supports that
- Points out that pressing the button again is the same repeat, just performed by a human with
  less control
- Considers asking the provider for the current state of the payment instead of sending it again
- Sets limits: how many attempts, how far apart, and what happens at the end of them
- Names who eats the damage in each direction — a double charge, or a lost sale

## Strong signals

- Notices that the user pressing the button is not a safety mechanism, because nothing stops them
  pressing it twice either
- Wants the outcome recorded before the call, so that an unknown result is visible afterwards
  rather than lost
- Mentions that a thousand-to-one failure across all requests becomes routine at volume, and
  asks what the volume is

## Weak signals

- Picks a side from general preference, with no reference to what the provider does with a
  repeat
- Assumes a timeout means the operation did not happen
- Adds attempts in a tight loop with no limit
- Says the provider will handle it, without asking how
- Explains what each of the two choices costs and will not take a side

## Answer bands

### weak

- Chooses one of the two options because it sounds safer, with no reasoning about the provider.
- Treats a timed-out call as a call that did not happen.
- Cannot say what damage either choice can cause.

### junior

- Says a repeat might charge the customer twice and worries about it.
- Suggests asking the provider whether the payment went through.
- Wants a limit on how many times it is sent.

### mid

- States that a timeout leaves the outcome unknown, and that both options are repeats.
- Asks whether the provider can be given a reference that makes a second attempt harmless.
- Weighs a double charge against a lost sale and says which the business would rather have.
- Adds spacing and a cap, and says what the customer sees when the attempts run out.

### senior

- Puts the guarantee at the boundary: what the provider promises, what your side records, and
  the window between them.
- Wants the intent written down before the call so an unresolved attempt is discoverable, and
  says what reconciles it later.
- Notes that a policy with no upper bound turns a slow dependency into an outage of your own
  making.
- Says how they would measure whether the decision was right after a month.

## Follow-ups

- The provider tells you that if you send the same reference twice they return the original
  result. Does your answer change?
  probes: whether they can exploit a safe repeat, and whether they ask how long the provider
  remembers it
- Your service crashes after the call goes out but before the answer comes back. What does the
  customer see, and what does your database say?
  probes: recording intent before acting; recovering an unknown outcome
- Marketing says a double charge costs a refund and an apology; a failed checkout costs the
  sale. How does that land in your design?
  probes: whether the cost of the damage sets how much machinery is justified
