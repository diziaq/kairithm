---
id: database-transactions-write-skew-on-call-rota-01
schema_version: 2
title: Both engineers went off call and the rota emptied
category: database
topic: transactions
level: senior
tags: [transactions, correctness, concurrency, failure-modes]
time_estimate_min: 12
order: 610
links:
  shallower: [database-transactions-lost-update-wallet-01]
  related: [java-concurrency-lock-ordering-transfer-01]
---

## Ask

Two on-call engineers, in different tabs at the same second, each check the rule that at least one
person must stay on call. Each sees two active and sets their own row inactive. Both commit, no
error, and the rota is empty. This PostgreSQL database was raised to repeatable read a month ago
to stop exactly this. Why did it not?

## Tests

Whether the candidate can tell two writes to one row apart from two writes to a shared condition,
and then choose a mechanism that makes the second kind collide instead of hoping an isolation
level covers it.

## Ideal minimal answer

The two transactions wrote different rows, so nothing collided; each decided from a snapshot that
stopped describing the table the moment the other committed. Repeatable read refuses a second
writer of the same row and says nothing about a shared condition. Fix it with a row both must
write — a count with a check — or run serializable and repeat on a 40001.

## Listen for

- Walks the interleaving: both snapshots are taken before either write, both see two active, and
  the two updates land on different rows so neither is in the other's way
- Says this is not the anomaly the earlier card was about — nothing was overwritten, and no write
  was lost; two correct-looking writes together broke a rule neither one could see
- Names the condition as the thing being contended, and points out that no row carries it, so
  there is nothing for the engine to conflict on
- Offers locking the rows the rule is computed from, and immediately says what that misses: a row
  arriving or changing into the set after the read
- Offers giving the rule a home — a row per rota holding the active count, with a check, updated
  by every transaction that changes membership — so two writers meet on one row
- Offers serializable, and says in the same breath that the caller now owns a repeat, because the
  conflict is reported at commit rather than prevented
- Asks how often this happens and what a failed attempt costs before picking

## Expected knowledge

- PostgreSQL's repeatable read aborts the second transaction to update a row another has already
  updated, and permits two transactions that touch disjoint rows
- Serializable in PostgreSQL watches for read-write dependencies between concurrent transactions
  and aborts one at commit; the error arrives with SQLSTATE 40001
- The locks that serializable takes to do this do not block, so they cannot deadlock, but they are
  promoted to coarser granularity as a transaction touches more rows

## Strong signals

- Says the isolation level was raised without anybody writing down which anomaly it was meant to
  stop, and treats that as the root cause of the surprise
- Asks whether the rule has to hold across the whole rota or only within a team, because the
  answer decides which row is the one both writers must touch
- Notes that serializable's watching gets coarser as transactions touch more rows, so the number
  of aborts is not proportional to the number of genuine conflicts
- Asks what a caller should see when its attempt loses, and treats it as a product decision
- Points out that a single-row check makes the rule enforceable by the store rather than reviewed
  by people

## Weak signals

- Names an isolation level and stops, with nothing about what that level permits
- Proposes reading the count again just before the write, without a lock
- Adds a lock inside one application process and calls the rule enforced
- Lists locking, a counter row and serializable with accurate trade-offs and will not choose
- Tells the story of a past incident with the same shape and never says what to do about this one

## Answer bands

### mid

- Draws the two timelines and says both decisions were made before either write landed.
- Says the two updates did not touch the same row, so the engine had nothing to complain about.
- Reaches for a lock, without saying what the lock covers or what it misses.

### senior

- Separates this from the case where one write overwrites another, and says why the earlier fix
  does not apply.
- Picks one of the three mechanisms unprompted and says what it costs and where it leaks.
- Says what the loser of the race is told, and who writes the code that handles it.
- Raises the row that arrives after both snapshots were taken, before being asked about it.

### lead

- Decides between the counter row and the stricter level from a stated rate and a stated cost of
  being wrong, not from taste.
- Says how the team finds the other rules in this codebase with the same shape.
- Puts the repeat loop somewhere every caller goes through, and says how it is tested.
- Says what changes for whoever is on call at three in the morning after the fix.

## Follow-ups

- Suppose the two of them had instead both edited the same person's entry. Would the database have
  behaved any differently?
  probes: whether they can say that same-row writers are refused and disjoint writers are not
- While those two are deciding, a third engineer is being added to the rota by a different
  request. Does your fix still hold?
  probes: a row that was in neither snapshot, and whether row locks can reach it at all
- You put the stricter level in. It runs forty times a minute and the team starts seeing failures
  where there were none before. What do you tell them to do?
  probes: whether the repeat loop was designed in, and what the caller is told meanwhile
- There is a second service here on a different engine, running at that engine's own default.
  Would you expect the same outcome there?
  probes: whether they treat the name of a level as engine-specific rather than a standard

## Sources

- https://www.postgresql.org/docs/current/transaction-iso.html
- https://www.postgresql.org/docs/current/applevel-consistency.html
- https://www.postgresql.org/docs/current/runtime-config-locks.html
- https://www.postgresql.org/docs/current/errcodes-appendix.html
- https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html

## Notes

This is the companion to the wallet card, and the pair is the point. There, two transactions write
the *same* row and PostgreSQL's repeatable read refuses the second one. Here they write
*different* rows against a condition neither snapshot saw change, and repeatable read permits it.
A candidate who has only learned "raise the level" will assume the first result covers the second.

Engine pins:

- PostgreSQL's manual states that repeatable read "prevents all of the phenomena described in
  Table 13.1 except for serialization anomalies", and that the view a transaction sees "will not
  necessarily always be consistent with some serial execution". This is that case.
- The manual's own worked example is two serializable transactions summing disjoint classes in
  `mytab` and each inserting into the other's class: "If either transaction were running at the
  Repeatable Read isolation level, both would be allowed to commit."
- Serialization failures "always return with an SQLSTATE value of `40001`", and the manual says an
  environment using serializable must have a generalised way of handling them.
- MySQL/InnoDB's repeatable read also permits this. Gap locks apply to locking reads; a plain
  `SELECT` is an MVCC snapshot. Do not let a candidate claim InnoDB is safe here because its
  default level has the same name as PostgreSQL's stricter one.

Figures to release when asked, and credit the asking:

- The rota table holds about 40 rows; the rule is checked with a `SELECT count(*)` and then an
  `UPDATE` of one row, in one transaction, from a Spring service.
- It has happened twice in a year, and both times somebody noticed because a page went unanswered.
- The team has no repeat-on-failure code anywhere.

On the three mechanisms:

- `SELECT ... FOR UPDATE` over the rows the count was taken from works only while the set of rows
  is fixed. An insert that joins the set afterwards is not locked by it.
- A counter row with `CHECK (active_count >= 1)` turns the shared condition into a real write-write
  conflict and lets the store refuse it. This is usually the right answer and is the one least
  often offered.
- Serializable is correct and is the smallest code change, but PostgreSQL promotes its predicate
  locks to page and then relation granularity as a transaction touches more rows —
  `max_pred_locks_per_page` defaults to 2 — so the abort rate is not proportional to the number of
  real conflicts. Worth releasing to a candidate who picks it without naming a cost.
