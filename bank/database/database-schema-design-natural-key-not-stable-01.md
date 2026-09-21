---
id: database-schema-design-natural-key-not-stable-01
schema_version: 2
title: The email address is the primary key, and it just changed
category: database
topic: schema-design
level: senior
tags: [data-modelling, api-design, maintainability]
time_estimate_min: 9
order: 121
links:
  deeper: [database-schema-design-soft-delete-policy-01]
---

## Ask

A `users` table uses the email address as its primary key, and eleven tables reference it. Support
has two tickets open: a user who changed their address, and two colleagues who shared one address
and now need an account each. A developer proposes declaring the references `ON UPDATE CASCADE`.
What do you say?

## Tests

Whether the candidate can separate a stable identity from an attribute that merely happens to be
unique today, and reason about what changing a key costs once it has spread through a schema and
out of the database.

## Ideal minimal answer

The cascade does rewrite all eleven tables in one transaction, but it cannot reach the copies
outside the database — logs, exports, caches, another team's store, a bookmarked URL. Add an
internal identifier that never changes, backfill, move the references one at a time and keep
both live for a while; the shared mailbox ticket says the address was never a valid identity in
the first place.

## Listen for

- An identifier has to be unique, present, and never change value; an address fails the last of
  those and, in practice, the first — shared mailboxes, aliases, recycled addresses
- The cascade does make the update succeed, and rewrites eleven tables in one go; anything holding
  the old value outside the database is untouched — logs, caches, exports, a URL somebody
  bookmarked, another team's store
- Proposes an internal identifier that never changes, with the address kept as an attribute that
  may change and may carry a uniqueness rule
- Asks whether uniqueness on the address is even a business rule, and what "the same address"
  means once case and normalisation are considered
- Reads the second ticket as evidence the model is wrong, not as a support problem

## Expected knowledge

- The difference between the key a row is identified by and a uniqueness rule on an attribute
- A cascading update rewrites every referencing row in the same transaction

## Strong signals

- Knows the uniqueness rule depends on collation, and that the engines differ — MySQL's default
  collation compares case-insensitively, PostgreSQL's does not
- Talks about identity that has left the database: an id in a link, in a published event, in
  another team's table
- Keeps the old address as a historical row rather than overwriting it, because somebody will ask
  which address a message was sent to

## Weak signals

- Accepts the cascade because the engine offers it
- Says "always use a surrogate key" with no account of the eleven tables or how to get there
- Treats the shared mailbox as user error and closes the ticket

## Answer bands

### weak

- Says the cascade handles the first ticket and closes both.
- Proposes creating a second account by hand and copying the rows across.
- Does not distinguish the identifier from the attribute at all.

### mid

- Says the key changes value, which a key should not, and that every reference has to move with it.
- Proposes an internal identifier and a uniqueness rule on the address instead.

### senior

- Works out what the cascade actually rewrites, and names the places it cannot reach.
- Sequences the migration: add the column, backfill, move the references one at a time, swap the
  key, keep both live for a while.
- Asks what the business rule on the address really is before making it unique at all.
- Says what the second ticket implies about rows already in the table.

### lead

- Orders the eleven references by what breaks first and says which steps are reversible.
- Names what the team should now look for elsewhere in the schema, and how the next one gets
  caught while it is still cheap.
- Weighs leaving it and paying per ticket against paying for the migration, and attaches a rough
  number to each.

## Follow-ups

- The update runs and completes. A week later a report still shows the old address against last
  month's orders. Is that a bug?
  probes: a frozen record versus a live reference; whether every occurrence is a reference at all
- Two of the eleven tables belong to another team's service, which has also copied the value into
  its own store. How does that change the plan?
  probes: identity crossing a boundary, and the coordination cost that turns a schema change into
  a programme
- Somebody signs up again with the same address typed in capitals. Does your rule stop them?
  probes: whether uniqueness is defined precisely, and whether they know which behaviour their
  engine gives them

## Sources

- https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK
- https://dev.mysql.com/doc/refman/8.4/en/charset-mysql.html
- https://www.postgresql.org/docs/current/citext.html

## Notes

MySQL 8's default collation `utf8mb4_0900_ai_ci` is accent- and case-insensitive, so a uniqueness
rule on an address in MySQL already treats two spellings as the same row; PostgreSQL's default
collation does not, and the usual answers there are `citext` or a unique index on the lowercased
value. A candidate who states one of these as universal truth has only ever used one engine —
worth noting, not worth penalising on its own.
