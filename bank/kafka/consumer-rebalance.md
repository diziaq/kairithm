---
title: What happens to in-flight work when a consumer group rebalances?
difficulty: 3
tags: [kafka, consumers, delivery]
time_minutes: 5
order: 20
---

## Ask

Your consumer is half way through processing a batch when the group rebalances. What happens to
that work, and what does the next owner of the partition see?

## Look for

- Partitions are revoked, so the batch may finish against a partition the consumer no longer owns
- The next owner starts from the last committed offset, so the work is repeated
- Knows where to do the cleanup: the revoked callback, before the new assignment
- Connects this to why the processing must be idempotent

## Red flags

- Believes a rebalance waits for in-flight work
- Says exactly-once is automatic
- Cannot say what a committed offset means

## Follow-ups

- How does cooperative rebalancing change this answer?
- Where would you commit the offset to make repeats cheap?
