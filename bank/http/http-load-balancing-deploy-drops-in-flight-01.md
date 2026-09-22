---
id: http-load-balancing-deploy-drops-in-flight-01
schema_version: 2
title: Every deploy costs a few hundred 502s
category: http
topic: load-balancing
level: mid
tags: [operations, failure-modes, correctness]
time_estimate_min: 8
order: 105
links:
  deeper: [http-load-balancing-grpc-one-pod-hot-01]
  related: [spring-bean-lifecycle-graceful-shutdown-01]
---

## Ask

Every rolling deploy produces a burst of 502s — a few hundred, over about twenty seconds. The
instances handle the shutdown signal properly: they stop the HTTP connector and the process is
gone in under a second. The team's proposal is to retry 502s at the gateway. What is actually
happening, and what would you change?

## Tests

Whether the candidate can reason about two independent things happening at once — a process
being told to stop and a router being told to stop using it — and pick a fix that orders them.

## Ideal minimal answer

The instance stops accepting connections the instant it is signalled, but the thing routing to it
has not been updated yet — the signal and the routing change go out in parallel and each
propagates at its own speed. Keep serving for a few seconds after the signal, then finish what is
in flight, then exit.

## Listen for

- Two things start at the same moment and neither waits for the other: the process is told to
  stop, and the routing table is told to drop it
- Requests already on the wire, and connections already open, are cut when the connector closes
  immediately
- The fix is an ordering: go on answering after the signal until the routing change has landed,
  then drain, then exit
- The grace period has to be longer than that pause plus the longest request, or the process is
  killed mid-request anyway
- Retrying a 502 at the gateway repeats work the instance may already have done — acceptable for
  a read, not for anything that charges a card
- Clients and proxies hold connections open across many requests, so the instance has to tell the
  peer to stop using the connection, not merely stop accepting new ones

## Expected knowledge

- A shutdown signal is delivered to the process, not to whatever is routing to it
- A rolling deploy replaces instances one at a time, so this happens once per instance

## Strong signals

- Wants a measured number for how long the routing change takes to reach every hop, rather than
  picking a round one
- Notices there may be two routing layers — an in-cluster one and a cloud balancer outside it —
  reacting at very different speeds
- Prefers telling the balancer explicitly to drain this instance over letting it infer from
  failures
- Asks which of the 502s were reads and which were writes before agreeing to any retry

## Weak signals

- Retries as the entire answer
- Lengthens the grace period without changing when the process stops listening
- Believes a failing readiness signal removes traffic instantly
- Treats a 502 as a client problem
- Tells the story of a release that dropped requests at a previous job and never says what to
  change about this one

## Answer bands

### weak

- Blames the balancer or the network and proposes retries.
- Cannot say what the instance is doing in the twenty-second window.

### junior

- Says traffic is still being sent to an instance that has already stopped listening.
- Suggests the instance keep serving for a while after being signalled.

### mid

- Describes the signal and the routing change as concurrent, and orders them deliberately.
- States that the grace period must cover the pause plus the longest in-flight request.
- Says, once asked whether a repeat is safe, which requests can go again and which cannot.

### senior

- Asks for the measured propagation time and sets the pause from it.
- Separates the in-cluster routing from an external balancer and treats them as two clocks.
- Raises connections the client is holding open without being asked, and what has to be sent to
  release them.

## Follow-ups

- One of the requests in that window was a card charge, and the gateway sent it again. Now what?
  probes: whether they check the safety of a repeat before agreeing to the retry
- You add a pause before the process stops serving. How long, and what tells you the number?
  probes: measuring propagation; the grace period must exceed the pause plus the slowest request
- A client holds one connection open and sends many requests down it. Your instance stops
  accepting new connections — does that help that client?
  probes: existing connections outlive the change; the peer has to be told to stop using it
- The same deploy behaves worse behind the cloud balancer than behind the proxy inside the
  cluster. Why might that be?
  probes: two routing layers with different update speeds

## Sources

- https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination
- https://nginx.org/en/docs/http/ngx_http_upstream_module.html#drain
- https://www.rfc-editor.org/rfc/rfc9113.html#section-6.8
- https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/operations/draining

## Notes

Figures to release if asked: eight instances, replaced one at a time; grace period 30 seconds;
p99 request 800 ms with a handful of uploads at 20 s; traffic arrives through an ingress proxy
which itself sits behind a cloud load balancer; deploys go out four times a week.

The mechanism, from the Kubernetes documentation: "At the same time as the kubelet is starting
graceful shutdown of the Pod, the control plane evaluates whether to remove that shutting-down
Pod from EndpointSlice objects." The two are concurrent by design, and the removal then has to
reach every proxy that holds a copy of the routing table. That is the whole window. A pause
before the process stops serving — a pre-stop hook, or delaying the connector shutdown — is the
standard fix, and it only works if the grace period is longer than the pause.

This is the network-side twin of `spring-bean-lifecycle-graceful-shutdown-01`, which asks about
the ordering inside the process. A candidate who has done one should find the other easier; ask
both only if you want to see whether they connect them.
