---
id: general-design-reasoning-two-teams-one-table-01
schema_version: 1
title: Another team wants to write to your table directly
category: general
topic: design-reasoning
level: senior
tags: [data-modelling, api-design, consistency, correctness]
time_estimate_min: 8
order: 160
links:
  deeper: [general-design-reasoning-choice-you-cannot-undo-01]
---

## Ask

Two teams need the same piece of data. Your team owns the table it lives in. The other team
wants credentials and to write to that table directly, because going through your service costs
them a network hop and a dependency on your release schedule. What do you propose, and what do
you give up either way?

## Tests

Whether the candidate reasons about who is responsible for keeping the data valid, rather than
about the mechanics of getting access to it.

## Listen for

- Asks what rules the data has to satisfy and where those rules are currently enforced
- Points out that the table is not the contract — the code around it is — and shared access makes
  the table's shape a public interface
- Asks what happens when your team needs to change a column, and who has to be asked
- Considers whether the other team's real need is reading, writing, or being told when something
  changes
- Separates the performance argument from the coupling argument and tests each on its own
- Offers alternatives: an endpoint, a copy they own, an event they subscribe to, moving ownership

## Strong signals

- Asks what the other team's release cadence has to do with correctness, and whether the real
  complaint is that your team is a bottleneck
- Says that with two writers, any rule not enforced by the database itself is now enforced
  nowhere
- Is willing to hand ownership over entirely if it turns out the data belongs to them

## Weak signals

- Refuses on principle without asking what they need
- Agrees because it is faster and the other team is competent
- Proposes a nightly copy with no account of what stale data does to the consumer
- Treats database permissions as the whole of the question

## Answer bands

### weak

- Answers only with yes or no and a rule of thumb.
- Does not ask what the data is for or what makes it valid.
- Assumes two writers is fine as long as both are careful.

### mid

- Asks what the other team actually does with the data.
- Notices that changing the table becomes harder once someone else depends on it.
- Proposes an endpoint or a copy instead, and names the cost of each.

### senior

- Puts the rules that keep the data valid at the centre and asks who will enforce them once
  there are two writers.
- Treats the table shape as an interface the moment it is shared, and says what that costs at the
  next migration.
- Tests the performance argument with a number before accepting it as a reason.
- Offers ownership as a variable, not a given.

### lead

- Recognises the complaint about the release schedule as a delivery problem and addresses that
  separately.
- Picks the option with the lowest ongoing coordination cost between the two teams, and says how
  they would know if it was wrong.
- Writes the agreement down — what is guaranteed, how it is changed, how it is deprecated —
  rather than relying on goodwill.

## Follow-ups

- Six months later your team has to add a field that must never be empty, and the other team's
  writes know nothing about it. How does that go under your proposal?
  probes: whether the chosen shape survives a change of schema, and who has to be asked before
  the change can happen at all
- They agree to go through your service, and now their page takes forty milliseconds longer and
  goes down whenever you deploy. What do you do about that?
  probes: whether they take the coupling they created seriously, and reach for a copy or an
  asynchronous feed
- It turns out they write to it far more often than you do, and your team barely touches it any
  more. Now what?
  probes: willingness to move ownership rather than defend territory
