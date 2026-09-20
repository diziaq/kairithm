---
id: spring-configuration-constructor-binding-01
schema_version: 1
title: Settings that silently stay at their defaults
category: spring
topic: configuration
level: mid
tags: [configuration, correctness, failure-modes, api-design]
time_estimate_min: 8
order: 31
links:
  related: [spring-auto-configuration-backed-off-01]
---

## Ask

A team makes their settings class immutable: a Java record annotated
`@ConfigurationProperties(prefix = "billing")`. To be certain it exists as a bean, they declare it
from a `@Bean` method in a configuration class, constructing it with sensible defaults. The
application starts, nothing is logged, and every field still holds the default that `@Bean` method
passed in — none of the values in `application.yml` are applied. What is going on, and how would
you have caught this in a test?

## Tests

Whether the candidate understands that binding settings onto an object is a separate step from
creating that object, and whether they know the failure mode is silence rather than an error.

## Listen for

- Filling an immutable object means passing the values in when it is created, so whoever creates
  the object has to do the binding
- Because the application constructed the object itself, the framework can only fill it
  afterwards, by setting properties on an object that already exists — and there are none to set
- Names the registration route where the framework creates the object itself, so it can pass the
  values through the constructor
- Knows a missing key is not an error by default, which is why this is silent
- Would assert on the bound object in a test rather than trusting startup

## Expected knowledge

- Relaxed naming, so one key can be written several ways
- That validation can be switched on for a settings type, which turns silence into a failure

## Strong signals

- Suggests annotating the type so a missing or nonsensical value stops startup, and argues that
  a service should refuse to run misconfigured rather than run wrong
- Mentions that a list in a higher-priority source replaces the list below it rather than
  merging with it, so a partial override is a trap
- Knows how to test the binding in isolation without standing the whole application up

## Weak signals

- Adds setters and declares the problem solved, with no account of why
- Blames the record type itself
- Says the annotation on the settings class is enough and cannot say who reads it

## Answer bands

### weak

- Reverts to a mutable class and cannot say what was different.
- Thinks the values were wrong in the file.

### mid

- Separates creating the object from filling it, and says an object the application built itself
  cannot be filled through its constructor afterwards.
- Names a registration route that does bind, and takes the hand-written declaration back out.
- Points out that nothing complained, and adds a test that asserts on the values.

### senior

- Makes the service refuse to start on a missing or invalid value, and explains why failing at
  startup beats failing at three in the morning.
- Knows a list from a higher source replaces rather than merges, and what that does to a partial
  override in one environment.
- Tests the binding with the smallest thing that can bind, not the whole application.

## Follow-ups

- Nothing failed and nothing was logged. What would you change so the next mistake of this shape
  is loud?
  probes: validation on the settings type; fail at startup rather than at runtime
- The file lists three allowed regions and the deployment adds a fourth through the environment.
  What does the running app end up with?
  probes: whether they know a list is replaced wholesale, not merged
- How would you prove the mapping works without starting the service?
  probes: a focused test over the binder rather than a full context
- Somebody suggests marking the record so it is picked up by scanning instead. What do you expect
  to happen?
  probes: whether they can predict a different, loud failure — the container trying to satisfy the
  record's parameters from the bean graph — rather than another silent one

## Sources

- https://docs.spring.io/spring-boot/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.constructor-binding
- https://docs.spring.io/spring-boot/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.enabling

## Notes

Constructor binding is not used for a bean created through regular mechanisms such as a `@Bean`
method, `@Component` or `@Import` — this is stated in the reference documentation. Such a bean
falls back to JavaBean binding onto the instance that already exists; a record has nothing to set,
so the bind is a no-op and nothing is reported. The working routes are
`@EnableConfigurationProperties(BillingProperties.class)` or `@ConfigurationPropertiesScan`, where
the framework instantiates the type and can pass the values to the constructor. In Spring Boot 3,
`@ConstructorBinding` may only be placed on a constructor, and is only needed when the type has
more than one.
