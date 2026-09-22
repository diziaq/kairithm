---
id: spring-auto-configuration-shared-starter-01
schema_version: 2
title: The internal starter that broke forty services
category: spring
topic: auto-configuration
level: lead
tags: [api-design, configuration, operations, testing]
time_estimate_min: 12
order: 61
links:
  related: [spring-testing-context-cache-01]
---

## Ask

You own an internal starter that forty services depend on for logging, tracing and a shared HTTP
client. A patch release went out on Friday and by Monday a dozen services would not start, two
had duplicate beans, and one team has forked the whole thing because they could not override a
single bean. Redesign it. What do you change in the code, and what do you change about how it
ships?

## Tests

Whether the candidate can design a library that participates in someone else's application
without owning it: conditional registration, overridability, ordering, and a release process
that makes breakage visible before it is deployed.

## Ideal minimal answer

Every bean the starter contributes is registered only when the consumer has not supplied its own,
through the declared entry point rather than by scanning their packages. Draw the line between
what a consumer may override and what the platform guarantees, put a canary and a staged rollout
in front of forty services, and replace breaking changes in a patch with a deprecation window.

## Listen for

- Every bean the starter contributes is registered only when the consuming application has not
  supplied its own, so overriding one bean never requires a fork
- Registration goes through the framework's declared entry point, not by scanning the consumer's
  packages — scanning from a library is how you get duplicates and surprise beans
- Beans that depend on an optional library are guarded on that library being present
- Ordering relative to the framework's own configurations is declared, not hoped for
- Everything configurable is exposed as bound settings with defaults, rather than requiring
  beans to be replaced
- Tests build a throwaway context per scenario and assert which beans exist under which
  conditions
- Shipping: version discipline, a canary service, deprecation before removal, a changelog that
  names behaviour changes and not just commits

## Expected knowledge

- That a starter and the module carrying the wiring are usually separate artefacts
- That the entry point is a declared list file, and that the older mechanism no longer works in
  Spring Boot 3

## Strong signals

- Writes the conditional behaviour as tests over a lightweight context runner, and can name it
- Points out that a library must never assume the consumer's package layout
- Distinguishes a bean the consumer may replace from one they may not, and says how the second
  kind is defended
- Treats the Friday release as a process failure and fixes the pipeline as well as the code

## Weak signals

- Describes only what a starter is
- Proposes pinning every consumer to a fixed version forever
- Registers beans unconditionally and tells consumers to exclude them one by one
- Has no story for testing the library other than deploying it
- Lists the ways a consumer could be given control of a bean, with fair trade-offs, and will not
  say which one the starter should offer

## Answer bands

### mid

- Guards contributed beans so the consumer's own bean wins.
- Knows the wiring is declared in a file the framework reads, not by scanning.
- Exposes settings for the values consumers change most.

### senior

- Guards on optional libraries as well as on beans, and declares ordering against the
  framework's own configurations.
- Tests each condition against a throwaway context instead of a full application.
- Separates the dependency-only artefact from the one carrying the wiring, and says why.

### lead

- Draws the line between what consumers may override and what the platform guarantees, and
  defends the second.
- Puts a canary service and a staged rollout in front of forty consumers.
- Specifies deprecation with a removal window rather than breaking changes in a patch.
- Names what the team owning the starter is on the hook for when a consumer's startup fails at
  two in the morning.

## Follow-ups

- One consumer needs the opposite of your default for a single bean. What do they have to write,
  and what must they not have to write?
  probes: overriding by defining their own, never by forking or excluding
- Your library adds a bean that needs a driver that half the consumers do not have on the
  classpath. What happens to the other half?
  probes: guarding on the library being present
- How do you know, before release, that all forty still start?
  probes: a context-level test matrix plus a canary, not hope
- A consumer's app starts three seconds slower after the upgrade. Whose problem is it?
  probes: ownership, and what the platform team measures

## Sources

- https://docs.spring.io/spring-boot/reference/features/developing-auto-configuration.html
- https://docs.spring.io/spring-boot/reference/features/developing-auto-configuration.html#features.developing-auto-configuration.testing

## Notes

In Spring Boot 3 the entry point is
`META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`; the
`spring.factories` route for auto-configuration was removed in 3.0. `@AutoConfiguration` carries
`before`/`after` for ordering. `ApplicationContextRunner` is the test tool worth hearing named.
