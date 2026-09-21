---
id: java-exceptions-client-library-contract-01
schema_version: 2
title: Thirty services grepping an exception message
category: java
topic: exceptions
level: lead
tags: [api-design, retries, failure-modes]
time_estimate_min: 10
order: 510
links:
  related: [java-api-design-shared-record-change-01]
---

## Ask

You have taken over an internal HTTP client library that thirty services depend on. Today every
failure comes out as a `RuntimeException` with a message, and callers are matching on the message
text to decide whether to send the request again. What do you change, and what do you stop those
thirty teams from having to decide for themselves?

## Tests

Whether the candidate derives a failure taxonomy from what a caller can actually do about each
case, and decides what the library absorbs itself rather than passing every failure outward.

## Ideal minimal answer

Reads what the thirty callers match on today, then derives the types from what a caller can act
on — send again now, send again later, give up, or fix the request. Draws the line between what
the library absorbs itself and what it surfaces, keeps the default safe for a caller that
ignores the distinction, and ships both shapes during a stated window.

## Listen for

- Callers need to tell apart what they can act on: send again now, send again later, give up, or fix
  the request — the type should carry that, not the prose
- Keeps the transport's own types out of the signature while keeping the cause attached underneath
- Says what belongs in the thrown object: status, endpoint, an identifier support can be quoted, and
  nothing secret
- Weighs checked against unchecked for a library at this scale, including the cost at every
  intermediate layer that must not care
- A hierarchy the caller can switch over completely, so a newly added kind does not quietly fall
  into the branch that sends the request again
- Ships the new shape alongside the old behaviour, moves consumers with a stated window, and does
  not require everyone to change on one day

## Expected knowledge

- Chained causes, and that the message is for a person while the type is for the code
- Sealed hierarchies, and what exhaustiveness buys a caller when the library grows a case

## Strong signals

- Asks what callers actually do today, reading their matching rules, before designing anything
- Makes the safe behaviour the default for a caller that ignores the distinction
- Says which failures the library should absorb itself, with its own backoff, and which must surface

## Weak signals

- Designs an elaborate type hierarchy with no migration story for the thirty
- "Always use checked exceptions", or "never use them", stated as a principle
- Adds an error code and keeps throwing one type, so callers still branch on a value in a string

## Answer bands

### mid

- Replaces the single type with a few types that mean different things.
- Keeps the cause attached and stops callers reading the message.
- Has no plan for the consumers beyond telling them to upgrade.

### senior

- Derives the types from what a caller can actually do, not from the transport's status codes.
- Puts enough context in the thrown object to diagnose an incident, and excludes secrets.
- Argues checked versus unchecked from this library's position rather than from doctrine.
- Sequences the change so both shapes work during a window.

### lead

- Starts from what the thirty callers do today, reading their matching rules, and designs to that
  evidence rather than to a taxonomy they like.
- Draws the line between what the library retries on its own and what it must surface, and says
  who owns the time and the load that its own retrying spends.
- Chooses defaults that stay safe when a caller ignores the distinction entirely, and says what
  that costs the caller who did care.
- Weighs a checked hierarchy against an unchecked one by what each costs the layers in between and
  the next person to add a case, rather than from doctrine.
- Says what a team that cannot move for two quarters gets, without making that everyone's problem.

## Follow-ups

- A caller treats anything it does not recognise as safe to send again. What do you have to be
  careful about?
  probes: idempotency of the underlying call; defaults that stay safe when the caller is careless
- Half the failures are the dependency being briefly unavailable, and every one of the thirty has
  written its own loop for that. What do you do with that observation?
  probes: what the library should absorb; thirty uncoordinated retry policies aimed at one service
- Six months on, someone adds a new kind of failure to the library. What do you want to happen at
  the thirty call sites?
  probes: complete handling versus silent fall-through; whether adding a case breaks compilation

## Notes

The nearby card on adding a component to a shared record also has consumers who cannot be made to
move, and a candidate can spend this whole card on rollout mechanics. That is the other card's
subject. Steer back to the design: which failures the caller can act on, which the library should
never have shown them, and what the type is supposed to make impossible to get wrong.

## Sources

- https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html#jls-8.1.1.2
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Throwable.html
