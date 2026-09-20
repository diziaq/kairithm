---
id: sap-jco-function-calls-leading-zeros-01
schema_version: 1
title: The material exists but the call finds nothing
category: sap-jco
topic: function-calls
level: mid
tags: [correctness, data-formats, integration]
time_estimate_min: 6
order: 90
---

## Ask

You pass the material number 4711 to a function module that reads material data. Business users
see that material in SAP every day, but your call comes back empty and raises nothing. What do
you check?

## Tests

Whether the candidate knows that an RFC interface takes values in SAP's internal format, and can
recognise a silent empty result as a key-format problem rather than a missing record.

## Listen for

- What users see on screen is the external format; the interface takes the internal one, and for
  several key fields the two are not the same string
- For a material number that normally means left-padded with zeros to the field length, so 4711
  and 000000004711 are different keys
- Nothing raises an error because an unknown key legitimately returns no rows
- The same class of problem for dates, times, amounts with their currency decimals, unit and
  language keys
- How to settle it: run the function module on the SAP side with the exact value the Java code
  sends, not with the value a person would type

## Expected knowledge

- Key fields can have a conversion routine that sits between what users type and what is stored
- A JCo parameter is set as a string of the field's own width and type

## Strong signals

- Puts the conversion in one place on the boundary rather than at each call site
- Knows the conversion can be done on the SAP side, and that doing it per row is another
  roundtrip
- Notes that field widths differ between releases, so padding to a hard-coded length ages badly

## Weak signals

- Concludes the material does not exist
- Adds zeros until it works, with no idea why, and hard-codes the width
- Wants the ABAP side to "fix the function module"

## Answer bands

### weak

- Decides the data is missing and closes the ticket.
- Cannot suggest any difference between the screen value and the stored value.

### junior

- Suspects the value being sent and compares it against what is stored.
- Gets to padding by experiment and makes the call work.

### mid

- Names the internal versus external distinction and why the call was silent.
- Extends it to the other field types that bite the same way.
- Puts the conversion in one place and can say where.

### senior

- Decides where conversion belongs and defends it against the alternative.
- Avoids hard-coded widths and says what would break on an upgrade.
- Says how this class of defect gets caught before production, given it produces no error.

## Follow-ups

- The fix works for every material except a handful that came from an old load. What might be
  different about those?
  probes: whether padding is unconditional, or depends on how the system is set up
- The next interface passes a date and gets an error instead of an empty result. Why the
  difference?
  probes: type checking at the boundary versus a silently wrong key
- Where in your code would you put this so the next developer cannot get it wrong?
  probes: one boundary layer versus scattered fixes

## Notes

Whether a material number is padded depends on system configuration; some systems store them
lexicographically and no padding is applied. The interviewer should accept "it depends how the
system is set up, and I would check" as a better answer than a confident rule.

In newer releases the material number field is wider than the classic eighteen characters, which
is exactly why hard-coded padding is a poor fix.

Interviewer background, not a recall test: the generic routine that pads numeric-looking keys
with leading zeros is `ALPHA`, but material numbers have their own routine, `MATN1`, whose
behaviour — including whether numbers are handled lexicographically — is driven by a
configuration setting on the SAP side. That is the mechanism behind "it depends how the system is
set up". A candidate who never names either routine but knows the stored key and the displayed
key can differ, and that the difference is configured rather than fixed, has answered this card
fully.

## Sources

- https://help.sap.com/doc/saphelp_em900/9.0/en-US/4a/547e956a8a1cd4e10000000a421937/content.htm?no_cache=true
- https://help.sap.com/doc/saphelp_nw75/7.5.5/en-US/4a/547e686a8a1cd4e10000000a421937/content.htm?no_cache=true
