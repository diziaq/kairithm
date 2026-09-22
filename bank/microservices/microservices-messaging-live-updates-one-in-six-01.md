---
id: microservices-messaging-live-updates-one-in-six-01
schema_version: 2
title: She sees one live update in six
category: microservices
topic: messaging
level: senior
tags: [failure-modes, capacity, consistency, operations]
time_estimate_min: 9
order: 635
links:
  shallower: [microservices-messaging-outbox-dual-write-01]
  deeper: [microservices-messaging-ordering-out-of-order-address-01]
---

## Ask

Your service pushes live order updates to the browser over a WebSocket. On one instance it worked.
On six, a customer watching her order gets about one update in six and never sees the rest. A
colleague says to switch on session pinning at the load balancer. What is actually wrong, and does
that fix it?

## Tests

Whether the candidate can say where the open connections are and where the update is produced, and
sees that pinning the customer changes neither.

## Ideal minimal answer

Each instance can only write to the sockets it is holding, and the update is produced by whichever
instance handled the order change, so only the customers connected to that one get it — one in
six. Pinning does not help: she is already on one instance, just not the one that produced it.
Every instance has to receive every update and push it to its own sockets.

## Listen for

- Names the two locations: her socket is held by one instance's memory, and the update is produced
  somewhere else entirely
- Says pinning changes nothing here, and can say why: it makes her requests land on the same
  instance, which is already true of an open socket
- Does the arithmetic — with six instances taking order traffic evenly, the producing instance is
  hers about one time in six
- Needs the update to reach all six instances, each of which pushes only to the sockets it holds
  and ignores the rest
- Notices that a shared group of consumers gives the update to one instance, which is the bug
  again — each instance needs its own view of the stream
- Asks what happens while her socket is reconnecting, and wants the screen to be correctable from
  stored state rather than depending on having caught every message
- Raises what a socket costs to hold — memory, a file descriptor, an idle timeout at the balancer
  and any proxy in between — before planning for sixty instances
- Considers giving the sockets their own tier so the service that owns the orders is not also
  holding a hundred thousand connections

## Expected knowledge

- An open socket is held by one process and cannot be written to by another
- Fanning a message out to every instance and handing it to one of them are different things
- A browser connection can drop and come back without the server noticing promptly

## Strong signals

- Draws it: where her socket is, where the order write happened, and the missing path between them
- Asks whether every update is essential or whether the screen can be brought up to date after a
  gap, and designs for the second
- Points out that each instance needs to know which of its sockets cares about a given order, and
  says how it would know
- Asks the number of concurrent connections and the update rate before choosing between a shared
  stream and a dedicated push tier

## Weak signals

- Accepts the pinning as the fix
- Proposes that the producing instance call the other five over HTTP and keeps that as the design
  at sixty instances
- Has the browser poll instead, without pricing what the polling costs at this connection count
- Puts all the sockets on one instance and scales that instance up
- Adds a shared cache of updates without saying who reads it or when
- Lists the options and will not choose one

## Answer bands

### mid

- Says the update only reaches the customers connected to one instance, once asked where the
  socket lives.
- Doubts that pinning helps and can be led to why.
- Wants some shared path between the instances without saying what each end does with it.

### senior

- Volunteers that the socket and the producer are on different instances, and that pinning
  addresses neither.
- Describes the fix precisely: every instance consumes every update and writes to the sockets it
  holds.
- Distinguishes fanning out to all instances from handing a message to one of them, and says which
  this needs.
- Asks what she sees after a reconnect, and treats catching up from stored state as part of the
  design.

### lead

- Chooses between every instance consuming everything and a separate tier that owns the
  connections, and prices both at the connection count given.
- Says what the screen is allowed to miss and for how long, as a product-facing decision.
- Names the operational cost — idle timeouts, deploys dropping connections, reconnect storms —
  and what is done about each.
- Says which team owns the push path once it is not a side effect of the order service.

## Follow-ups

- They put the pinning in anyway. Which of her updates arrive now, and which do not?
  probes: whether they can say pinning leaves the producer exactly where it was
- All six instances now read the same stream through one shared group of consumers. What does she
  see?
  probes: one-of-N delivery versus reaching every instance
- Her phone loses signal for ninety seconds and then comes back. What is on her screen?
  probes: gaps while disconnected, and whether the screen can be rebuilt from stored state
- Six instances become sixty, each holding twenty thousand connections, and every update goes to
  all sixty. What runs out first?
  probes: the cost of fanning out per instance, filtering, and a dedicated connection tier

## Sources

- https://www.rfc-editor.org/rfc/rfc6455#section-1.1
- https://socket.io/docs/v4/using-multiple-nodes/
- https://docs.spring.io/spring-framework/reference/web/websocket/stomp/handle-broker-relay.html

## Notes

Keep this broker-neutral: the requirement is that every instance sees every update and filters to
its own sockets, whatever carries it. Socket.io's own documentation is the clearest statement of
both halves — pinning is needed for its long-polling handshake, and a separate mechanism is needed
to pass messages between processes — which is worth knowing because it shows the two questions are
unrelated.

Figures to release when asked: six instances behind one balancer, about four thousand open
connections each at peak, order updates at two hundred a second across all tenants, and the
balancer closes idle connections after sixty seconds.
