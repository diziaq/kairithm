---
id: kafka-consumer-groups-flapping-member-01
schema_version: 2
title: One pod keeps dropping out and the whole group stalls
category: kafka
topic: consumer-groups
level: mid
tags: [operations, failure-modes, observability]
time_estimate_min: 8
order: 40
---

## Ask

One pod in a consumer group is thrown out and re-joins every few minutes, and each time it
happens the entire group stops reading for a moment. The pod's processor use is low, its memory
is fine, and the brokers are healthy. Where do you look?

## Tests

Whether the candidate knows the two different reasons a member is declared dead, and can separate
a stalled handler from a network problem.

## Ideal minimal answer

Handling one batch is taking longer than the member is allowed to go quiet, so the group throws
it out; every departure and return makes the group hand out the partitions again, and that
redistribution is the pause everyone else sees. Fetch fewer records per poll, or move the slow
work off the loop, before raising any timeout.

## Listen for

- Asks how long handling one batch takes, and compares that against `max.poll.interval.ms`
- Knows the heartbeat is sent from its own thread, so a stuck handler shows up as a missed poll
  rather than a missed heartbeat
- Connects the group-wide pause to every member's partitions being taken away and handed out
  again, which is what the long-standing protocol does on each departure and each return
- Suggests fetching fewer records at a time, or moving slow work off the main thread, before
  raising any timeout
- Asks whether one unusual record is what takes minutes to get through

## Expected knowledge

- A member is dropped when it stops sending heartbeats, or when it goes too long without asking
  for more records
- A member leaving or arriving makes the group divide the partitions again; how much of the group
  has to stop while that happens depends on which protocol the clients are using

## Strong signals

- Notices that the evicted member's attempt to record its position will be rejected, so the batch
  it had just finished arrives again somewhere else
- Asks for the tail of the handler's duration rather than the mean
- Asks whether the pod gets enough shutdown grace to leave cleanly

## Weak signals

- Raises the timeout without finding out what the handler is doing
- Confuses the background heartbeat with the main loop
- Does not connect one pod's exit to the other pods pausing
- Tells the story of a pod that flapped at a previous job and never says where to look on this one

## Answer bands

### weak

- Blames the network and restarts the pod.
- Cannot say why one member leaving would affect the others.
- Proposes a larger pod with no evidence that it is short of anything.

### mid

- Compares how long a batch takes to handle against how long a member is allowed to go quiet.
- Says every departure and return makes the group redistribute its work, and that is the pause.
- Proposes smaller batches or faster handling before raising any limit.

### senior

- Separates a missed heartbeat from a member that simply stopped asking for records, and says
  which one this is.
- Points out that the records handled just before the eviction are likely to be handled again.
- Asks for the tail of the handler's duration rather than the mean, and names what they would
  graph.

## Follow-ups

- They raise the limit to thirty minutes and the flapping stops. What have they just signed up
  for?
  probes: how long a genuinely dead pod now goes unnoticed
- After each of these episodes, support receives two copies of one notification email. Why?
  probes: connects the eviction to the position never being recorded
- One record in a hundred thousand takes four minutes to get through. How would you stop it taking
  the group down?
  probes: isolating slow or poisonous work away from the main loop

## Sources

- https://cwiki.apache.org/confluence/display/KAFKA/KIP-62%3A+Allow+consumer+to+send+heartbeats+from+a+background+thread
- https://kafka.apache.org/documentation/#consumerconfigs_max.poll.interval.ms
- https://cwiki.apache.org/confluence/display/KAFKA/KIP-429%3A+Kafka+Consumer+Incremental+Rebalance+Protocol

## Notes

Worth separating out loud if the candidate blurs them: the heartbeat runs on a background thread
and keeps the member alive while the handler is busy (KIP-62); the poll interval is the separate
limit that catches a handler which has stopped making progress. Because of that split, a stuck
handler is evicted for missing the poll deadline, not for missing a heartbeat — which is the part
candidates most often get backwards.

The scenario states that the whole group pauses, and that is what the long-standing eager
protocol does: every member gives up every partition before anything is handed out. It is not
universal. With a cooperative assignor only the partitions that actually move are revoked, and
the newer broker-driven protocol (KIP-848) changes the picture again, so the size of the pause
depends on the client version and the assignor configured. A candidate who asks which is in use
before explaining the pause is ahead, not pedantic.
