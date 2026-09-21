---
id: microservices-messaging-backlog-replay-expiry-01
schema_version: 2
title: Nine hours behind, and the queue only keeps a day
category: microservices
topic: messaging
level: senior
tags: [messaging, failure-modes, operations, scalability]
time_estimate_min: 9
order: 115
links:
  deeper: [microservices-messaging-ordering-out-of-order-address-01]
  related: [microservices-failure-handling-cascade-slow-dependency-01]
---

## Ask

An upstream team replayed six months of history onto your queue last night. Your consumer is
running flat out, the queue is nine hours behind and getting worse, and anything older than
twenty-four hours is dropped. The team's plan is to raise that to seven days. Tell me what is
actually happening, and what you do today.

## Tests

Whether the candidate reasons about a queue as a buffer with a finite lifetime — arrival rate
against drain rate, what is lost the moment it overflows, and where the pressure ends up — rather
than making the buffer bigger.

## Ideal minimal answer

Arrivals exceed the drain rate, so depth grows and a longer limit only moves the deadline: at
twenty-four hours each unprocessed message is dropped, its change is never applied, the record
keeps its old value and nothing records that it existed. Today, work backwards from when the
oldest expires, move the replay off the live path, and ask the upstream team to stop.

## Listen for

- Compares the two rates out loud: the depth grows because more arrive than leave, and more room
  to store them changes neither number
- A longer limit buys hours, and only helps if the consumer eventually clears faster than the
  arrivals; if it does not, the same messages fall off the end a week later
- Says what an expired message costs in the data: the change it carried is never applied, the
  record keeps the value it had, and nothing in the system knows a message was there
- Today's events are queued behind last night's history, so live traffic is nine hours late too,
  even though nothing is wrong with it
- Nothing here makes the producer wait — that is the point of a queue — so the pressure shows up
  as unbounded depth instead of a slow producer, and someone has to ask the upstream team to stop
- Ways to drain faster, each with what it moves the load onto: more consumers all writing to the
  same store, fewer round trips per message, less work per message
- Puts the replay on its own path so it is not in front of live traffic
- Drops on purpose where it is safe: if a hundred of those messages are updates to one record,
  only the newest one changes anything
- Watches the depth as a time — how far behind — because that is the number that predicts the
  loss, not the count

## Expected knowledge

- A queue absorbs a burst only when the consumer is on average faster than the producer
- Messages are kept for a bounded time or size, and what passes the bound is gone

## Strong signals

- Works out the moment the oldest message expires and treats it as a deadline, then works
  backwards from it
- Asks whether the replayed messages can be told apart from the live ones at all
- Asks what the downstream data looks like after a gap and how it would be rebuilt from whoever
  owns the fact, rather than assuming the messages are the only copy
- Asks whether the replay was even wanted by the consumers before spending a day on draining it

## Weak signals

- Raises the limit and considers it handled
- Adds consumer instances without asking what they all write to
- Says it will catch up eventually, with no comparison of the two rates
- Purges the queue to get back to live traffic and cannot say what was in it
- Answers entirely in one broker's configuration settings

## Answer bands

### mid

- Compares how fast messages arrive with how fast they are cleared, and sees that only the second
  being larger makes the depth fall.
- Adds consumers, and names the thing they all contend for.
- Notices that live events are sitting behind the replayed ones.

### senior

- Says what happens to one specific message at the moment it passes the limit, and what the record
  it was going to update holds afterwards.
- Turns the depth and the drain rate into a deadline and plans against it.
- Names where the load lands once the consumer goes faster, and bounds it there.
- Separates the replayed traffic from the live traffic so one no longer delays the other.
- Points out that the producer feels none of this, and names something that would make it feel it.

### lead

- Decides what may be dropped deliberately and what may not, and says how that is defended to the
  teams downstream.
- Says which alarm should have fired hours earlier and what number it watches.
- Turns the next replay into something agreed with the upstream team in advance rather than
  survived.

## Follow-ups

- Say you clear two thousand a second and they are still sending three thousand. What does
  tonight look like?
  probes: whether the two rates are compared at all, and whether they see the depth never falls
- You add thirty more consumers and the writes start timing out. What now?
  probes: where the limit moves once the consumer is no longer it
- One of last night's messages was a customer changing their address, and it falls off the end at
  midnight. What does that customer's record say tomorrow, and who finds out?
  probes: naming the damage in the data, and whether the gap can be repaired from the owner
- The same team tell you they will do this again next month. What do you ask them for?
  probes: control at the producing end, a separate path, warning in advance

## Sources

- https://sre.google/sre-book/addressing-cascading-failures/

## Notes

Keep this at the pattern level. Delivery semantics, partition counts and consumer groups belong
to the Kafka category; if the candidate goes there, bring them back to the two rates, the
deadline, and what happens to the data in the messages that do not make it.
