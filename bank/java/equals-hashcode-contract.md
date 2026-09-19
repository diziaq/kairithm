---
title: An object goes into a `HashSet` and cannot be found again. What happened?
difficulty: 2
tags: [collections, equals, correctness]
time_minutes: 4
order: 10
---

## Ask

Someone puts an object into a `HashSet`, changes one field, and then `contains` returns false for
that same object. Walk me through what happened.

## Look for

- The hash was computed at insert time and the bucket does not move
- The mutated field is part of `hashCode`
- Keys in a hash structure should be immutable, or at least stable

## Red flags

- Blames the `HashSet` implementation
- Overrides `equals` without `hashCode` and sees no problem
- Suggests calling `rehash` or rebuilding the set as the normal fix

## Follow-ups

- What is the contract between `equals` and `hashCode`, in your own words?
- Would a record fix this, and why?
