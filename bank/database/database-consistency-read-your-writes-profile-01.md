---
id: database-consistency-read-your-writes-profile-01
schema_version: 2
title: The operator saved the opening hours; the list shows the old ones
category: database
topic: consistency
level: senior
tags: [consistency, transactions, failure-modes, observability]
time_estimate_min: 10
order: 220
links:
  related: [kafka-offsets-external-store-01]
  deeper: [database-consistency-quorum-dashboard-disagrees-01]
---

## Ask

In the back-office tool an operator edits a store's opening hours, the save returns, and the list
page comes back with the old hours. A second refresh shows the new ones. Anything the code marks
read-only goes to a hot standby; writes go to the primary. A ticket proposes making every commit
wait for the standby. Talk me through what you would do.

## Tests

Whether the candidate can state the guarantee this one session needs, scope it to that session,
and say what the engine can actually promise — instead of buying a global guarantee to fix one
screen.

## Ideal minimal answer

After her own commit this operator must not be shown older data, so scope the fix to that
session — its next reads pinned to the primary, or her write's position compared with the
standby's — rather than making every commit wait. In PostgreSQL only
`synchronous_commit = remote_apply` makes a commit visible to queries on a standby, and only on
the standbys named in `synchronous_standby_names`.

## Listen for

- Reads the timeline: the commit returned from the primary, and the list ran as a read-only
  transaction on a standby that had not applied it yet
- States the guarantee from the writer's side: after my own commit I must not be shown something
  older than it, while other people's edits may arrive late
- Scopes the fix to that session — its next reads pinned to the primary for a window, or the
  position of its own write carried forward and compared against how far the standby has got
- Knows the settings differ in how far the standby has to have got: received, written, flushed,
  or applied and therefore visible to a query there
- Knows a waiting setting only covers the standbys the primary has been told to wait for, so a
  read can still land on one outside that list
- Says what the ticket costs: every writer in the system pays the round trip, and somebody has to
  decide what the primary does when that standby is gone
- Notices the wait can be asked for per transaction rather than for the whole server, so only the
  writes that are read straight back need pay
- Asks how far behind the standbys run now, how far at the worst moment of the week, and whether
  anybody measures it
- Asks whether the list had to be re-read at all, given the save already returned the stored row

## Expected knowledge

- PostgreSQL streaming replication is asynchronous by default: the primary commits without waiting
  for any standby
- `synchronous_commit` has five settings and only `remote_apply` waits until the change has become
  visible to queries on the standby; `on` and `remote_write` stop at durability there
- `synchronous_standby_names` decides which standbys are waited for; if it is empty the remote
  settings degrade to a local wait
- A standby's position can be read (`pg_last_wal_replay_lsn`) and compared with the primary's, but
  nothing in the engine blocks until it arrives

## Strong signals

- Pays for this operator's own edits and lets everyone else's arrive when they arrive
- Asks whether the read after the save was needed at all
- Says what happens to a per-session decision when the next request lands on another instance of
  the tool
- Sets the point at which a standby is pulled out of the read pool, and says who is told
- Separates durability on the standby from visibility on the standby without being led there

## Weak signals

- Sends every read back to the primary and calls it done, with nothing about the load just moved
- Accepts a fixed pause in the page because it worked when they tried it
- Treats all the commit settings as one switch labelled "safer"
- Says the setup is eventually consistent as though that settled the matter
- Takes the ticket as written because it sounds like the strong option
- Lays out sending the read to the primary, waiting for the standby and a bounded window, and will
  not say which one this screen gets

## Answer bands

### mid

- Explains the timeline: the write went to one machine and the list to another that was behind.
- Says the ticket makes every write on the system slower to fix one screen.
- Suggests sending that screen's read to the primary.

### senior

- States the guarantee needed and scopes it to the session that wrote, not to the whole system.
- Names what the commit would have to wait for before the standby could answer correctly, and
  separates that from merely having the data safe there.
- Ties the fix to the position of the actual write, or to a bounded window, and says what happens
  when the standby is far behind.
- Points out without being asked that nothing is logged when this happens, and adds the
  measurement.

### lead

- Decides per screen which reads may be behind, and records it where the next team will find it.
- Trades the load taken off the primary against the screens that must now go back to it, in
  numbers.
- Says what the primary should do when a standby it waits for is unreachable, rather than letting
  that be discovered during a patch window.
- Says what the tool shows the operator when the standby is far behind, instead of quietly serving
  the past.

## Follow-ups

- The standby normally trails by under 50 ms. A bulk load runs for two hours and it reaches 40
  seconds. What does the operator see, and what does your fix do?
  probes: whether a fix tuned to the quiet hour survives the loud one
- A different screen in the same tool shows a payout as already sent. Does your answer change?
  probes: ranking a stale read by what it costs, screen by screen
- The operator's next click lands on another instance of the back-office service. Is your fix
  still there?
  probes: where the per-session state lives, and whether it follows the operator
- The team goes ahead with the ticket. At 09:00 one standby is taken down for a patch. What
  happens to the tool?
  probes: the availability cost of waiting, and that every writer pays for one screen

## Sources

- https://www.postgresql.org/docs/current/runtime-config-wal.html
- https://www.postgresql.org/docs/current/runtime-config-replication.html
- https://www.postgresql.org/docs/current/functions-admin.html
- https://www.postgresql.org/docs/current/warm-standby.html

## Notes

Do not run this card in the same session as `microservices-consistency-stale-read-after-write-01`.
That card is about a read model maintained by another service and the product decision behind a
green tick; this one is about where a session's reads are routed and what a database engine can be
made to promise. Together they read as the same question asked twice.

Figures to release when asked, and credit the asking:

- One primary, two hot standbys, read-only transactions load-balanced across both.
- The standbys normally trail by 20–80 ms; one reached 40 seconds during a backfill last month.
- Nothing alerts on that figure today.
- The save endpoint already returns the stored row; the page discards it and re-reads.
- About 30 back-office operators, a few hundred edits a day.

Engine pins, all from the PostgreSQL documentation:

- Streaming replication is asynchronous by default.
- `synchronous_commit` takes `off`, `local`, `remote_write`, `on` (the default) and `remote_apply`.
  Only `remote_apply` waits until the standby has *applied* the commit record, "so that it has
  become visible to queries on the standby(s)". `on` waits for a flush to durable storage there
  and `remote_write` for a write to the standby's file system — both are about durability, not
  visibility. This distinction is where most candidates are vague, and it is the centre of the
  card.
- Any of these only apply to the standbys named in `synchronous_standby_names`; with that setting
  empty, `remote_apply`, `remote_write` and `local` all degrade to the same local behaviour as
  `on`. A read can therefore land on a standby nobody is waiting for.
- The setting can be changed at any time and the behaviour of a transaction is fixed by the value
  in effect when it commits, so `SET LOCAL synchronous_commit = 'remote_apply'` buys the wait for
  one transaction instead of for the whole server. A candidate who reaches this has answered the
  ticket properly.
- There is no built-in call that blocks until a standby has replayed a given position; comparing
  `pg_last_wal_replay_lsn()` on the standby against the position of the write is the application's
  job. MySQL does have such a call, on GTIDs — credit the comparison, do not require it.

The cheapest correct answer is the one nobody offers: the page already had the new values in the
response to the save.
