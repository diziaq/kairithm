---
id: database-cloud-databases-profile-saves-then-reverts-01
schema_version: 2
title: Rows deleted yesterday at 14:00, and nobody has ever run a restore
category: database
topic: cloud-databases
level: mid
tags: [operations, failure-modes, testing, ownership]
time_estimate_min: 8
order: 340
links:
  deeper: [database-cloud-databases-aurora-failover-four-hour-outage-01]
  related: [general-incidents-first-fifteen-minutes-01]
---

## Ask

Your service runs on Amazon RDS for PostgreSQL. Automated backups run nightly, retention is seven
days, point-in-time recovery is switched on. Yesterday at 14:00 somebody deleted the rows of one
table in production, and you found out this morning. Walk me through getting them back, and tell
me what you want to know before you start.

## Tests

Whether the candidate can turn a switched-on managed feature into a plan somebody could actually
execute: what the restore produces, how much of the database it covers, how long it runs, and who
has agreed what may be lost.

## Ideal minimal answer

Point-in-time recovery brings up a new RDS instance with the whole database as it was just
before 14:00, so the rows must be copied from it into the live one; cutting production over
would lose a day of every other table. The wait is set by the size of the whole database, and
nobody has run a restore, so we time one to find out.

## Listen for

- Asks what was deleted before touching anything: which table, how many rows, and what has been
  written to it since 14:00
- Knows the restore builds a separate instance and leaves the live one alone, so production keeps
  running while it happens
- Says the recovery takes the whole database back to a moment, not the one damaged table, so the
  rows have to be pulled out of the new instance and put back into the live one
- Names a moment just before the delete rather than "yesterday", and asks how that moment will be
  established
- Points out that the new instance is a day behind for every other table too, so swapping
  production over to it throws away everything written since
- Separates how much may be lost from how long the service may be unavailable, and asks who has
  agreed both figures
- Treats seven days as how far back you are allowed to go, not how quickly you get back
- Answers "how long will this take" with "nobody here has run one, and the honest thing is to
  find out on a copy"
- Asks who is allowed to start a restore at all, and whether that person is awake

## Expected knowledge

- A managed restore to a moment creates a new instance; the source is never rewound in place
- What can be recovered is bounded by the retention window, and the most recent moment available
  trails the present

## Strong signals

- Wants the recovered rows captured somewhere before anyone else touches production
- Asks what downstream already acted on the rows being gone — an export, a report, a queue
- Notices the size of the database, not the size of the damaged table, is what sets the wait
- Suggests running the whole sequence once on a copy so the next incident has a known duration
- Asks how the delete happened at all, and whether the same account can do it again this afternoon

## Weak signals

- "We have backups" as the entire answer, with nothing about what a restore hands you
- Expects the one table to come back inside the running database
- Reads the retention setting as an answer to how long the recovery will take
- Plans to point the application at the new instance without a word about the day of writes on the
  old one

## Answer bands

### weak

- Says backups are enabled so the rows will be back, without saying what a restore produces.
- Expects to put the single table back into the database that is running now.
- Reads seven days as the time the recovery will take.

### junior

- Says a new instance comes up beside the live one and the live one is untouched.
- Picks a moment just before the delete rather than a whole day back.
- Asks how many rows went and what has been written to that table since.

### mid

- Says the whole database comes back at that moment, so the rows must be copied from the new
  instance into the live one.
- Points out the new instance is stale for every other table, so cutting over loses a day of work.
- Asks how big the database is, because that is what the wait depends on.
- Says, once asked for a number, that nobody knows how long it runs because nobody has done it,
  and proposes timing one.

### senior

- Separates the moment recovered to from the length of the interruption, and asks who signed up
  for each number.
- Names what the new instance does not inherit — its own endpoint name, the default parameter and
  security settings — and what that means for pointing anything at it.
- Writes the sequence down so somebody else can run it at 03:00 without them.
- Raises unasked what would be different if this had been found on day nine instead, or if a
  column had been dropped rather than rows deleted.

## Follow-ups

- The damaged table holds 40 GB. The whole database holds two terabytes. Does that change your
  plan?
  probes: that the wait is set by the size of the whole thing, not the damaged part
- While you work on this, orders keep arriving and landing in the same database. What happens to
  them?
  probes: that the copy is frozen at a moment and the day since has to survive the fix
- Before you begin, your manager asks when the data will be back. What do you tell them?
  probes: whether they admit the number is unknown and offer to find it, or invent one
- The same thing happens again, but this time it comes to light nine days later. What have you
  got?
  probes: the hard edge of the retention window, and whether anything colder was ever arranged

## Notes

Figures to release when asked, and credit the candidate who asks: the database is roughly 900 GB
on a db.m6g.xlarge; the table held about 2.4 million rows and is written to all day; the delete
ran with a `WHERE` clause that matched every row; writes to every other table have continued
normally since; there is no snapshot outside the seven days; nobody currently on the team has
performed a restore.

Provider pins, documented and worth crediting:

- RDS point-in-time recovery creates a **new** DB instance and does not modify the source. There is
  no in-place rewind and no single-table restore: an automated backup is a snapshot of the whole
  instance, "backing up the entire DB instance and not just individual databases".
- Transaction logs are uploaded to S3 every five minutes, so the latest restorable time trails the
  present. Within the retention window any point can be chosen.
- A restored instance comes up with the default parameter and option groups unless others are
  named in the call, and with a security group that has to be chosen — it is not a clone of the
  source's configuration.
- After the new instance reports available, its volumes go on loading blocks from S3 in the
  background, so it is fully usable but slower until that finishes. A candidate who expects the
  copy to be immediately as fast as production is in for a surprise.
- Restore duration is not published as a figure; it depends on the volume, and the only honest way
  to know it for this database is to run one.

Getting one table across afterwards is ordinary PostgreSQL work — `pg_dump --table`, or a query
against the restored instance — and is worth hearing but is not the interesting part of the
answer.

This card is the `mid` step below the Aurora failover card in the same topic: this one is a
planned recovery the team controls, that one is an unplanned one it does not.

## Sources

- https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_PIT.html
- https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_WorkingWithAutomatedBackups.html
- https://www.postgresql.org/docs/current/app-pgdump.html
