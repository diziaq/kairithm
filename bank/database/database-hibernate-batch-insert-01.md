---
id: database-hibernate-batch-insert-01
schema_version: 1
title: Forty thousand rows, forty thousand inserts
category: database
topic: hibernate
level: senior
tags: [performance, operations, transactions, failure-modes]
time_estimate_min: 10
order: 420
---

## Ask

A nightly import writes forty thousand rows through a repository in one loop. Batching is on in
the configuration, but the statement log shows forty thousand separate inserts, the job takes
twenty minutes, and heap use climbs the whole way through. What is stopping the batching, and
what else is wrong with that loop?

## Tests

Whether the candidate can explain why a configured batch size does not produce batches, and sees
that a long-running write loop has a second problem that has nothing to do with statements.

## Listen for

- Rows cannot be grouped if each insert has to come straight back with the key it was given, so
  how the key is produced is the lever, not the batch size setting
- Nothing is being released, so every written object stays under watch for the length of the job,
  and each check at the end of a unit of work walks the whole pile
- The shape of the fix: a chunk at a time, pushing the work out and dropping the watched objects,
  with the chunk lined up against the batch size
- Asks whether this job should be going through the mapping layer at all, or through a bulk load
- Says how they would prove it: count the statements, not the seconds
- Knows that interleaving two kinds of rows breaks a run of identical statements unless they are
  grouped first

## Expected knowledge

- That a driver can carry several statements to the server in one round trip
- The two ways a key arrives: the database hands it back on insert, or the application takes a
  block of them from a sequence up front
- That the version in use matters here; this is one of the areas Hibernate has changed

## Strong signals

- Names the block-of-keys option and pre-empts the objection: the numbers will have gaps, and
  gaps cost nothing
- Says a chunk that is committed is not a job that can be rerun blindly, and asks what happens on
  the second run
- Wants the statement count in the job's own log, so the regression is visible next quarter
- Asks whether rows already present should be updated, because that turns every insert into a
  read first

## Weak signals

- Raises the heap
- Runs the same loop on four threads
- Re-reads the documentation, confirms the property is set, and stops there
- Blames the network or the database server
- Wraps the whole job in one transaction and calls that the batching fix

## Answer bands

### weak

- Raises the heap or the timeout and calls it done.
- Says the property is set, so batching must already be happening.
- Cannot connect the climbing heap to anything the loop is doing.

### mid

- Connects the per-row trip for the key to the inserts not grouping.
- Says nothing lets go of the written objects, so memory grows with the row count.
- Writes in chunks and clears as it goes.

### senior

- Picks how the key is produced from what this job needs, and says what that costs elsewhere.
- Sizes the chunk against the batch size and says what is in the table if row eighteen thousand
  fails.
- Explains that the check at each boundary gets slower as the watched pile grows, so the job
  decays rather than being uniformly slow.
- Proves the change by counting statements rather than timing one warm run.

### lead

- Asks whether a job of this shape belongs behind the mapping layer at all, and prices the
  alternative including who owns it.
- Says what gets measured nightly so the next regression is caught before a user reports it.
- Weighs a rerunnable job against a single atomic one and picks on what the business does when
  the import is half done.

## Follow-ups

- You change how the key is handed out and the numbers in the column now jump. The product owner
  says the numbers appear on an invoice. What do you tell them?
  probes: gaps are harmless for a surrogate; a business-visible number is a different column
- Row eighteen thousand breaks a constraint. What is in the table when the job stops, and what
  does the operator do at seven the next morning?
  probes: partial work across chunks, and whether a rerun is safe
- A colleague says it went from twenty minutes to four, so it is fixed. What do you want to see?
  probes: counting statements on production-shaped data rather than timing one run
- The same loop also reads a row for each record before writing it. Does your fix touch that?
  probes: whether they separate the write problem from the reads the loop is also issuing

## Sources

- https://docs.jboss.org/hibernate/orm/6.4/userguide/html_single/Hibernate_User_Guide.html#batch
- https://docs.jboss.org/hibernate/orm/6.4/userguide/html_single/Hibernate_User_Guide.html#identifiers-generators

## Notes

The mechanism: with a database-generated key returned per insert, Hibernate has historically had
to execute each insert on its own to learn the key, so `hibernate.jdbc.batch_size` has no effect
on those inserts. A sequence with an allocation block lets the ids be known before the flush, so
the inserts group. The second half of the card is the persistence context: without a periodic
flush and clear, every entity stays managed, memory grows, and each flush does more work than the
last.

NEEDS-REVIEW — unverified claim about which Hibernate 6.x version relaxed the identity-key
restriction. Recent 6.x releases can batch inserts for identity-generated keys where the JDBC
driver supports returning generated keys for a batch; do not state a specific version number to a
candidate. If they say "that changed in a recent version", treat it as a strong signal and ask
which driver they were on.
