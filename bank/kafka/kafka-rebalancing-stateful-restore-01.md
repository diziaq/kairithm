---
id: kafka-rebalancing-stateful-restore-01
schema_version: 1
title: Every rebalance costs twenty minutes of rebuild
category: kafka
topic: rebalancing
level: lead
tags: [operations, performance, consistency]
time_estimate_min: 12
order: 84
links:
  related: [sap-jco-performance-nightly-bulk-extract-01]
---

## Ask

A stateful application keeps a running window per customer in local storage on each instance.
Every rebalance, whichever instance is given a moved partition spends twenty minutes rebuilding
before it emits anything, and the business sees a twenty-minute hole in its dashboards. You own
this. What do you change?

## Tests

Whether the candidate can separate the cost of work moving from the cost of making moved work
useful again, and choose between reducing movement, speeding recovery and changing what is
promised during recovery.

## Listen for

- Separates the two costs: work moving at all, and what it takes to make moved work productive
- Names ways to stop routine restarts moving anything — giving an instance an identity that
  outlives the process, so a brief absence is tolerated
- Names ways to make recovery cheap: a warm copy held on another instance, or replaying a
  compacted record of the state instead of recomputing it from the source
- Asks what the twenty minutes is actually spent doing, and whether it is reading or calculating
- Asks how often a rebalance genuinely happens, before optimising the wrong half

## Expected knowledge

- Local data belonging to a partition has to be rebuilt wherever that partition ends up
- A member that returns quickly can be given its own work back if the group is told to wait for it

## Strong signals

- Asks what the hole in the dashboard costs, and whether stale numbers for twenty minutes beat no
  numbers
- Asks whether instances are pinned to storage that survives a restart
- Treats a planned deploy and a crash as two events deserving different handling

## Weak signals

- Proposes fewer partitions as the only lever
- Treats the rebuild as fixed and unavoidable
- Cannot say what should happen if the instance came back within ten seconds

## Answer bands

### mid

- Connects the hole to a partition being handled somewhere with no local data for it.
- Suggests restarting less often, or keeping the storage attached to the instance.

### senior

- Separates stopping the movement from making the recovery cheap, and offers an option for each.
- Asks what the twenty minutes consists of before choosing anything.
- Says what a warm copy held elsewhere would cost in memory and in extra write traffic.

### lead

- Picks an approach from how often the event happens and what the hole is worth, and names the
  figures they would need first.
- Decides what the dashboard shows during a rebuild rather than leaving it blank.
- Names the failure their chosen approach makes worse, and who would notice it first.

## Follow-ups

- The instance that crashed is back in eight seconds. Should its work have moved at all?
  probes: holding partitions for a returning member instead of handing them out immediately
- The team proposes keeping a second copy of every window on another instance. What does that cost
  you?
  probes: memory, network and the extra write path, and whether they price it
- Finance tells you a stale number is worse than no number. Does your plan survive that?
  probes: whether they see the behaviour during recovery as theirs to choose

## Sources

- https://cwiki.apache.org/confluence/display/KAFKA/KIP-345%3A+Introduce+static+membership+protocol+to+reduce+consumer+rebalances
- https://kafka.apache.org/documentation/streams/architecture
- https://kafka.apache.org/documentation/#compaction
