---
id: java-collections-large-lookup-table-01
schema_version: 2
title: Forty million quotes and three proposals
category: java
topic: collections
level: lead
tags: [memory, performance, api-design]
time_estimate_min: 10
order: 130
links:
  related: [java-performance-local-cache-proposal-01]
---

## Ask

A pricing service keeps a huge lookup table in a `HashMap<Long, Quote>`, rebuilt hourly and
read-only in between. A heap dump says a third of the heap is the map's own structure, not the
quotes. The proposals: a primitive-keyed map from a library, two sorted arrays we search
ourselves, or a shared cache outside the process. How do you choose, and what is the team
signing up for?

## Tests

Whether the candidate establishes which constraints are actually binding before choosing, and can
name what each option costs the people who maintain it afterwards, rather than ranking the three
on lookup speed.

## Ideal minimal answer

Asks for the numbers the question withholds — rows, reads a second, heap, what the hourly
rebuild may cost — and puts the lookup behind one narrow interface first, so the choice is cheap
to get wrong. Names the standing cost of each option, a dependency somebody has to follow or
code only its author can read, and sets the bar it must clear on real data.

## Listen for

- Asks for the numbers the question withholds: how many rows, how many reads a second, how much
  heap there is, what the hourly rebuild is allowed to cost
- Asks what the reads look like before anything else: single keys or ranges, how the key is
  distributed, whether a miss is normal
- Says where the map's own bytes go — a boxed key and an entry object per row, plus the table
  slot, all of it per row and none of it proportional to the data
- Uses "never written between rebuilds" as the thing that rules options in: a structure built once
  and only read is a different problem from one changed in place
- The shared cache is a different shape of answer, not a faster one: a lookup becomes a call that
  can be slow, fail, or answer with something out of date, and every call site grows a path for that
- The hand-built arrays win on memory and lose on everything else: nothing prints them usefully in
  a debugger, the two have to be kept in step by hand, and the team owns the tests for the search
- Asks to measure the candidates on real data and a real key distribution before committing
- Wants the lookup behind one narrow interface so the structure can be changed later without
  touching callers

## Expected knowledge

- A boxed key is a separate object per row, and only a small range of values is shared
- A hash entry carries a header, a hash, references and a slot in the table on top of the value
- A sorted array gives a logarithmic search with no per-row object, at the cost of insertion

## Strong signals

- Asks what the service must do when the table cannot be built or cannot be reached at all, and
  lets that weigh on the choice
- Treats a new dependency as something to track, upgrade and eventually remove, and checks whether
  its types would spread through signatures across the codebase
- Says which measured result would make them leave the current map alone
- Notices that a heap this size is also a collector question and asks what the pauses look like
  today

## Weak signals

- Picks the fastest option in a published benchmark with no reference to this workload
- Writes the arrays because it is the most interesting piece of work on the table
- Treats moving the table out of the process as purely an infrastructure change
- Argues from the total size rather than from the per-row cost
- Prices all three proposals accurately and leaves the choice of which one to build to the team

## Answer bands

### mid

- Compares the three on memory and lookup cost and picks one.
- Says boxing and the per-row object are where the extra space goes.
- Does not raise what any of it does to the code around the structure.

### senior

- Uses the read-only window between rebuilds to rule options in and out.
- Says what moving the table out of the process does to every call site.
- Asks for the key distribution and a measurement on real data before choosing.
- Separates the cost of the hourly rebuild from the cost of a steady-state read.

### lead

- Puts the lookup behind one interface first, and says that this is what makes the choice cheap to
  get wrong.
- Names the standing cost of each option: a dependency somebody has to follow, or code only its
  author can read, with its own tests and no tooling behind it.
- Sets the bar the change has to clear, measured on production-shaped data, before any of the work
  is worth doing.
- Asks what the service does when the table is unavailable and lets the answer weigh on the choice.

## Follow-ups

- Six months in, the team wants to correct a few rows between rebuilds. What does that do to each
  of the three?
  probes: whether they kept the build-once-read-many property in view; the arrays stop being cheap

- The library is one line in the build file and it comes out ahead on every trial you run. What
  would still make you say no?
  probes: upgrade cadence, transitive weight, its types spreading through signatures

- A year later the person who wrote it has gone, and one id is coming back with the wrong row. How
  does the next person get to the bottom of that?
  probes: tooling and tests as part of the cost, not a footnote

## Notes

The figures, if the candidate asks — and a good one asks: forty million rows, six gigabytes of
heap with two of them the map's own structure, about a hundred thousand reads a second, and an
hourly rebuild that currently takes a couple of minutes. Hand them over one at a time rather than
reading them out, and note which ones they went looking for.

Rough arithmetic for the map: a boxed key, an entry object and a table slot come to something like
fifty bytes a row under a compressed heap, before the value. The order of magnitude is the point,
not the figure — a candidate who wants to measure it rather than accept it is answering well. The
card is not looking for a particular winner; the arrays are a defensible choice if the candidate
says what the team is signing up for.

Distinct from the in-process cache card, which shares the words but not the question: there the
structure is a partial, expiring copy of something authoritative elsewhere, and the subject is
staleness and what a wrong answer costs. Here the table is complete and correct by construction,
and the subject is which representation to pay for and who lives with it.

## Sources

- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Long.html#valueOf(long)
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/HashMap.html
- https://openjdk.org/projects/code-tools/jol/
