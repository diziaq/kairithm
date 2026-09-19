---
id: spring-bean-lifecycle-constructor-init-01
schema_version: 1
title: A null collaborator inside a constructor
category: spring
topic: bean-lifecycle
level: junior
tags: [failure-modes, correctness, configuration]
time_estimate_min: 5
order: 20
links:
  deeper: [spring-bean-lifecycle-graceful-shutdown-01]
---

## Ask

A colleague writes a cache warm-up: the class has a `@Autowired` field for `RateRepository`, and
the constructor calls `rateRepository.findAll()` to fill a map. It throws a null pointer on every
startup. They move the same two lines into a method marked `@PostConstruct` and it works. Why?

## Tests

Whether the candidate knows the order in which the container builds a bean, and can say why one
piece of startup work is safe in one place and impossible in another.

## Listen for

- The object has to exist before anything can be put into its fields, so a field set from
  outside is still empty while the constructor runs
- The callback runs after every field has been filled, which is why the same code works there
- Knows the container calls the initialisation callback itself, and when
- Prefers taking the repository as a constructor parameter, which removes the whole class of
  problem instead of moving it

## Expected knowledge

- The order: create the object, fill what it needs, run the startup callback
- That a failure inside a startup callback stops the application from coming up

## Strong signals

- Says the fix they would actually make is to take the collaborator as a parameter, not to move
  the code into a callback
- Asks whether warming a cache at startup is even wanted, since it makes startup depend on the
  database being up

## Weak signals

- Says the framework is "not ready yet" with no account of which step had not happened
- Believes the annotation on the field makes the value appear before the object exists
- Suggests catching the null pointer

## Answer bands

### weak

- Says the framework had not finished, without naming which step had not run.
- Treats the working version as luck and cannot say what changed.

### junior

- States that the field is filled after the object is built, so it is empty inside the
  constructor.
- Knows the callback runs after the fields are filled.

### mid

- Walks the three steps apart and places both versions of the code on that timeline.
- Says a constructor parameter would make the value available at construction and make a missing
  collaborator a compile-time problem.
- Notes that failing in the startup callback stops the whole application, and asks whether that
  is the behaviour they want when the database is down.

## Follow-ups

- They change it so the thing it needs arrives as a constructor parameter, and put the warm-up
  back in the constructor. Is that now correct?
  probes: it works, but startup work in a constructor still ties object creation to a live
  database; whether they separate building from doing
- The warm-up needs data that another bean produces at startup. How do you make sure it runs
  second?
  probes: whether they reach for ordering between beans rather than sleeping or guessing
- What should happen if the query fails while the pod is starting?
  probes: fail fast versus degrade, and who finds out

## Sources

- https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html

## Notes

In Spring Boot 3 the annotation is `jakarta.annotation.PostConstruct`. The point of the card is
the ordering, not the annotation: a candidate who names it immediately but cannot say what has
and has not happened at each step has not answered.
