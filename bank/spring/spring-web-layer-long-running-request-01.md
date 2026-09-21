---
id: spring-web-layer-long-running-request-01
schema_version: 2
title: An export that outlives its own request
category: spring
topic: web-layer
level: lead
tags: [api-design, operations, failure-modes, idempotency]
time_estimate_min: 12
order: 73
links:
  related: [spring-transactions-remote-call-inside-01]
---

## Ask

`POST /exports` builds a spreadsheet that takes anywhere from forty seconds to eleven minutes.
Today the handler blocks until the file is ready, the load balancer in front of it cuts every
connection at sixty seconds, the mobile clients retry the moment that happens, and last week's
rolling deploy dropped thirty half-built exports on the floor. You own the redesign. What shape
do you give this endpoint, and what does your choice cost the team that carries the pager?

## Tests

Whether the candidate can choose a request shape for work that outlives a single request from
the stated constraints rather than from habit, and can say what each candidate shape costs in
stored state, in operational work and at deploy time.

## Ideal minimal answer

Separate accepting the work from delivering it: record the job durably, answer at once with
somewhere to come back to, build outside the request, and make a repeated submit attach to the
run already going. Pick that shape against the sixty-second cut-off, and name its standing cost:
a store holding job state, a worker to watch, and cleanup that can itself fall behind.

## Listen for

- Separates accepting the work from delivering the result, so the answer goes back in
  milliseconds and the file is fetched afterwards
- Writes the job down somewhere that survives the process before the client is told yes
- Knows that returning from the handler early only frees the request thread; the work still
  dies with the pod unless it was recorded first
- A repeated submit must land on the run that already exists, keyed by something the client
  sends or something derived from what was asked for
- Names more than one shape and what each one costs: a held-open connection per waiting client,
  against a store that now holds the state of every job and has to be expired
- Says what a rolling deploy does to work in flight, and picks between draining it and making
  it safe to start again
- Gives the client something concrete to come back to, and says how often it may ask
- States what the operator sees when this goes wrong — a growing backlog, a run wedged halfway
  — and what wakes somebody

## Expected knowledge

- That a `202` with somewhere to come back to is the conventional way to say "accepted, not done"
- That state tied to the original request does not follow the work onto another thread
- That an in-memory queue of pending work is gone when the pod is replaced

## Strong signals

- Asks for the distribution of build times and for what the clients actually do on a timeout,
  before proposing anything
- Points out that the caller's identity and the trace identifier live on the original thread and
  have to be carried across deliberately, or the logs for the slow half are anonymous
- Puts an expiry on finished files and names who deletes them
- Says what the endpoint does when the backlog is already thousands deep: refuse, shed, or
  accept and be honest about the wait
- Asks whether the client wants a file at all, or wants to be told when one is ready

## Weak signals

- Raises the load balancer's timeout and stops there
- Hands the work to an in-memory pool, calls it asynchronous, and has no answer for a restart
- Picks a live stream to the browser with no account of what closes an idle connection
- Describes a redesign without ever saying what is guaranteed if the process dies mid-build

## Answer bands

### mid

- Returns from the handler before the file exists and lets the client come back for it later.
- Cannot say what happens to a build that was already running when the process stopped.
- Treats a repeated submit as harmless, or does not raise it.

### senior

- Records the job durably first, answers the client, and runs the build outside the request.
- Makes a second submit attach to the run that is already going rather than starting another.
- Names the window where the process dies mid-build and says what the client sees then.
- Bounds how long a finished file is kept and how often the client may come back.

### lead

- Picks between the shapes from the constraints given — how long a wait is tolerable, how many
  clients wait at once, what the load balancer permits — and says which constraint decided it.
- States the standing cost of the shape chosen: the store that now holds job state, the worker
  somebody has to watch, the cleanup that has to run and can itself fall behind.
- Says what the deploy procedure becomes, and who is woken when the backlog stops draining.
- Names the number on a dashboard that shows this design failing before a customer reports it.
- Says which of the options they would refuse to build here, and what makes it too much
  machinery for this traffic.

## Follow-ups

- The mobile client's own timeout fires and it sends the same thing again. How many spreadsheets
  get built?
  probes: whether a repeat is made safe by design, or merely tolerated
- Ops does a rolling restart at two in the afternoon while forty of these are half finished.
  What do those forty users see?
  probes: draining against restarting the work, and what the client is told in the meantime
- Someone proposes just holding the socket open and dripping bytes down it until the file is
  done. Talk me through that.
  probes: cost per waiting client, idle cut-offs in front of the app, a truncated download that
  looks like a complete one
- A customer says their file never arrived and nobody can find any trace of the attempt. Where
  do you look?
  probes: whether the design is observable at all, and whether the trail survives the hand-off

## Sources

- https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-ann-async.html
- https://docs.spring.io/spring-boot/reference/web/graceful-shutdown.html

## Notes

The point is the choice, not the machinery. Asynchronous request handling in Spring MVC
(`Callable`, `DeferredResult`, `CompletableFuture`, `StreamingResponseBody`) releases the
container thread, but the work still lives in this process and dies with it; graceful shutdown
only waits out the configured grace period. Anything longer than that needs the job written to a
store and a worker that can pick it up again. A candidate who reaches only for the async return
types has answered a smaller question than the one asked.
