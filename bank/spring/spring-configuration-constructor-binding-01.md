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
`@ConfigurationProperties(prefix = "billing")`, and they keep `@Component` on it so it is still
picked up. The application starts, nothing is logged, and every field holds the default from the
record's compact constructor — none of the values in `application.yml` are applied. What is going
on, and how would you have caught this in a test?

## Tests

Whether the candidate understands that binding settings onto an object is a separate step from
creating that object, and whether they know the failure mode is silence rather than an error.

## Listen for

- Filling an immutable object means passing the values in when it is created, so whoever creates
  the object has to do the binding
- A bean picked up by scanning is created the ordinary way, so nothing binds into it
- Names the registration route that does do it: declaring the settings type where the framework
  is told to bind it, or scanning specifically for settings types
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

- Separates creating the object from filling it, and says the ordinary creation path does not
  fill it.
- Names a registration route that does bind, and removes the scanning annotation.
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

## Sources

- https://docs.spring.io/spring-boot/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.constructor-binding
- https://docs.spring.io/spring-boot/reference/features/external-config.html#features.external-config.typesafe-configuration-properties.enabling

## Notes

Constructor binding is not used for a bean created through regular mechanisms such as
`@Component` or a `@Bean` method — this is stated in the reference documentation. The working
routes are `@EnableConfigurationProperties(BillingProperties.class)` or
`@ConfigurationPropertiesScan`. In Spring Boot 3, `@ConstructorBinding` may only be placed on a
constructor, and is only needed when the type has more than one.
