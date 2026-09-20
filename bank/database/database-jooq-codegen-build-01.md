---
id: database-jooq-codegen-build-01
schema_version: 1
title: The new hire cannot build the repo
category: database
topic: jooq
level: mid
tags: [operations, testing, maintainability, failure-modes]
time_estimate_min: 8
order: 440
links:
  related: [database-mybatis-placeholder-injection-01]
---

## Ask

A new hire cannot build the repo: the jOOQ generator wants a database and there is not one on
their laptop. CI hits the same wall about twice a week. Someone proposes committing the generated
classes to the repo and running the generator by hand when the schema changes. Talk me through
that proposal.

## Tests

Whether the candidate understands where the schema comes from in a generated data access layer,
and can weigh a committed copy of generated output against a build that stands on its own.

## Listen for

- The generator has to read a schema, and the real question is which one: a shared server, or one
  built from the scripts already in the repo
- Names the actual fault — the build depends on a machine and on whoever last changed it — rather
  than treating the new hire's laptop as the problem
- Describes the self-contained route: bring up an empty database inside the build, apply the
  project's own schema scripts, generate from that, throw it away
- If the classes are committed, something has to prove they still match, or a stale copy makes the
  compiler confirm a schema that no longer exists
- Says what each route costs in build time, and that the generated part can be cached or moved
  into a module of its own
- Says what the arrangement buys in the first place: a mismatch surfaces at compile time

## Expected knowledge

- That the generator reads a schema and emits classes the rest of the code compiles against
- That the project's own schema scripts describe the same thing the server does
- That a throwaway database can be started by the build itself

## Strong signals

- Points at the shared server as the flaky part of CI, and asks what else in the pipeline leans
  on it
- Wants local and CI doing the same thing, and says a local-only shortcut is worse than the
  original problem
- Will take the committed copy as well, provided the check that it matches runs on every build
- Asks how long the generated part actually takes before optimising it

## Weak signals

- Commits the classes with nothing checking that they match
- Says every developer should install the database and keep it current
- Turns the generator off for local builds only
- Treats the generated code as source to be edited when something does not fit

## Answer bands

### weak

- Tells the new hire to install a database and moves on.
- Sees the flaky CI as a separate problem from the build needing a server.

### junior

- Says the generator needs a schema to read and that is what is missing.
- Says committing the classes lets the build run without one.

### mid

- Builds the schema inside the build from the scripts in the repo, so no server is needed.
- Says a committed copy goes stale and needs something that proves it still matches.
- Weighs the added build time and offers caching or a module of its own.

### senior

- Names what the whole arrangement buys and refuses to trade it away for a faster build.
- Treats the shared server as the fault and asks what else depends on it.
- Keeps local and CI identical, and says why a local-only shortcut costs more than it saves.
- Says who regenerates, when, and what happens on a branch that changes the schema.

## Follow-ups

- You add the check that compares a fresh run against what is committed. It fails on a Friday for
  a change nobody made. Where do you look?
  probes: which inputs decide the output — server state, tool version, ordering of scripts
- The build is now four minutes longer for everyone, every time. What do you do?
  probes: caching, a module of its own, only rebuilding when the scripts change
- Two people change the schema on separate branches the same day. What happens when both merge?
  probes: ordering, and that the output follows whatever the two changes produce together
- Someone needs a view that only exists in production. How does it get into the build?
  probes: whether the repo is the source of truth, or the server quietly still is

## Sources

- https://www.jooq.org/doc/latest/manual/code-generation/
- https://www.jooq.org/doc/latest/manual/code-generation/codegen-ddl/

## Notes

The two self-contained routes are jOOQ's DDL-based generation straight from the scripts, and
starting a throwaway container, applying the migrations and generating from that. Either removes
the shared server. Committing the output is fine on its own terms — the mistake is committing it
with nothing verifying it. Candidates who have only ever pointed the generator at a shared
development database usually do not see the dependency until it is named.
