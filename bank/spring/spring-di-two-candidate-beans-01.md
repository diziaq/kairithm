---
id: spring-di-two-candidate-beans-01
schema_version: 2
title: Two beans of the same type and a startup failure
category: spring
topic: dependency-injection
level: junior
tags: [configuration, failure-modes, correctness]
time_estimate_min: 5
order: 10
links:
  deeper: [spring-di-circular-dependency-01]
  related: [spring-bean-lifecycle-constructor-init-01]
---

## Ask

A service used to start fine. Someone adds a second implementation of `PaymentGateway`, and now
the application will not start: the log says one bean was required but two were found, at the
constructor of `CheckoutService`. Walk me through what the container was doing when it gave up,
and what your options are.

## Tests

Whether the candidate can read a container startup failure as a resolution step that had more
than one valid answer, and then choose between the ways out on their consequences rather than on
which annotation they remember first.

## Ideal minimal answer

The container was filling that constructor parameter by type, two definitions matched it, and it
will not guess, so startup fails. Either mark one as the default so it wins wherever the type is
asked for, or name the one wanted at that single point.

## Listen for

- The wiring point asks for a type, and two definitions match that type
- Knows the container matches on type first and only then falls back to other rules, including
  matching the parameter name against the bean name
- Names at least two ways out and says what each costs the next reader: marking one as the
  default, naming the wanted one at that single point, or taking all of them as a collection
- Asks whether both implementations should exist at all, or whether one is dead code

## Expected knowledge

- A bean has both a type and a name
- Wiring a collaborator through the constructor rather than setting a field later, and why that
  moves the failure to startup

## Strong signals

- Points out that marking one as the default quietly changes every other place that asks for
  the type, including code they have never read
- Says that taking both as a collection is the honest answer when the two are meant to coexist,
  and asks how the caller is supposed to pick between them

## Weak signals

- Deletes one of the two beans without asking what it was for
- Says the container wires by name and stops there
- Cannot say why the application fails at startup rather than at the first request
- Sets out the ways out with their consequences and will not say which one they would use here

## Answer bands

### weak

- Reads the message back without saying which step of startup failed.
- Guesses at an annotation and cannot say what it would do to other call sites.

### junior

- States that two candidates matched one place that asked for the type.
- Names a way to mark one as the default, or to name the wanted one at that place.

### mid

- Separates picking a default for the whole application from picking one at a single place.
- Suggests taking both where the two are meant to coexist, and says who decides at call time.
- Volunteers that the failure lands at startup, which is the cheapest place for it to land.

## Follow-ups

- Another team asks for the same type somewhere you have never read. Which of your options
  changes their behaviour without them noticing?
  probes: blast radius of a global default versus a choice made at one call site
- Both are meant to stay, and which one runs depends on the country on the order. How would you
  wire that?
  probes: whether they reach for taking all of them and choosing at call time
- The second one is only wanted when a flag is set in the deployed settings. What changes?
  probes: conditional registration, and whether they know a bean can simply not be defined

## Sources

- https://docs.spring.io/spring-framework/reference/core/beans/annotation-config/autowired-qualifiers.html

## Notes

If they mention matching the parameter name against the bean name, note that this depends on
parameter names surviving compilation. The Spring Boot build plugins pass `-parameters`; a build
that does not is a real source of "it works in my IDE" failures.
