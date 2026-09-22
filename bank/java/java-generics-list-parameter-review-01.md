---
id: java-generics-list-parameter-review-01
schema_version: 2
title: It compiles once the type argument is removed
category: java
topic: generics
level: junior
tags: [correctness, api-design, testing]
time_estimate_min: 5
order: 600
links:
  related: [microservices-api-evolution-renamed-field-broke-consumer-01]
  deeper: [java-generics-erasure-boundary-01]
---

## Ask

A colleague writes `void logAll(List<Object> items)` and finds that it will not compile when they
pass a `List<String>`. Their fix is to change the parameter to a bare `List`. It compiles, the tests
pass, and they have opened the pull request. What do you say?

## Tests

Whether the candidate can explain why the compiler refused the call, and choose the fix that keeps
the checking rather than the one that switches it off.

## Ideal minimal answer

Says the call is rejected because, if it were allowed, the method could put anything at all into
the caller's list; the bare form does not fix the signature, it switches the checking off for
every use inside the method. Reaches for the parameter form that accepts any element type while
forbidding additions.

## Listen for

- Says why the two are not interchangeable: if that call were allowed, the method could put anything
  at all into the caller's list
- The bare form does not just unblock this call — it turns checking off for every use of that
  variable inside the method
- Names the parameter type that accepts any element type while forbidding additions
- Asks what the method actually needs to do with the elements, because that decides which form is
  right

## Expected knowledge

- A list of one type is not a subtype of a list of its supertype, while arrays behave the other way
- The compiler inserts the casts that a call on a parameterised type implies

## Strong signals

- Brings up that arrays are assignable that way and fail at runtime instead, and contrasts the two
- Says that reading and adding want different signatures, and picks the narrower one
- Notices the compiler already flagged the bare form and treats that as the signal, not as noise

## Weak signals

- "Generics are only syntax sugar so it makes no difference"
- Adds an annotation to silence the warning and moves on
- Casts the list and is satisfied because it runs

## Answer bands

### weak

- Approves the change because it compiles and the tests pass.
- Cannot say why the original call was rejected.
- Says the two list types are the same thing at runtime and stops there.

### junior

- Explains that allowing the call would let the method insert the wrong element type.
- Says the bare form removes checking rather than fixing the signature.
- Reaches the right parameter type, possibly after being asked what the method does.

### mid

- States the rule about subtyping between parameterised types and gives the counterexample.
- Chooses the signature from what the method does to the elements — reading versus adding —
  before anyone asks.
- Says where the failure would surface with the colleague's version, and when.

## Follow-ups

- The method now needs to add a placeholder entry to the list it was given. Does your answer hold?
  probes: whether they see that reading and adding pull the signature in opposite directions
- With their version in place, someone later adds a line that puts a number into that list. When
  does anybody find out?
  probes: the failure moving to an inserted cast at a distant call site, at runtime
- The build prints a warning on that line. What is that worth?
  probes: whether a warning is treated as information or as noise to be silenced
