---
id: database-orm-choose-for-codebase-01
schema_version: 2
title: Forty tables, a dozen reports, two people who write SQL
category: database
topic: orm
level: senior
tags: [maintainability, performance, testing, data-modelling]
time_estimate_min: 10
order: 400
links:
  related: [database-mybatis-no-persistence-context-01, database-jooq-mixed-with-entities-01]
---

## Ask

You are picking the data access layer for a new billing service: about forty tables, twenty
screens that are plain create-and-edit work, and a dozen reporting queries with window functions
that a data analyst already wrote. Two of the six developers are comfortable in SQL. Argue for
one approach over the others, and tell me what you expect to regret in a year.

## Tests

Whether the candidate chooses a data access approach from the shape of the query surface and
from who will maintain it, rather than by habit, and can name the cost of their own choice.

## Ideal minimal answer

Pick one for this codebase and defend it against the runner-up: with only two of six comfortable
in SQL, say who writes and reviews the dozen reports, how someone gets from a slow page back to
the text the database actually ran, when a renamed column is caught — build, startup or 3am —
and which option needs a database running to test.

## Listen for

- Splits the surface in two: how much is row-by-id work that any mapping layer does well, and
  how much is bespoke reads that somebody has to write and tune by hand
- Asks who writes and reviews the SQL, and whether those are the same people who get paged
- Says what the route is from a slow query in the database log back to the line of code that
  produced it, and which option makes that route longer
- Treats a schema change as the interesting event: which option fails at build time, which at
  startup, which at three in the morning
- Says what a test costs under each: whether the thing under test can run without a database,
  and whether such a test would catch the failure they actually fear
- Will not leave the answer as a list of properties — commits to one for this codebase

## Expected knowledge

- That a mapping layer emits SQL nobody on the team wrote, and that emitted form is what the
  database plans and executes
- That a code generator reads a schema and hands you classes to compile against
- Roughly what each option needs in a test: a real database, an in-memory stand-in, or nothing

## Strong signals

- Asks to see the two or three worst reports before choosing anything
- Allows a different answer on the read path and the write path, and says where the line is
- Names the exit: what it would take to move off the choice in two years and what would be stuck
- Points out that the analyst's queries already exist, so one option is mostly transcription and
  another is a rewrite

## Weak signals

- Picks whatever the last project used, with no property of this codebase in the reason
- Claims the choice removes the need for anyone on the team to read SQL
- "It is all behind an interface, so we can swap it later"
- Treats the twenty plain screens as the hard part and the dozen reports as a detail

## Answer bands

### weak

- Names a favourite library and gives no property of this codebase as a reason.
- Says it can be swapped out later without saying what would be stuck.

### mid

- Separates the routine row work from the dozen bespoke reads and gives each a home.
- Says who on this team would be writing and reviewing the SQL under each option.
- Names at least one cost of the option they picked.

### senior

- Traces a slow query back to the code that produced it under each option and says which is
  harder, and why that matters at three in the morning.
- Says what each option does when a column is renamed under it, and when the team finds out.
- Prices the tests: which option needs a database running to prove anything.
- Picks one for this codebase and defends it against the runner-up.

### lead

- Says what it would take to reverse the decision in two years and which parts would not move.
- Draws the line if two approaches are to live side by side, and names who enforces it.
- Accounts for the six people who are actually here, not for an ideal team.

## Follow-ups

- A report page takes nine seconds. Walk me through how someone on your team gets from that page
  to the text the database actually ran.
  probes: whether the route from code to emitted SQL was part of the choice or an afterthought
- Next sprint somebody renames a column. Who finds out, and when?
  probes: build-time versus start-up versus run-time failure, per option
- Four of the six cannot write the kind of query you are proposing. What happens in month one?
  probes: whether the choice accounts for the team that exists

## Sources

- https://www.jooq.org/doc/latest/manual/getting-started/jooq-and-jpa/
- https://docs.jboss.org/hibernate/orm/6.4/userguide/html_single/Hibernate_User_Guide.html#fetching

## Notes

The card is about the argument, not the answer. Any of the three can be defended here; a
candidate who picks one and cannot say what they lose has not answered it. Push back on whichever
option they chose — the useful signal is whether they can state the runner-up's case fairly.
