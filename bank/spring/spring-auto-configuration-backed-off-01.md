---
id: spring-auto-configuration-backed-off-01
schema_version: 2
title: One new bean changes every endpoint
category: spring
topic: auto-configuration
level: mid
tags: [configuration, failure-modes, api-design, observability]
time_estimate_min: 8
order: 60
links:
  deeper: [spring-auto-configuration-shared-starter-01]
---

## Ask

A developer needs one extra serialisation rule, so they add an `@Bean ObjectMapper` to a
configuration class. The build passes. The next day, three consumer teams open tickets: every
timestamp in every response has changed from an ISO string to a number, on endpoints that
developer never touched. Explain the mechanism that made one bean do that, and how you would
find out what else changed.

## Tests

Whether the candidate understands that Boot's defaults are conditional beans that step aside
when the application defines its own, and can name the report that shows what stepped aside.

## Ideal minimal answer

Boot defines its own only when the application has not, so the new bean replaced it and took
everything Boot had configured on that default with it, not just the one rule. Adjust the
existing default through the customisation hook instead of replacing it, and read the report of
what matched and what stepped aside to see what else moved.

## Listen for

- Boot's default is defined only when the application has not defined one of its own, so the
  new bean replaced it
- Replacing it discards everything Boot had configured on that default, not just the one rule
  the developer wanted
- The date format changed because the module and the setting Boot applied are no longer applied
- The right move is to adjust the existing default through the customisation hook rather than
  replace it
- Knows where the framework prints what it decided and why, and would read it

## Expected knowledge

- That auto-configured beans are conditional on the application not supplying one
- That a report of positive and negative matches is available at startup and at runtime

## Strong signals

- Frames it as an API break for three downstream teams, and asks whether anything consumes the
  old format in storage as well as over the wire
- Says a contract test on the response shape would have caught it and the unit tests could not
- Notices that the same shape of accident is waiting for anyone who defines their own data
  source, template builder or message converter
- Asks how the replacement was actually constructed, because a bare one would have failed on
  those fields outright rather than quietly changing their shape

## Weak signals

- Says "Spring magic"
- Fixes it by reapplying settings onto the new bean by hand, one at a time, until the tickets
  stop
- Cannot say how to see which defaults are in effect
- Recounts how a similar bean replacement was diagnosed at a previous job, without saying what
  they would change about these endpoints

## Answer bands

### weak

- Cannot connect the new bean to the changed responses.
- Patches the symptom by copying settings until the reported fields look right.

### junior

- Knows the framework has defaults and that defining a bean can replace one.
- Cannot say what else was lost or where to look.

### mid

- Explains that the default is conditional on the application not defining its own.
- Says, once asked what else moved, that the replacement lost all of Boot's configuration on it,
  not just the changed rule.
- Uses the customisation hook instead of replacing the bean.
- Knows where to read the list of what matched and what did not.

### senior

- Raises it as a published contract change without being asked, and wants to know who else is
  affected, including storage.
- Says which test would have caught it and why the existing suite could not.
- Generalises to the other beans with the same conditional shape.

## Follow-ups

- Another team hits the same thing with their data source and loses database metrics. Same
  cause?
  probes: whether the rule generalises past the one bean they were told about
- You want exactly one extra rule and nothing else to move. What do you write?
  probes: reaching for the customisation hook rather than a replacement
- How would the pipeline have stopped this before three teams noticed?
  probes: a test that asserts the wire format, not the internals

## Sources

- https://docs.spring.io/spring-boot/reference/using/auto-configuration.html
- https://docs.spring.io/spring-boot/reference/features/json.html

## Notes

`JacksonAutoConfiguration` defines its `ObjectMapper` with `@ConditionalOnMissingBean`, built
through `Jackson2ObjectMapperBuilder`, which registers the discoverable modules including
java.time and disables `SerializationFeature.WRITE_DATES_AS_TIMESTAMPS`. Define your own and all
of that goes. The number-shaped output in the scenario is what you get when the replacement
registers the modules — `findAndRegisterModules()`, or a builder — but not the feature settings,
because that feature is enabled by default in Jackson itself and only Boot's builder turns it off.
A mapper with no modules at all fails on those fields instead, which is a useful thing to notice.
The customisation hook is `Jackson2ObjectMapperBuilderCustomizer`. The report is `--debug` at
startup or `/actuator/conditions` at runtime.
