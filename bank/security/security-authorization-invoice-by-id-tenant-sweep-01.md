---
id: security-authorization-invoice-by-id-tenant-sweep-01
schema_version: 2
title: A pentest reads another customer's invoice
category: security
topic: authorization
level: senior
tags: [security, correctness, api-design, testing]
time_estimate_min: 10
order: 132
links:
  related: [database-schema-design-soft-delete-policy-01]
---

## Ask

`GET /invoices/{id}` returns whatever invoice that id names. It requires a valid token, and the
web app only ever links a customer to their own. A pentest report says one customer read another
customer's invoice. Where does the fix go?

## Tests

Whether the candidate puts the owner into the lookup rather than after it, and treats the finding
as a class of bug across the API rather than one endpoint.

## Ideal minimal answer

The owner has to be part of the lookup, not a comparison after it: the query asks for this id
belonging to this customer and comes back with nothing otherwise. Then say how the rest are found
— every route taking an id has the same hole unless something makes the owner impossible to leave
out.

## Listen for

- Says the token proving who is calling says nothing about which rows they may read
- Puts the owner into the query rather than comparing fields on a row that has already been loaded
- Decides what the caller is told when the row is not theirs, and says why that choice
- Treats it as a class rather than a bug: names the other routes taking an id, and how they get
  swept
- Names something that makes the next one safe without anybody remembering — a repository that
  will not build the query without the owner, a filter bound to the session, a row policy in the
  database
- Says the web app never linking to it is not a control

## Expected knowledge

- A token says who is calling, not which rows belong to them
- A predicate in a query is applied by the database on every call that uses it

## Strong signals

- Asks whether the id being hard to guess was ever doing any work here
- Distinguishes "not found" from "not allowed" by what each tells an attacker, and chooses
  deliberately
- Wants a test that asks for somebody else's id and expects nothing back, on every route
- Asks who else reads that table — a report, an export, a nightly job — because they have the same
  question to answer
- Asks what the pentest found by accident versus what else is probably there

## Weak signals

- Replaces the ids with random ones and calls it fixed
- Adds one comparison in one service method and moves on
- Says the user interface does not offer the link
- Lists the layers the check could live in and will not choose one
- Recounts a past pentest without saying what happens to this report

## Answer bands

### mid

- Says any caller with a valid token can read any invoice today.
- Adds a check on the server that the invoice belongs to the caller.

### senior

- Puts the owner into the lookup so a row belonging to somebody else never comes back.
- Raises the other routes with the same shape without being asked, and says how they are found.
- Chooses what the caller is told when the row is not theirs, and says why.

### lead

- Picks a mechanism that makes the next route safe by default, and says what it costs to live with.
- Says what changes in review and in the test suite so this does not come back.
- Decides what is said to the customers whose invoices may already have been read.
- Says what gets fixed today and what gets fixed properly.

## Follow-ups

- Somebody suggests random ids instead of counting ones. Does that close it?
  probes: guessability standing in for a missing check
- There are forty routes that take an id. What do you do about them?
  probes: whether they treat it as a class and can describe a sweep
- You have to choose between answering "not found" and "not allowed". Which, and why?
  probes: what the reply tells an attacker, and making the choice on purpose
- A month later a new route ships with the same bug. What failed?
  probes: whether their fix was a one-off or changed the default

## Sources

- https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/
- https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- https://www.postgresql.org/docs/current/ddl-rowsecurity.html

## Notes

Broken access control is A01 in the OWASP Top 10 2025, where the project reports finding some form
of it in every application it tested. The 2025 edition also folded server-side request forgery
into A01, so the category is broader than it was in 2021 — do not quote the older numbering at a
candidate.

Two answers look similar and are not. A comparison after the load — fetch the invoice, then check
its customer against the caller's — is correct as written and fails the moment somebody writes a
new route and forgets, or a code path returns early, or a second query is added for a report. The
owner inside the lookup cannot be forgotten by that route, and mechanisms that carry it
automatically (a repository that refuses to build the query without it, a session-scoped filter,
or PostgreSQL row-level security with the tenant set per connection) cannot be forgotten by the
next route either. Any of the three is a good answer; not distinguishing them from the `if` is not.

Row-level security is worth naming, with its cost: the policy is enforced by PostgreSQL on every
statement including ones nobody reviewed, but it depends on the connection carrying the right
identity, which pooled connections make easy to get wrong. A candidate who names it and also names
that risk is at the top of the band.
