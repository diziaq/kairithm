---
id: database-relational-model-missing-foreign-key-01
schema_version: 2
title: Orders that point at a customer who is not there
category: database
topic: relational-model
level: junior
tags: [correctness, data-modelling, failure-modes]
time_estimate_min: 6
order: 110
links:
  deeper: [database-relational-model-denormalised-copy-01]
  related: [spring-web-layer-validation-missing-01]
---

## Ask

An `orders` table has a `customer_id` column and no foreign key — the team dropped it because
"the application always sets it correctly" and it was slowing deletes down. A year later the
monthly report crashes, and support finds orders whose customer does not exist. What happened, and
what would you change?

## Tests

Whether the candidate treats referential integrity as a rule the store enforces against every
writer, rather than a convention the current version of the application happens to follow.

## Ideal minimal answer

Nothing in the database was told that `customer_id` refers to `customers`, so no writer was ever
stopped — and the application is not the only writer: a migration, a bulk import or a console
session can all put an order there. Declare the foreign key, but the broken rows already exist,
so they have to be dealt with before it will go on.

## Listen for

- Names writers that are not the running application: a migration, a bulk import, a console
  session, an older release still deployed, a restored backup, a plain bug
- Says what the key does at write time — refuses a child row pointing at nothing, and refuses to
  remove a parent that still has children unless a different action is declared
- Realises the broken rows already exist, so adding the key fails until somebody decides what they
  mean
- Asks what should happen when a customer really is removed: refuse, blank the column, or remove
  the orders too, and which one the business wants
- Points out the crash is late evidence; joins had been silently dropping those orders for months

## Expected knowledge

- A foreign key is checked on insert, on update and on delete
- The engine matters: MySQL parses and ignores the declaration on storage engines that do not
  support it, so the syntax being present is not the same as the rule being enforced

## Strong signals

- Asks how many broken rows there are before proposing anything
- Separates "the orders are worthless" from "we lost the customer record" — the second one is a
  different incident
- Notices the reason the key was dropped is a real cost and states it honestly rather than
  dismissing it

## Weak signals

- Says the application has a bug and stops, leaving the table as it is
- Proposes the report skip rows it cannot resolve
- Wants a nightly job that hunts for broken rows and deletes them

## Answer bands

### weak

- Blames the application and proposes no change to the table.
- Suggests the report ignore the rows it cannot join.
- Cannot name anything other than the application that writes to the table.

### junior

- Says the database was never told the column refers to another table, so nothing rejected the row.
- Names at least one writer outside the normal application path.
- Proposes declaring the key, and expects the rows already there to need handling first.

### mid

- States what the key rejects on write and what it does when a parent is removed, and picks the
  behaviour from what the business wants rather than from the default.
- Sequences the work: find the broken rows, decide what they mean, then declare the key.
- Weighs the cost the team originally complained about against the cost they have now paid.

## Follow-ups

- You run the statement to add it and it fails on the spot. What do you do with the rows it is
  objecting to?
  probes: that the rule is checked against data already on disk, and that orphans need a business
  decision rather than a delete
- A customer asks to be removed entirely. What happens to their orders now?
  probes: whether they see the rule forces the question to be answered, and can name the choices
- The same team wants to point a new table at `orders` and says they will keep it right in code.
  What do you tell them?
  probes: whether the lesson generalises, and whether they can state the cost of the rule fairly

## Sources

- https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-FK
- https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html

## Notes

Do not let the candidate turn this into a recitation of the cascade options. The question is what
a rule enforced by the store buys that a rule enforced by one application does not, and that the
answer needs a decision about the existing rows.

MySQL accepts `FOREIGN KEY` clauses on engines that do not implement them and silently ignores
them; the reference manual linked above is explicit about this.
