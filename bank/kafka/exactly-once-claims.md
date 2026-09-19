---
title: A team says their pipeline is exactly once. What do you ask them?
difficulty: 4
tags: [kafka, delivery, transactions, correctness]
time_minutes: 6
order: 30
---

## Ask

A team tells you their Kafka pipeline is exactly once, end to end, into a database. What questions
do you ask before you believe it?

## Look for

- Separates the Kafka transaction from the write to the external system
- Asks where the offset is committed relative to the database write
- Knows the two workable shapes: one transaction covering both, or an idempotent write with a
  business key
- Treats "exactly once" as a property of one unit, not of a whole workflow

## Red flags

- Accepts the claim because a configuration flag is set
- Believes the producer setting alone gives exactly once into a database
- Cannot describe what a repeat would look like in the data

## Follow-ups

- The consumer crashes between the database write and the offset commit. What does the data look
  like after recovery?
- What would you put in the table to make a repeat harmless?
