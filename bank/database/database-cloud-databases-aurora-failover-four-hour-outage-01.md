---
id: database-cloud-databases-aurora-failover-four-hour-outage-01
schema_version: 1
title: Failover took 32 seconds; the outage took four hours
category: database
topic: cloud-databases
level: senior
tags: [failure-modes, operations, ownership]
time_estimate_min: 9
order: 350
---

## Ask

Your Aurora PostgreSQL cluster fails over at 03:00 and the writer endpoint is moved to what used
to be the reader. AWS reports the failover finished in 32 seconds. Your Java service kept failing
every write until somebody restarted it at 07:20. Why was your outage four hours rather than 32
seconds?

## Tests

Whether the candidate can explain the gap between a provider's recovery and an application's, and
name the client-side state that keeps a process talking to a machine that has changed role.

## Listen for

- The endpoint is a name; something on the client side went on resolving it to the address it had
  before
- A JVM caches the result of resolving a name for a period it controls, and that period is worth
  checking rather than assuming
- The pool was still holding open connections established before the event, and it kept handing
  them out
- Those connections now lead to a machine that has become a reader, so every write is refused
  while an ordinary liveness check on the connection still passes
- The restart worked because it discarded every connection and resolved the name again — that is
  the whole of the fix a human applied
- Something should have thrown the entire pool away the moment writes started being refused
- Four hours with nobody reacting is an alerting failure sitting on top of a connection failure
- Work in flight at the moment of the switch was lost and somebody has to decide whether to
  repeat it

## Expected knowledge

- A pooled connection outlives the request that borrowed it; the pool chooses when to discard one
- A provider's failover moves a name; it does not reach into your process

## Strong signals

- Asks whether this was ever rehearsed deliberately, rather than only fixing the code
- Notices the roles have swapped, so the old writer now serves reads and the traffic shape
  changes with it
- Separates what the client can fix itself from what a proxy in front of the cluster would fix

## Weak signals

- Concludes the provider's failover did not work and a support ticket is the answer
- Proposes restarting the service on any burst of errors, with no account of what broke
- Accepts 32 seconds as the whole story and calls the four hours a coincidence

## Answer bands

### weak

- Says the failover did not really work and blames the provider.
- Proposes an automatic restart whenever errors appear, without saying what was wrong.
- Cannot say why a restart helped when nothing else did.

### mid

- Says the service was still talking to the machine it had been talking to before.
- Identifies the pool of already-open connections as the thing that had to go.
- Explains that restarting rebuilt every connection and looked the name up again.

### senior

- Separates name resolution on the client from the state of the connections already open, and
  says the restart happened to cure both.
- Describes the exact symptom the application saw — writes refused by a machine that is now a
  reader — and why a pool does not judge such a connection to be dead.
- Names what should have discarded the pool at the first refusal, and where that logic belongs.
- Treats four hours with no response as its own defect, not a detail of the same one.

### lead

- Says how the fix would be proven: trigger the same event on purpose and watch what the service
  does.
- Weighs a client-side fix against putting a managed proxy in front, in cost and in who maintains
  it.
- Decides what the service should do to callers during the window, rather than only how it
  recovers afterwards.

## Follow-ups

- During those 32 seconds a customer's payment was half done. What do you owe that customer?
  probes: in-flight work at the switch, and whether repeating it is safe to do
- You may not touch the application code this week, but you want tomorrow night to cost two
  minutes instead of four hours. What is the smallest change you make?
  probes: whether detection and an automated restart are recognised as a floor under a proper fix
- The night this happened, the service was scaled from four instances to forty while people tried
  things. The cluster then began refusing new arrivals entirely. What do you think happened?
  probes: the ceiling on simultaneous clients of a modest instance, and that a pool per instance
  multiplies
- A colleague says this cannot be rehearsed without risking production. What do you propose?
  probes: whether recovery is ever exercised on purpose, and in which environment

## Notes

Figures to release when asked, and credit the candidate who asks: a db.r6g.large writer; roughly
40 service instances at peak with a pool of 10 each; the on-call alert was on the cluster, which
was healthy from 03:00:32 onwards, and not on the service's own error rate.

Two client-side details worth knowing and worth crediting, neither of which a candidate has to
name to pass:

- The positive DNS cache in a HotSpot JVM is controlled by `networkaddress.cache.ttl`; it is 30
  seconds by default and forever when a security manager is installed. Check the value for the
  JDK in use rather than quoting one.
- PostgreSQL answers a write on a hot standby with SQLSTATE 25006, `read_only_sql_transaction`.
  That is an ordinary SQL error, so a pool testing connections with a trivial query sees nothing
  wrong.

## Sources

- https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/Concepts.AuroraHighAvailability.html
- https://www.postgresql.org/docs/current/errcodes-appendix.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/net/InetAddress.html
