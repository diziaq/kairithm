---
id: database-cloud-databases-transaction-pooling-01
schema_version: 2
title: The pooler mode changed and two things quietly stopped working
category: database
topic: cloud-databases
level: lead
tags: [operations, correctness, failure-modes, ownership]
time_estimate_min: 12
order: 670
links:
  shallower: [database-cloud-databases-aurora-failover-four-hour-outage-01]
---

## Ask

The PgBouncer in front of your PostgreSQL cluster was switched from session mode to transaction
mode. Throughput went up four times and nobody will give that back. Since then a nightly job that
takes an advisory lock has run twice at once, and one service's statement timeout is ignored
about a third of the time. Neither reports an error. What happened, and what do you do?

## Tests

Whether the candidate understands what a pooling mode actually changes about the lifetime of a
backend, can predict which features stop working from that alone, and can keep the throughput
while making the two defects go away.

## Ideal minimal answer

Transaction mode returns the backend at commit, so anything whose lifetime is the session lands
on a connection the client no longer owns and is gone next time — a lock taken outside a
transaction, a setting applied once after connecting. Take the lock for the life of a transaction
instead, and put the timeout on the role or on each statement rather than on connect.

## Listen for

- States the rule once and derives everything from it: in this mode the backend belongs to the
  client only for the duration of a transaction, and any two statements outside one may land on
  different backends
- Applies it to the lock: a lock held by a session outlives the transaction, so it is left on a
  backend that is handed to somebody else, and the second run of the job asks a different backend
  and gets it
- Applies it to the timeout: it was set once after connecting, so it is on one backend and the
  service's later transactions mostly run on others
- Says neither produces an error because both are perfectly legal statements that simply had no
  effect where it mattered
- Reaches for the transaction-scoped form of the lock, which is released at commit and therefore
  fits the mode
- Moves the timeout to where the pooler cannot lose it: on the database or the role, or set inside
  each transaction
- Wants an inventory of the other session-lifetime things in the codebase before declaring it
  fixed
- Keeps the throughput: nobody proposes going back to session mode as the answer

## Expected knowledge

- A pooler in session mode assigns a backend for as long as the client is connected; in
  transaction mode only for the duration of a transaction
- Settings applied after connecting, notification subscriptions, cursors held open past commit,
  and temporary tables all have session lifetime

## Strong signals

- Asks what the pooler runs on a backend before handing it on, and whether that is active in this
  mode
- Notices that the nightly job's mutual exclusion was never really enforced, only usually
  observed, and treats the four-times throughput win as the thing that exposed it
- Says which of the two defects is dangerous and which is merely untidy, and fixes them in that
  order
- Asks who owns the pooler configuration and whether the application teams were told the mode
  changed
- Proposes a way to detect the class of fault, not just these two, before the next one bites

## Weak signals

- Proposes going back to session mode and treats the throughput as a nice-to-have
- Gives the nightly job a direct connection that bypasses the pooler, with nothing about keeping
  that true
- Says the pooler is buggy, or opens a ticket with the vendor
- Adds a lock in the application to stop the job running twice
- Lays out the trade-offs of the three pooling modes and will not recommend a configuration

## Answer bands

### mid

- Says the connection is no longer the same one between transactions.
- Connects that to the lock being left somewhere and the setting not being there.
- Suggests a dedicated connection for the nightly job.

### senior

- States the lifetime rule once and derives both symptoms from it, of their own accord.
- Names the transaction-scoped form of the lock and says when it is released.
- Puts the timeout somewhere the pooler cannot lose, and says which of the available places they
  would choose.
- Says why nothing raised an error, rather than being surprised by it.

### lead

- Enumerates the rest of the session-lifetime surface and says how the team audits for it.
- Keeps the throughput and fixes the correctness, rather than trading one for the other.
- Decides who owns the pooling mode and what has to happen before it is changed again.
- Says what is watched from now on, and what evidence would show the nightly job overlapping.
- Names the operational cost of any carve-out and whether it will survive a year of turnover.

## Follow-ups

- The team's proposal is to give the nightly job its own connection that goes straight past the
  pooler. Would you sign that off?
  probes: whether a carve-out is treated as a thing somebody has to keep true, or as a fix
- Somebody asks what else in this codebase might already be broken and nobody has noticed. How do
  you find out by Friday?
  probes: an inventory of session-lifetime features rather than chasing the next symptom
- A month later the driver is upgraded and calls start failing with a complaint about a name the
  server has never heard of.
  probes: statements the server holds by name, and what the pooler has to be told to track them
- Going back is off the table and the numbers say so. What do you actually recommend?
  probes: whether they can keep the win and still close both defects

## Sources

- https://www.pgbouncer.org/features.html
- https://www.pgbouncer.org/config.html
- https://www.postgresql.org/docs/current/explicit-locking.html
- https://www.postgresql.org/docs/current/functions-admin.html
- https://www.postgresql.org/docs/current/runtime-config-client.html

## Notes

PgBouncer's own description of the two modes: session pooling is the "most polite method. When a
client connects, a server connection will be assigned to it for the whole duration it stays
connected"; transaction pooling means "a server connection is assigned to a client only during a
transaction. When PgBouncer notices that the transaction is over, the server will be put back into
the pool." Its feature table marks a set of things as never working in transaction mode, and the
documentation says plainly that transaction pooling "breaks client expectations of the server by
design".

The list worth having in your head, from that table: `SET` and `RESET`, `LISTEN`, `WITH HOLD`
cursors, `PREPARE` and `DEALLOCATE`, `LOAD`, session-level advisory locks, and temporary tables
declared to survive a commit.

On the locks, the PostgreSQL manual is exact: "Once acquired at session level, an advisory lock is
held until explicitly released or the session ends... Transaction-level lock requests, on the
other hand, behave more like regular lock requests: they are automatically released at the end of
the transaction." So `pg_advisory_lock` is the wrong call here and `pg_advisory_xact_lock` is the
right one — with the consequence, worth drawing out, that the nightly job must now hold one
transaction for as long as it wants the exclusion, which is a design change and not a one-word
edit.

Two things a strong candidate may raise and both are correct:

- `server_reset_query` defaults to `DISCARD ALL`, but `server_reset_query_always` defaults to off,
  so in transaction mode the reset is *not* run. Backend state genuinely carries over between
  unrelated clients.
- Protocol-level named statements do work in transaction mode, but only if
  `max_prepared_statements` is non-zero so the pooler tracks them. That is the fourth follow-up.

Figures to release when asked: about 900 application connections onto 40 backends; the nightly
job runs on two instances of the same service, either of which may pick it up; the timeout is set
in a connection-init callback in the pool's configuration; there is no monitoring on the job
having overlapped.

This is the `lead` step above the Aurora failover card. That one is about client state surviving
a change on the server side; this one is about server state not surviving a change on the client
side. The common thread is that a connection is not the thing the application thinks it is.
