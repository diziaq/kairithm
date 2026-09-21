---
id: general-requirements-one-line-ticket-01
schema_version: 2
title: The ticket says "add CSV export" and nothing else
category: general
topic: requirements
level: junior
tags: [api-design, data-modelling, collaboration]
time_estimate_min: 6
order: 60
links:
  deeper: [general-requirements-instant-and-always-current-01]
---

## Ask

The ticket says "add CSV export to the orders page" and nothing else. The person who wrote it is
away for a week. What do you do?

## Tests

Whether the candidate can surface the unknowns that would change the implementation, and still
make progress rather than stalling or guessing silently.

## Ideal minimal answer

Lists the decisions the ticket leaves open — which rows, which columns, who opens the file —
finds somebody else who can answer some of them, and writes the assumptions into the ticket
before starting, rather than guessing quietly or waiting a week.

## Listen for

- Asks which orders: what is on the screen, what the filter selects, or everything
- Asks which columns, and whether anything on that page should not leave the system
- Asks who opens the file and in what — the answer changes separators, encoding and date format
- Notices that "everything" might be two million rows, and asks what happens then
- Writes the assumptions down and shares them rather than keeping them in their head
- Finds someone else to ask — support, the person who requested it, whoever uses the page daily
- Ships something small and checkable rather than guessing at the full thing

## Weak signals

- Builds whatever seems reasonable and says nothing
- Blocks for a week waiting for the author to return
- Asks twenty questions at once with no proposal of their own
- Never considers the size of the export or who is allowed to see the data

## Answer bands

### weak

- Starts coding immediately with no questions.
- Waits for the author and does nothing in the meantime.
- Cannot name a single decision the ticket leaves open.

### junior

- Lists the questions that would change what they build: which rows, which columns, who uses it.
- Finds another person who can answer some of them.
- States assumptions in the ticket before starting.

### mid

- Proposes a specific default for each unknown rather than only asking, so the answer is a yes
  or no.
- Raises the cases the requester has not thought about: a very large export, a customer whose
  data should not appear, a field that breaks in a spreadsheet.
- Builds the smallest version that can be put in front of a real user and refined.
- Checks whether something nearby already solves it.

## Follow-ups

- Somebody exports two million rows on the first morning. What did you wish you had asked?
  probes: whether size and time were ever treated as part of the requirement
- The file you produce opens on the requester's machine with the dates in the wrong order and
  one column mangled. Whose problem is that?
  probes: whether the real requirement is the file or what the person does with it afterwards
- You cannot reach anybody who can decide, and the work is due Friday. What ships?
  probes: making a defensible choice visible, rather than a silent guess or a stall
