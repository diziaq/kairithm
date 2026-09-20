---
id: database-mybatis-placeholder-injection-01
schema_version: 1
title: Ninety lines of XML and a sort column from the URL
category: database
topic: mybatis
level: mid
tags: [correctness, security, maintainability, failure-modes]
time_estimate_min: 8
order: 430
---

## Ask

A search mapper builds its `where` clause from whichever filters the user filled in, binds the
values as `#{name}`, and ends with `order by ${sort} ${dir}`. The sort comes straight off the
query string. It works, it passes review, and the file is ninety lines. What do you flag, and
what do you do about the ninety lines?

## Tests

Whether the candidate knows the difference between a value the driver binds and text pasted into
the statement before it is sent, and has a position on hand-written SQL that has outgrown its
file.

## Listen for

- One form becomes a placeholder and the value travels beside the statement; the other is pasted
  into the text, so whatever came in is now part of the statement
- The pasted one is the hole, and a sort field taken off the query string walks straight into it
- The fix is not scrubbing the input: it is a fixed set of column names the application owns,
  with the request value used to look one up
- The bound form also lets the server reuse a plan, because the text stops changing per value
- Says where the pasted form is legitimate — a name the application chose — and never for a value
- On the ninety lines: pull the shared pieces out, or keep a smaller purpose-built statement per
  screen instead of one that serves them all

## Expected knowledge

- That a driver sends values apart from the statement text, and why that closes the hole
- Why an allow-list beats trying to clean input

## Strong signals

- Asks what else downstream treats that same request value as trusted
- Wants a test that demonstrates the hole, rather than a comment telling the next person not to
- Raises the plan reuse point without being prompted
- Notices that a filter that is sometimes absent changes the statement text too, and asks what
  that does to the server's cache of plans

## Weak signals

- Escapes quotes in the value and moves on
- "The framework takes care of that"
- Says nobody would send that, treating who calls the endpoint as the control
- Collapses the whole thing into one statement with `1=1` and a pile of conditions

## Answer bands

### weak

- Sees no difference between the two forms.
- Adds quote stripping and considers the matter closed.

### junior

- Says one form binds a value and the other drops text into the statement.
- Says user input reaching the second form is the problem.

### mid

- Restricts the sort to a fixed set of names the application owns, rather than cleaning input.
- Says why the same hole is not reachable through the bound filters.
- Breaks the ninety lines into shared pieces, or into one statement per screen, and says which
  and why.

### senior

- Says what the pasted form is actually for and keeps it for that, rather than banning it.
- Explains what each form does to the server's ability to reuse a plan.
- Asks what else treats that request value as safe, so the fix is not only local.
- Says how the rule survives review: a test or a build check, not a convention in a wiki.

## Follow-ups

- Your teammate keeps it as it is but strips quotes and semicolons from the value first. Talk me
  out of it, or talk me into it.
  probes: cleaning input versus a fixed set of names the application owns
- Product wants users to sort by any column on the screen, and the screen is configurable per
  tenant. Now what?
  probes: mapping a request token to an owned name, and where that map lives
- The file is ninety lines because six screens share it. Splitting gives six files that are
  eighty percent the same. Which way do you go, and what makes you change your mind later?
  probes: duplication against one conditional file nobody dares edit
- The same search runs fine for years and then the database starts planning it badly for one
  customer. What in this file would you look at first?
  probes: whether they connect the varying statement text to the server's plan cache

## Sources

- https://mybatis.org/mybatis-3/sqlmap-xml.html#String_Substitution
- https://mybatis.org/mybatis-3/dynamic-sql.html

## Notes

`#{}` becomes a `?` in a `PreparedStatement`; `${}` is string substitution done before the
statement is sent. The MyBatis documentation says outright that `${}` should not take user input.
The legitimate use is an identifier the application chooses — a table or column name — which is
exactly the case here, and exactly why an allow-list rather than a ban is the right answer.
