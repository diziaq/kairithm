---
id: microservices-scalability-shard-key-dominant-tenant-01
schema_version: 2
title: Hash the order id, or the tenant id, with a tenant at forty per cent
category: microservices
topic: scalability
level: lead
tags: [capacity, performance, correctness, operations]
time_estimate_min: 11
order: 625
links:
  related:
    [microservices-scalability-one-tenant-dominates-01, kafka-partitioning-hot-partition-01]
---

## Ask

You are splitting the orders store across eight databases before it doubles again. One engineer
wants to spread rows by hashing the order id; another wants to hash the tenant id. Almost every
query filters by tenant, and your largest tenant is forty per cent of the rows. Which, and what
does it cost you?

## Tests

Whether the candidate can name the trade between keeping a tenant's data together and spreading
load evenly, and notices that a tenant at forty per cent breaks both proposals as stated.

## Ideal minimal answer

Tenant id keeps a tenant's rows in one place so a normal query hits one database, but forty per
cent of the rows land on one of the eight. Order id spreads them evenly and turns every tenant
query into a fan-out across all eight. So neither unaltered: the big tenant is split by a second
key or given its own database, and the routing knows which tenants are which.

## Listen for

- States the trade in one sentence: one key keeps the data that is queried together on one
  machine, the other spreads the rows without regard to who asks for them
- Works out what each choice does here — one database holding 40% of the rows and 40% of the load,
  or every tenant-scoped query touching all eight and merging
- Says that with a tenant this size neither proposal works as it stands, rather than picking the
  lesser evil and stopping
- Proposes a composite arrangement: tenant id for ordinary tenants, tenant plus a second
  component for the large ones, with routing that knows which is which
- Or isolates the large tenant on its own database and accepts that the routing has an exception
  in it
- Asks which queries must stay cheap before choosing: per-tenant reads, cross-tenant reporting,
  joins, uniqueness within a tenant
- Notices that a fan-out query is limited by the slowest of the eight and by the merge, not by
  the average
- Treats the choice as close to irreversible and asks what the path to sixteen databases looks
  like, so the mapping is not the row's hash against the number of machines
- Asks what the forty per cent tenant does over the next year, and whether a second tenant is
  heading the same way

## Expected knowledge

- A query that cannot be narrowed to one database has to be sent to all of them and the answers
  combined
- Rows that are always read together are cheapest when they sit together
- Changing how rows are distributed after the fact means moving data while the system runs

## Strong signals

- Asks for the query mix — how much traffic is per-tenant versus cross-tenant — before choosing
- Separates hot from full: the big tenant's shard may hit disk before it hits CPU, or the reverse,
  and the remedies differ
- Points out that a second key inside the large tenant costs its own queries a fan-out, and says
  which of that tenant's queries would suffer
- Plans the move to more databases from the start — many logical groups mapped onto few machines —
  rather than tying the arrangement to the number eight
- Says what has to be given up in writing: the query that will never be cheap again

## Weak signals

- Picks the tenant id because co-locating a tenant is the standard advice, with no mention of the
  forty per cent
- Picks the order id because it spreads evenly, and does not price the fan-out
- Proposes adding read replicas of the hot shard as the answer to a write and storage problem
- Suggests sharding on a hash of both keys together without saying what a tenant query then does
- Lists the options with correct trade-offs and will not choose
- Says it depends on the workload and does not ask a single question about the workload

## Answer bands

### mid

- Explains that hashing the tenant keeps a tenant together and hashing the order spreads rows.
- Identifies that one database would carry the big tenant, once prompted with the figure.
- Chooses one of the two and does not question whether either works as given.

### senior

- Prices both against the stated query pattern without being led there, including what a fan-out
  costs and which query it hurts.
- Says the forty per cent tenant makes the simple version of either choice unworkable.
- Proposes splitting that tenant further, or isolating it, and describes what the routing has to
  know.
- Asks what has to stay cheap and what the team is willing to give up.

### lead

- Commits to a design under the constraints given, names the queries it makes slower, and says who
  is told those queries are now slower.
- Plans for the arrangement changing: a level of indirection between a row and a machine, and what
  moving data while live involves.
- Decides whether the largest tenant should be on its own hardware as a commercial and operational
  decision, not only a technical one, and says who owns it.
- Handles the general case — the second and third large tenants — instead of special-casing one.

## Follow-ups

- You go with the tenant. Six months on, that one database is at eighty per cent of its disk and
  the others are at twenty. What do you do that week?
  probes: isolating one tenant, and whether the routing can carry an exception
- Finance reads every tenant at once for the monthly numbers. Which choice hurts them, and how
  much?
  probes: cross-tenant reads, the merge cost, and whether a separate store is the honest answer
- Two years on you need sixteen databases rather than eight. How much of the data moves under each
  proposal?
  probes: mapping rows to machines through something that can be repointed, versus a hash of eight
- Your second-largest tenant grows to thirty per cent as well. Does your answer survive?
  probes: designing for the pattern rather than for this one customer

## Sources

- https://docs.citusdata.com/en/stable/sharding/data_modeling.html
- https://docs.citusdata.com/en/stable/develop/api_udf.html
- https://vitess.io/docs/reference/features/vindexes/

## Notes

The card is not asking which key is right. It is asking whether the candidate spots that a tenant
at forty per cent makes both proposals wrong on their own terms, and then designs something that
treats large tenants differently from small ones. Citus ships a function for exactly this
(isolating one tenant onto its own shard), which is worth knowing about but is not the point —
the point is noticing that a uniform rule cannot hold.

Figures to release when asked: 92% of queries filter to one tenant; the monthly finance report
reads all of them; the largest tenant is 40% of rows and growing faster than the rest; the second
largest is 9%; eight databases today, sixteen expected within two years.
