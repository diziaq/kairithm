---
id: spring-testing-context-cache-01
schema_version: 1
title: The banner printed sixty times
category: spring
topic: testing
level: lead
tags: [testing, performance, operations, correctness]
time_estimate_min: 11
order: 92
links: {}
---

## Ask

A team's test suite has grown to 400 tests and takes 26 minutes; the same tests took four
minutes a year ago and the assertions have barely changed. Scrolling the build log, the Spring
banner appears about sixty times. You are asked to get the pipeline back under five minutes
without deleting tests. Where do you start, and what rules do you leave behind so it does not
come back?

## Tests

Whether the candidate knows that the test framework reuses application contexts, what makes two
tests get different ones, and can turn that into a policy a team can follow.

## Listen for

- A context is built once and reused by every test whose configuration is identical; sixty
  banners means sixty distinct configurations
- Names what makes two tests differ: different classes or profiles, different inline settings,
  a different set of replaced beans, and anything that forces a rebuild
- Knows replacing a bean with a stub is part of what identifies the context, so a one-off
  replacement in one test class costs a whole new context
- Knows the reuse has a bounded size, so past a certain number of distinct configurations
  contexts are evicted and rebuilt repeatedly — which is why growth is not linear
- Converges on a small number of shared configurations, and pushes most tests down to plain
  objects or narrow slices
- Shares the external dependencies too, rather than starting a database per class
- Leaves a rule: adding a new distinct configuration is a reviewed decision

## Expected knowledge

- That swapping one bean for a stub in a single test class fragments reuse
- That an annotation asking for a rebuild defeats reuse for everything after it
- Narrow test slices, and that each slice is its own configuration

## Strong signals

- Measures first: counts the distinct configurations and the rebuild time before changing
  anything
- Points out that most of the 400 tests do not need a container at all, and that constructor
  wiring is what makes that possible
- Knows the reuse limit is tunable and that raising it trades memory for time, and says how
  they would pick
- Treats a stub declared on a base class as different from one declared per class, and uses
  that

## Weak signals

- Proposes running tests in parallel as the first move, with no account of the shared state
- Deletes integration tests
- Raises the reuse limit and stops
- Says the suite is slow because there are too many tests

## Answer bands

### mid

- Knows the context is reused between tests and that rebuilding is the cost.
- Names one or two things that make two tests need different contexts.

### senior

- Explains what identifies a context and why a per-class stub fragments reuse.
- Consolidates onto a handful of shared configurations and moves tests to narrow slices.
- Reuses the external dependencies across the suite instead of per class.
- Measures the rebuild count before and after rather than only the wall clock.

### lead

- Knows reuse is bounded and explains the non-linear blow-up past that bound, and how to choose
  the bound.
- Argues that most tests should not need a container, and says what has to be true of the code
  for that.
- Leaves a rule the team can apply in review, not a one-off cleanup.
- Says what the pipeline reports afterwards so the regression is visible in a week, not a year.

## Follow-ups

- One class replaces a single collaborator with a stub. What does that cost the suite?
  probes: whether they know the replaced beans are part of what identifies a context
- They fix it, and six months later it is 20 minutes again. What did you fail to leave behind?
  probes: a reviewable rule and a signal, rather than a cleanup
- Half of these tests only check a mapping between two objects. What should they be?
  probes: pushing work down to plain tests; what the code has to look like for that
- Somebody suggests running the suite in parallel instead. What has to be true first?
  probes: shared state and shared external dependencies before concurrency

## Sources

- https://docs.spring.io/spring-framework/reference/testing/testcontext-framework/ctx-management/caching.html
- https://docs.spring.io/spring-boot/reference/testing/spring-boot-applications.html

## Notes

The cache key is built from the configuration classes, locations, initializers, active profiles,
property sources, context customizers (which is where `@MockBean` / `@MockitoBean` enters) and
the resolved loader. `spring.test.context.cache.maxSize` defaults to 32, and eviction is least
recently used — which is exactly why a suite degrades sharply once the number of distinct
configurations passes it. `@MockBean` is deprecated in favour of `@MockitoBean` from Spring Boot
3.4; both fragment the cache the same way.
