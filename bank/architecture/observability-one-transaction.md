---
title: Support needs to follow one transaction across two systems. What do you log?
difficulty: 3
tags: [observability, operations, support]
time_minutes: 5
order: 20
---

## Ask

Support has a customer complaint and one timestamp. They need to follow that single transaction
from your service into the system behind it. What did you log so they can?

## Look for

- A stable request id and a business key, both carried across the boundary
- The identifier the other system uses, captured from its response
- Operation, duration, error category and retry count, not just a stack trace
- Says what is redacted: credentials, tokens, payload fields
- Clear time zones

## Red flags

- Logs the full request and response
- Only a Java stack trace
- A correlation id that stops at the service boundary

## Follow-ups

- The other system was restarted and lost its logs. What in your logs still helps?
- How would you find every transaction affected by a two-minute outage?
