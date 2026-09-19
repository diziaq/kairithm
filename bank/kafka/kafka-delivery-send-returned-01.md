---
id: kafka-delivery-send-returned-01
schema_version: 1
title: The send call returned, so the data is safe
category: kafka
topic: delivery-semantics
level: junior
tags: [correctness, failure-modes, api-design]
time_estimate_min: 6
order: 18
links:
  deeper: [kafka-delivery-acks-min-isr-01, kafka-delivery-exactly-once-claim-01]
---

## Ask

A developer tells you their write is safe because `producer.send(record)` returned without
throwing, so the service deletes its local copy of the data on the next line. What would you check
before agreeing with them?

## Tests

Whether the candidate knows that handing a record to the producer is not the same as the record
being stored, and can say what the gap between the two contains.

## Listen for

- Says the call puts the record in a buffer and returns before anything has reached a broker
- Asks whether anyone waits on the returned result or inspects the callback
- Asks what `acks` is set to, and says what each choice actually waits for
- Connects a failure happening in the background to data that has already been deleted locally

## Expected knowledge

- The producer gathers records in memory and a background thread sends them
- `acks=0`, `acks=1` and `acks=all` wait for nothing, for the leader, and for the current in-sync
  replicas

## Strong signals

- Asks what happens to whatever is still buffered when the process is killed
- Separates "a broker took it" from "enough copies exist for it to survive a failure"
- Asks whether the delete could simply be moved after the confirmation

## Weak signals

- Treats a call that returned as a durable write
- Cannot say what the returned object is for
- Thinks an exception is the only way a write can fail

## Answer bands

### weak

- Accepts that no exception means the data is stored.
- Cannot say what happens between the call returning and a broker holding the record.
- Treats the local copy as safe to delete on that line.

### junior

- Says the call hands the record to a buffer and returns straight away.
- Asks whether the result is ever waited on, or the callback ever inspected.
- Knows there is a setting controlling how many copies must confirm.

### mid

- Says what each of the confirmation choices waits for, and what is given up with each.
- Points out that killing the process throws away whatever is still buffered.
- Refuses to let the local copy go until something has confirmed the write.

## Follow-ups

- The pod is terminated one second after that line runs. What is on the broker?
  probes: the in-memory buffer, and what an abrupt shutdown does to it
- They add a log line in the callback, never see an error, and still lose records about once a
  month. What next?
  probes: whether they inspect the failure argument at all, and whether one copy is enough
- What would you want that code to do differently before the local copy is thrown away?
  probes: waiting for the result, or ordering the delete after it

## Sources

- https://kafka.apache.org/documentation/#producerapi
- https://kafka.apache.org/documentation/#producerconfigs_acks
