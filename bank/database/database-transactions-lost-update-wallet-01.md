---
id: database-transactions-lost-update-wallet-01
schema_version: 1
title: Two top-ups, fifty euros missing
category: database
topic: transactions
level: mid
tags: [transactions, correctness, performance]
time_estimate_min: 10
order: 211
links:
  deeper: [database-transactions-commit-lost-acknowledgement-01]
---

## Ask

Two requests top up the same wallet at the same moment. Each reads the balance as 100, adds 50 in
the application, and writes 150. Both transactions committed, neither raised an error, and the
customer is 50 euros short. Why did the database allow that, and how do you fix it?

## Tests

Whether the candidate can describe why two committed transactions may silently overwrite each
other, and then choose a fix the store enforces rather than one the application hopes for.

## Listen for

- Lays out the interleaving: both reads land before either write, so the second write is computed
  from a value that is already out of date
- Says that on PostgreSQL's default level nothing is violated here — each statement sees the
  latest committed data, and the two statements belong to different transactions
- Offers to do the arithmetic in the database: one statement that adds to the current value rather
  than storing a value worked out in the application
- Or takes a lock on the row at read time and keeps it until the write, and knows that this puts
  the two requests in a queue
- Or carries a version column and makes the write conditional on it, then says what the
  application does when the conditional write changes zero rows
- Asks whether a stored total is the right shape at all, or whether the balance should be derived
  from an append-only list of movements

## Expected knowledge

- The default level on PostgreSQL gives every statement a fresh view of committed data; it
  promises nothing about a value staying still between two statements
- PostgreSQL at repeatable read aborts the second writer of the same row with a serialization
  failure, so the caller has to be ready to run the whole thing again
- InnoDB at repeatable read behaves differently: a plain read comes from a snapshot while an
  update reads the newest committed row, so a read followed by a write of a computed value can
  still be lost
- A lock taken by a statement is held until the transaction ends, not until the statement ends

## Strong signals

- Says the rule has to be enforced by the store, because two application servers cannot agree
  among themselves
- Weighs the lock against throughput on a busy row, and says what a queue of waiters does to
  latency and to the connection pool
- Notices that raising the level on PostgreSQL converts silent loss into visible errors, so the
  repeat loop becomes part of the design rather than an optimisation
- Asks what evidence would survive for the finance team six months later

## Weak signals

- Blames caching
- Proposes re-reading the balance immediately before the write, with no lock
- Answers with the name of a level and nothing about what that level permits
- Guards the section with a lock inside one application process

## Answer bands

### weak

- Says the two requests collided, without saying where or when.
- Proposes reading the balance again just before writing it.
- Blames a cache.

### junior

- Draws the two timelines and points at the moment the second read happened.
- Moves the addition into one statement so the database applies it to whatever is there.

### mid

- Says why both commits were legal, in terms of what is permitted rather than by naming a level.
- Picks a fix and separates what the store guarantees from what the application must handle.
- Says what the loser of the race sees, and what the caller is told.

### senior

- Distinguishes the engines: names one where the second writer is refused and one where the write
  is silently lost.
- Costs a held lock on a busy row against a conditional write with a repeat, at a stated rate.
- Questions whether a stored total is the right shape, and says what moving away would take.

## Follow-ups

- This wallet belongs to a marketplace seller and takes forty top-ups a second. Does your fix
  still hold up?
  probes: contention on one busy row, waiter queues, and whether they reach for a different shape
- The two requests arrive at two different instances of the service. Does that change anything you
  just said?
  probes: whether the rule lives in the store or in one process
- Run the same code against a different engine and the second write is refused instead of quietly
  winning. What has to change in the caller?
  probes: the retry the application now owns, and engine-specific behaviour
- Finance ask, six months later, when the 50 went missing and why. What can you tell them?
  probes: whether a stored total leaves any evidence at all

## Sources

- https://www.postgresql.org/docs/current/transaction-iso.html
- https://dev.mysql.com/doc/refman/8.0/en/innodb-transaction-isolation-levels.html
- https://dev.mysql.com/doc/refman/8.0/en/innodb-consistent-read.html
- https://dev.mysql.com/doc/refman/8.0/en/innodb-locking-reads.html

## Notes

Ask for the anomaly, not the label. A candidate who says "read committed" and stops has said
nothing; push for what the level lets happen to these two requests.

Engine pins, and they matter here more than anywhere:

- PostgreSQL defaults to read committed, which permits this. At repeatable read PostgreSQL does
  *not* permit it: the second transaction to update the same row is aborted with "could not
  serialize access due to concurrent update". The anomaly is traded for an error the caller has
  to handle.
- MySQL/InnoDB defaults to repeatable read, and that name means something different there. A
  plain `SELECT` reads a consistent snapshot; `UPDATE`, `DELETE` and `SELECT ... FOR UPDATE` read
  the latest committed row and lock it. So read-then-write with a value computed in the
  application can still lose an update at InnoDB's repeatable read.
- The SQL standard's definition matches neither engine exactly, so treat "repeatable read
  prevents lost updates" as a claim that needs an engine attached.

The fixes in rough order of how often they are right: a single `UPDATE ... SET balance = balance +
50`; `SELECT ... FOR UPDATE` then update; a version column with a conditional update and a repeat;
an append-only ledger with the balance derived or maintained by trigger. The last is the answer
most likely to be right for money and least likely to be offered.
