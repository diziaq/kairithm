---
id: java-generics-erasure-boundary-01
schema_version: 1
title: Where the compiler stops promising
category: java
topic: generics
level: mid
tags: [correctness, api-design, failure-modes]
time_estimate_min: 7
order: 610
---

## Ask

Inside a `Repository<T>` someone wants to write `if (row instanceof T)` and to build a `T[]` to
return. Neither compiles. They ask whether to take a `Class<T>` in the constructor, or to just cast
and add `@SuppressWarnings`. How do you answer?

## Tests

Whether the candidate knows what survives compilation, and can say where the compiler's guarantee
stops and a runtime failure starts.

## Listen for

- The type argument is not present at runtime, so there is nothing to test against and nothing to
  build the array from
- Taking the class object at construction is the standard way to get the check back, because the
  caller does know what the type is
- The suppressed cast does not fail where it is written; it fails later, at a cast the compiler
  inserted at the call site
- Knows what is kept: the declared types in signatures, and the type arguments of a superclass,
  which is why some libraries make you extend an empty holder
- Says an array of a type variable is unsound in a way a list is not, and prefers the collection

## Expected knowledge

- Erasure, and that one compiled class serves every type argument
- An unchecked warning marks the exact place where the compiler has stopped promising

## Strong signals

- Mentions that a varargs parameter of a parameterised type is the same hole, and what the
  annotation on such a method is claiming on the author's behalf
- Says who is responsible once the check is suppressed, and wants it confined to one place with the
  invariant written down
- Asks whether the repository needs the type at runtime at all, or whether the caller can do the
  narrowing

## Weak signals

- "Java generics are fake" and stops there
- Suppresses the warning at class level
- Believes reflection can recover the type argument of an arbitrary object

## Answer bands

### weak

- Suggests casting until it compiles, with no account of what that costs.
- Cannot say why the two lines are rejected.
- Thinks the type argument is available at runtime like any other field.

### junior

- Says the type argument is not there once the code is compiled.
- Prefers passing the class object but cannot say what it buys beyond making it compile.
- Treats the suppressed warning as equivalent and harmless.

### mid

- Explains why the check is impossible and what the class object restores.
- Says where the suppressed version actually blows up, and that it is far from the cast.
- Prefers a list over an array of the type variable and can say why.

### senior

- Names what is retained in signatures and how a library exploits it to recover a type argument.
- Treats the suppression as a claim the author is making, and insists it be confined and documented.
- Decides between the two options from who holds the knowledge of the type, not from convenience.

## Follow-ups

- They cast and ship it. A caller reports a failure on a line that has no cast in it at all.
  Explain that to them.
  probes: compiler-inserted casts; the distance between the mistake and the symptom
- A serialisation library manages to produce exactly the right type when it fills in a generic
  field. How does it manage that?
  probes: what is retained in signatures, and the empty-subclass trick for capturing an argument
- When is passing the class object genuinely not worth it?
  probes: judgement — a confined cast with a stated invariant can be the right call
