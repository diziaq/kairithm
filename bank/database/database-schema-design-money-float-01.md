---
id: database-schema-design-money-float-01
schema_version: 1
title: The monthly total is a few cents out, every month
category: database
topic: schema-design
level: mid
tags: [correctness, data-modelling, operations]
time_estimate_min: 7
order: 120
links:
  deeper: [database-schema-design-natural-key-not-stable-01]
---

## Ask

Payments are stored in a column declared `amount double precision`. Finance reports the monthly
total is out against the ledger by a few cents, every month, sometimes high and sometimes low. A
developer says the rounding creeps in when the report renders and wants to round on display. Do
you agree?

## Tests

Whether the candidate knows a binary floating point column cannot hold an ordinary decimal amount,
and can say where the error is introduced rather than where it is noticed.

## Listen for

- Values like 0.10 and 0.01 have no exact binary form, so what is stored is already not the amount
  that was charged
- Rounding at the edge tidies one row and does nothing to the sum of a million of them; the error
  is inside the stored data
- Names the right column: an exact decimal type (`numeric` in PostgreSQL, `DECIMAL` in MySQL) with
  a declared scale, or an integer count of minor units
- Says what else this breaks — equality tests against an amount, grouping by one, a balance that
  will not come out at zero
- Asks whether the currency travels with the amount, and what scale the currencies in play need

## Expected knowledge

- Binary floating point is inexact for ordinary decimal fractions
- An exact decimal type costs more per operation and is what money is stored in anyway

## Strong signals

- Asks which way the business rounds and whether anybody has written that down
- Knows adding the same values in a different order can give a different result, so two reports
  that are both "correct" disagree
- Says the migration is the hard part: the column already lost information, so the correction has
  to be agreed with finance rather than applied quietly

## Weak signals

- "Round to two decimals" as the entire fix
- Compares amounts with a tolerance and leaves the column alone
- Argues the error is too small to matter, without asking how many rows get added up

## Answer bands

### weak

- Agrees with rounding at the edge and expects the monthly figure to line up afterwards.
- Says an error that size cannot matter.
- Treats it as a reporting defect and hands it to the reporting team.

### junior

- Says that column type cannot hold an exact amount and names an exact type to replace it.
- Places the error in the stored data rather than in the report.

### mid

- Explains how a tiny repeated error accumulates over a sum and can land either side.
- Chooses between an exact decimal type and minor units and says what each costs to read, write
  and work with in the application.
- Notices that changing the column does nothing for the rows already written.

### senior

- Plans the change: the correction rule, who approves it, and what the report shows for the period
  that straddles it.
- Asks for the currencies and the scale before choosing a type, instead of assuming two decimals.
- Names which totals have to reconcile against which system, and how that is asserted after the
  change rather than noticed by finance again.

## Follow-ups

- The same report is run twice over the same rows and the two figures differ by a cent. Nothing
  was written in between. How?
  probes: order-dependent summation of inexact values, and whether they tie it to the same root
  cause
- A third of the rows are in Japanese yen. Does your choice still hold?
  probes: scale, and whether the amount carries its unit with it
- You change the column next sprint. What do you tell finance about the figures they have already
  signed off?
  probes: whether the migration includes a correction story and an owner, not only a statement
  that alters the table

## Sources

- https://www.postgresql.org/docs/current/datatype-numeric.html
- https://dev.mysql.com/doc/refman/8.4/en/problems-with-float.html

## Notes

Both engines' manuals say this outright: PostgreSQL warns that floating point comparisons may not
work as expected and points at `numeric` for amounts where exactness matters, and MySQL has a page
devoted to the same surprise. A candidate who has hit it in production usually reaches for minor
units first; one who has read about it reaches for the decimal type. Either is fine — the question
is whether they can say what happens to the existing rows.
