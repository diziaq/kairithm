---
id: http-load-balancing-grpc-one-pod-hot-01
schema_version: 2
title: One instance takes seventy per cent of the calls
category: http
topic: load-balancing
level: senior
tags: [scalability, performance, failure-modes, operations]
time_estimate_min: 10
order: 110
links:
  deeper: [http-load-balancing-own-the-proxy-layer-01]
  related: [kafka-partitioning-hot-partition-01]
---

## Ask

You move an internal call from HTTP/1.1 to gRPC. Throughput improves, but one of your eight
instances is taking about seventy per cent of the calls, the other seven are nearly idle, and the
autoscaler keeps adding instances that get nothing at all. The balancer is set to round robin.
What is going on?

## Tests

Whether the candidate can identify what unit the thing in front is actually distributing, and
see that no choice of algorithm helps while that unit is wrong.

## Ideal minimal answer

gRPC runs many calls over one long-lived connection, and the balancer picks a backend once, when
that connection is opened. After that every call on it lands on the same instance. Round robin
over connections is not round robin over calls — you need something that forwards per call, or
clients that spread themselves across all the backends.

## Listen for

- The thing being distributed is the connection, and the decision is made once, at connect time
- Many calls are multiplexed onto one connection and clients are expected to keep it open, so a
  handful of callers means a handful of connections
- Changing the algorithm cannot help while the unit is a connection — says this before being
  pushed
- Names a fix that changes the unit: a proxy that parses the protocol and forwards each call, or
  a client that resolves every backend and picks per call
- A maximum lifetime on the connection makes clients reconnect periodically and redistribute,
  with a grace period so calls in flight finish
- A newly added instance receives nothing until somebody opens a fresh connection to it, which is
  exactly why scaling out changes nothing
- The one loaded instance is also the one that will fail, and its failure will not shift the
  others' traffic

## Expected knowledge

- A connection carrying multiplexed calls is persistent, and a client is expected to hold one per
  destination rather than many
- A transport-level proxy copies bytes between two connections and never sees an individual call

## Strong signals

- Asks how many client processes there are, and works out that with a handful the skew is
  arithmetic rather than mysterious
- Points out the autoscaler is reading a signal that cannot improve, so it will keep spending
  money until someone stops it
- Weighs the two real fixes against each other on ownership: a proxy is one thing to run, client
  balancing is a policy living in every caller's deploy
- Asks what happens to calls in flight when a connection is deliberately retired, and wants the
  retirements spread out rather than synchronised

## Weak signals

- Switches round robin to least connections, which distributes the same unit
- Suggests raising the instance count
- Reaches for session affinity settings
- Blames the balancer's hashing without saying what it is hashing
- Weighs a proxy that reads the calls against balancing in the client and will not say which one
  they would run

## Answer bands

### mid

- Says the connection stays open and the calls follow it to one instance.
- Suggests putting something in front that understands the protocol.

### senior

- States, without being led there, that the balancing unit is the connection and the algorithm is
  therefore irrelevant.
- Names at least two fixes and says what each one costs to run.
- Explains why new instances stay empty and why the autoscaler will not stop.

### lead

- Chooses between a proxy and client-side balancing from who owns the upgrade path for each.
- Raises deliberate connection retirement, including what it does to calls in flight and what
  happens if every client retires at the same instant.
- Names what would have caught this before the change shipped, and what to watch now.

## Follow-ups

- Somebody reconfigures it to send each new connection to whichever instance has the fewest open.
  Talk me through tomorrow.
  probes: the plausible wrong answer — the unit has not changed
- You add a rule that closes each connection after an hour. What does a caller see at that
  moment, and what does it look like across thirty instances?
  probes: graceful close plus a grace period, jitter, synchronised reconnects
- There are three calling services and each runs two copies. Does that change your diagnosis?
  probes: six connections over eight backends; the skew is arithmetic
- The autoscaler is watching processor usage. Why is it still adding capacity?
  probes: a signal that cannot improve, and runaway cost

## Sources

- https://www.rfc-editor.org/rfc/rfc9113.html#section-9.1
- https://grpc.io/blog/grpc-load-balancing/
- https://github.com/grpc/proposal/blob/master/A9-server-side-conn-mgt.md
- https://grpc.github.io/grpc-java/javadoc/io/grpc/netty/NettyServerBuilder.html#maxConnectionAge(long,java.util.concurrent.TimeUnit)

## Notes

Figures to release if asked: eight instances; three calling services running two copies each;
about 2,000 calls a second; the balancer is a transport-level cloud balancer; the autoscaler
targets 70% processor usage and has gone from eight instances to twenty-three.

The mechanism, verified: RFC 9113 §9.1 says "Clients SHOULD NOT open more than one HTTP/2
connection to a given host and port pair" and that these connections are persistent. A
transport-level proxy, in gRPC's own words, "terminates the TCP connection and opens another
connection to the backend of choice" and then simply copies frames — so it distributes
connections, not calls. The three sanctioned fixes are an application-level proxy, client-side
balancing, and look-aside balancing.

On connection age: grpc-java's `maxConnectionAge` gracefully terminates a connection after a set
lifetime and adds a random jitter of ±10% so that a fleet does not reconnect in lockstep;
`maxConnectionAgeGrace` gives calls in flight time to finish. There is no default — it is off
unless someone sets it. A candidate who proposes this without mentioning jitter has invented a
thundering herd; that is worth probing, not failing.
