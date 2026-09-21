---
id: database-choosing-a-store-second-cluster-for-six-people-01
schema_version: 2
title: A second cluster for a team of six
category: database
topic: choosing-a-store
level: lead
tags: [operations, ownership, scalability]
time_estimate_min: 10
order: 370
---

## Ask

Your team of six runs one PostgreSQL database on RDS. An engineer proposes adding ClickHouse for
a new reporting feature, self-hosted on three machines because the managed offering "costs too
much". The feature is worth real revenue. You are the one who decides. What do you decide, and
what do you need to know before you decide it?

## Tests

Whether the candidate prices a new store in team capacity, on-call surface and long-term
ownership, and can state what evidence would settle the question either way.

## Ideal minimal answer

Decide either way, but price the self-hosted option as recurring work — upgrades, capacity,
being woken by it — against the fee called too expensive, ask what the reporting queries do on
the existing PostgreSQL instance today, and give the decision an owner and a measured condition
that reopens it.

## Listen for

- Asks what the reporting queries actually are, and whether the existing database serves them at
  today's volume — answered with a measurement, not an opinion
- Lists what the self-hosted option adds permanently: upgrades, patching, capacity, watching it,
  and a second thing that can wake somebody at 3am
- Notices six people would now carry something none of them has run before
- Sets the fee for the hosted offering against the loaded cost of the engineering time it
  replaces, not against zero
- Asks who the second and third people able to run it are, and what happens when the proposer is
  away or leaves
- Looks for a cheaper first step — a copy on the existing database, a rolled-up summary, a paid
  trial — with a stated bar the step has to clear
- Says under what measured condition the decision gets reopened
- Neither approves because it is fashionable nor refuses because it is new

## Expected knowledge

- Running a stateful cluster yourself is a standing obligation, not a one-off installation
- A saved copy of the data counts for nothing until somebody has put it back

## Strong signals

- Asks whether the new store would hold anything that could not be regenerated from the existing
  one, and lets the answer set how careful they have to be with it
- Answers the proposer's actual frustration rather than only the proposal
- Names what the team will stop doing to pay for this

## Weak signals

- Approves it as the right tool for the job and moves on
- Refuses it because the team should keep things simple
- Compares only the monthly bill of the two options
- Decides without asking what the reporting queries are

## Answer bands

### weak

- Approves it because it is the right tool for the job.
- Refuses it because the team should stay simple, with nothing measured.
- Compares the two price tags and stops there.

### mid

- Asks what the reporting queries are and whether the current database can serve them today.
- Names installation and upkeep of a new cluster as work the team is taking on.
- Asks whether paying for the hosted offering removes most of that work.

### senior

- Prices the self-hosted option as recurring work — upgrades, capacity, watching it, being woken
  by it — and sets that against the fee that was called too expensive.
- Asks how many people besides the proposer could run it during a holiday or after a departure.
- Proposes a smaller step first and states the result that would justify the larger one.
- Asks whether the new store would hold anything not regenerable from the one they already have.

### lead

- Gives a decision and the measured condition under which it gets reopened, with a figure
  attached.
- Says who owns the thing afterwards and what the team drops to make room for it.
- Treats the proposer's motivation as evidence about the current database and responds to it,
  instead of overruling it.
- Distinguishes a store holding only derived data, which can be rebuilt, from one holding the
  authoritative copy, and lets that set how much rigour the new store needs.

## Follow-ups

- The engineer says they will look after it and it is barely any work. Six months later they take
  a job elsewhere. Walk me through that week.
  probes: bus factor, and whether ownership was ever shared or just assumed
- Everything the new store would hold can be regenerated from the main database in about four
  hours. Does that change how careful you have to be with it?
  probes: derived data versus the authoritative copy, and how that moves the operational bar
- The hosted offering costs about what one engineer costs for two weeks a year. Does that settle
  it?
  probes: whether they compare a fee with the loaded cost of the time it replaces, and whether
  price alone is allowed to decide
- Sales has already promised this feature to a customer for next quarter. Does that change the
  decision, or only the schedule?
  probes: whether a commitment made elsewhere is permitted to choose the architecture

## Notes

Figures to release when asked, and credit the candidate who asks: the PostgreSQL instance holds
about 900 GB and sits at 35 percent CPU; the reporting queries are six dashboards over roughly 18
months of order lines, currently taking 40 to 90 seconds; two of the six engineers are on call;
the hosted offering was quoted at roughly the cost of two weeks of one engineer per year, and
three self-hosted machines at about a third of that in infrastructure.

Both answers can be right. What is being marked is whether the decision is made against those
figures, whether the recurring cost of running it is counted at all, and whether a name is
attached to the result. A candidate who lands on "managed, not self-hosted, after a two-week
trial against these dashboards" has answered well; so has one who lands on "not yet, here is the
number that changes my mind".

## Sources

- https://clickhouse.com/docs/en/guides/sizing-and-hardware-recommendations
