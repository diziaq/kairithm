---
title: Where does Kafka guarantee order, and where does it not?
difficulty: 2
tags: [kafka, ordering, partitioning]
time_minutes: 4
order: 10
---

## Ask

A colleague says Kafka keeps messages in order. Is that true? Say where it holds and where it does
not.

## Look for

- Order holds inside one partition, not across a topic
- The key decides the partition, so the key decides what is ordered together
- Adding partitions moves keys, so order across the change is not kept
- Retries with more than one in-flight request can reorder unless idempotence is on

## Red flags

- Claims order across the whole topic
- Thinks a timestamp restores order
- Never mentions the key

## Follow-ups

- Two events for one customer must stay ordered. What is your key?
- What breaks if that customer produces far more traffic than any other?
