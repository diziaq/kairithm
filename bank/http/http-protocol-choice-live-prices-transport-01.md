---
id: http-protocol-choice-live-prices-transport-01
schema_version: 2
title: Live prices for two thousand desks
category: http
topic: protocol-choice
level: lead
tags: [operations, scalability, failure-modes, api-design]
time_estimate_min: 12
order: 160
links:
  related: [spring-web-layer-long-running-request-01]
---

## Ask

The trading desk wants live prices in the browser: a few hundred instruments, updating up to
twice a second, for about two thousand users. The team has proposed a WebSocket tier with a
Redis fan-out behind it. You own the decision. What do you want to know first, and what is the
team taking on by shipping this?

## Tests

Whether the candidate picks a transport from what the data actually does, and can name what a
stateless team inherits the day it starts holding connections open.

## Ideal minimal answer

Ask whether anything travels from the browser to the server beyond subscribing; if not, a
one-way stream over ordinary HTTP does the job and every proxy, balancer and deploy keeps
behaving normally. Either way the team now owns long-lived connections: instances that cannot be
replaced quickly, everybody reconnecting at once after each deploy, and a fan-out on the live
path.

## Listen for

- Asks which direction data actually flows, and notices that a price feed is one-way
- Names what a one-way stream over ordinary HTTP gives for free: it is a normal response, so
  proxies, balancers and content networks handle it without special configuration, the browser
  reconnects by itself, and it can tell the server where it left off
- Names what it costs: text only, and on the older protocol version a browser holds only a
  handful of connections per origin
- Says the connection is now state: the instance holding it cannot be replaced without
  disconnecting people
- A deploy disconnects everyone at once and they all return at once; wants that spread out, with
  a measured budget for the reconnect wave
- Connection count rather than request rate becomes the scaling signal, and the autoscaler is
  almost certainly watching the wrong thing today
- The fan-out is a new dependency on the live path; asks what a trader sees when it is slow or
  gone
- Does the arithmetic: two thousand users times what each is actually watching, and asks whether
  the server filters per user or ships everything
- Asks whether the desk needs every tick or the latest value, because collapsing updates changes
  the size of the problem by an order of magnitude

## Expected knowledge

- A held-open connection occupies resources on every hop between the browser and the server, not
  only at the end
- An instance holding connections cannot drain in the time an ordinary instance can

## Strong signals

- Asks what a client that missed updates does — resume, resynchronise, or show a stale price —
  and what a stale price costs on a trading desk
- Questions whether twice a second is a requirement or a habit, and what a human can perceive
- Treats pinning a user to one instance as a judgement to be made here, with a cost, rather than
  as a rule to be quoted either way
- Costs the operational change honestly: a team that has only ever run stateless services now
  runs a stateful tier, and says who learns that and when
- Asks what happens on the desk's network — corporate proxies, idle timeouts, the laptop closing

## Weak signals

- Picks the transport on performance grounds with no numbers
- Assumes the proxies and balancers already in the path handle held-open connections
- Has no answer for what a deploy does
- Treats the fan-out as free
- Says "use WebSocket, it is the standard for real time"
- Sets out both transports even-handedly and will not say which one they would sign off

## Answer bands

### mid

- Compares the two transports on what each can carry and picks one.
- Raises that the server has to push rather than be polled.

### senior

- Asks about the direction of the data before choosing, and uses the answer.
- Names what the team takes on: draining, reconnect waves, connection count as the scaling unit.
- Works out the message volume from the figures rather than assuming it is small.

### lead

- Decides, and states the conditions — what has to be true about deploys, about the fan-out, and
  about what a client does after a gap.
- Plans the first deploy under load, including who watches what.
- Says what the desk is told when it degrades, and who tells them.
- Names the cheapest thing that would have answered the requirement, and whether it was tried.

## Follow-ups

- You deploy at 09:15 on a trading day. Walk me through the next sixty seconds.
  probes: everybody dropped at once, everybody back at once, spacing it out, and what the
  browser shows meanwhile
- One team asks that a given user always comes back to the same instance. Do you agree, and what
  do you want in return?
  probes: affinity as a judgement — what it buys, what it costs at deploy and under autoscaling,
  and whether they set an expiry and a fallback rather than quoting a rule
- Half the desk is behind a corporate proxy that drops anything idle for sixty seconds.
  probes: heartbeats, connections that die silently, how the client notices and recovers
- Two thousand browsers each want thirty instruments, the tabs are open all day, and nobody is
  looking at most of them.
  probes: filtering on the server, collapsing updates, and whether the client should say what it
  is actually displaying

## Sources

- https://www.rfc-editor.org/rfc/rfc6455.html
- https://html.spec.whatwg.org/multipage/server-sent-events.html
- https://www.rfc-editor.org/rfc/rfc9113.html#section-9.1
- https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events

## Notes

Figures to release if asked: about 2,000 concurrent users; roughly 300 instruments, each
updating up to twice a second; a message is about 120 bytes; deploys go out three times a week
at 09:15; the current stack is stateless Spring Boot behind an application-level ingress; nobody
on the team has run a stateful tier before.

Both transports are defensible and the card does not have a preferred answer. What separates the
bands is whether the candidate asks about direction before choosing, and whether they name the
operational inheritance either way.

Verified details worth having ready. Server-sent events are defined in the WHATWG HTML standard:
the browser reconnects automatically and re-sends the identifier of the last event it saw, so
resumption is built in; the payload is UTF-8 text, so binary needs encoding. The per-origin
connection limit is browser behaviour rather than a specification: over HTTP/1.1 browsers cap
concurrent connections to an origin at about six, which is painful with several tabs open;
HTTP/2 multiplexes streams over one connection and removes it, with a default of 100 concurrent
streams. WebSocket (RFC 6455) starts as an HTTP upgrade and then stops being HTTP, which is
exactly why intermediaries need to be configured for it.

The affinity follow-up is the same judgement as in `http-load-balancing-own-the-proxy-layer-01`
and is deliberately unresolved. The two source articles behind this category contradict each
other on it, which is the sign that it is a decision and not a rule.
