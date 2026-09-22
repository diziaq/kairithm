---
id: spring-di-circular-dependency-01
schema_version: 2
title: A refactor introduces a cycle between two services
category: spring
topic: dependency-injection
level: senior
tags: [failure-modes, correctness, api-design, configuration]
time_estimate_min: 8
order: 11
links:
  related: [spring-proxying-interface-vs-class-01]
---

## Ask

After a refactor, `OrderService` takes `InvoiceService` in its constructor and `InvoiceService`
takes `OrderService`. On Spring Boot 3 the application refuses to start and prints a cycle. A
colleague says the same shape worked on an older Boot version and wants to set the property that
brings that behaviour back. What do you tell them, and what would you actually do?

## Tests

Whether the candidate can explain why one wiring style can survive a cycle and another cannot,
and whether they treat the cycle as a design signal rather than a setting to be silenced.

## Ideal minimal answer

With both collaborators required at construction, neither object can be finished first, so no
order works. The property they want goes back to handing out a half-built object, which is
observably incomplete during startup and bites in a startup callback; a lazily resolved stand-in
only moves the failure to the first call. The real fix is a third collaborator or an event.

## Listen for

- With both collaborators required at construction time, neither object can be finished first,
  so there is no order that works
- Setting the field after the object exists lets the container hand out a half-built reference,
  which is why the older default appeared to work
- Knows that the escape hatch is off by default now, and that turning it back on leaves a bean
  that is observably incomplete during startup
- Inserting a stand-in that resolves the real bean on first use is the mechanical fix, and it
  moves the failure from startup to the first call
- The real fix is usually a third collaborator, an event, or moving the shared behaviour down

## Expected knowledge

- The order the container creates and wires singletons in
- That a cycle among singletons is broken, if at all, by exposing an unfinished object

## Strong signals

- Asks what the two services actually share, and proposes the smaller piece that both depend on
- Points out that a cycle that only survives by handing out an unfinished object will bite in a
  startup callback, where the other half may still be empty
- Mentions that the same cycle can hide behind an aspect or a scoped bean and only appear once
  something is advised

## Weak signals

- Switches the wiring style purely to make the message disappear, with no account of what
  changed
- Sets the property and moves on
- Claims the container can always sort this out and the error is a regression
- Sets out the property, the lazily resolved stand-in and the third collaborator with fair
  trade-offs, and will not say which one they would merge

## Answer bands

### weak

- Suggests a keyword or a property that makes the message go away, without saying what it does.
- Cannot say why one wiring style survives the cycle and the other does not.

### mid

- Explains that neither object can be completed first when both are required at construction.
- Knows, when pushed on why the older version coped, that setting a field later allows a partly
  built object to be handed over.
- Suggests pulling the shared behaviour into a third collaborator.

### senior

- Raises unasked what the escape hatch actually leaves behind, and when that bites.
- Explains what a lazily resolved stand-in changes: startup succeeds, the failure moves to the
  first call, and the object seen is not the target.
- Reads the cycle as two services that are really one responsibility, and says which way to cut.

### lead

- Decides between splitting the services, publishing an event, and living with the stand-in from
  the size of the change and who maintains it.
- Says how the team stops the next cycle: keeping the default on in every service, and treating
  the failure as a review signal rather than a build problem.

## Follow-ups

- Suppose you take the quick way out and the app starts. One of the two does work in a startup
  callback. What can go wrong there?
  probes: whether they realise the partly built object is visible during startup
- The two services keep drifting back together over a year. What would you change so it stops
  happening?
  probes: moves from the mechanical fix to the design and the review habit
- The cycle only appears after someone marks a method on one of them as needing a transaction.
  Why would that matter?
  probes: an advised bean brings a wrapper into the wiring graph

## Sources

- https://docs.spring.io/spring-boot/reference/features/spring-application.html
- https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html

## Notes

`spring.main.allow-circular-references` has defaulted to `false` since Spring Boot 2.6. A
constructor cycle is unresolvable; setter and field wiring are resolved by exposing an early
reference to a singleton that is still being created. `@Lazy` at one wiring point inserts a proxy
and defers resolution.
