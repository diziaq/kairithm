---
id: spring-configuration-property-precedence-01
schema_version: 2
title: The value in the file is not the value in the pod
category: spring
topic: configuration
level: junior
tags: [configuration, operations, failure-modes]
time_estimate_min: 5
order: 30
links:
  deeper: [spring-configuration-constructor-binding-01]
---

## Ask

`application.yml` in the repository says the downstream read timeout is thirty seconds. In
production the calls are clearly giving up after two. Nobody has changed the file, the image is
built from that commit, and the same build behaves correctly on a laptop. Where do you look, and
why would a file in the jar lose?

## Tests

Whether the candidate knows that settings come from an ordered stack of sources rather than from
one file, and whether they go and read what the running process actually resolved instead of
reasoning from the repository.

## Ideal minimal answer

Values come from an ordered stack of sources and a later one wins; the file packaged in the jar
sits near the bottom, so the process environment or a command line argument where it is deployed
is beating it. Log the resolved value at startup, or ask the running application which source
supplied it.

## Listen for

- There is an ordered list of sources and a later one wins; the packaged file is near the bottom
- Names sources that beat it: command line arguments, the environment of the process, an
  externalised file next to the jar, a profile-specific file
- Knows an environment variable in shouting case maps onto a dotted key, so the name in the
  deployment does not look like the name in the file
- Goes and asks the running application which source won, rather than guessing

## Expected knowledge

- Profile-specific files, and that they sit above the plain one
- That the platform can inject values the repository never mentions

## Strong signals

- Asks for the deployment manifest and the container's environment in the same breath as the
  repository
- Mentions that the laptop working is evidence about the laptop, not about the code

## Weak signals

- Insists the file must be wrong and rereads it a third time
- Does not know anything outside the jar can set a value
- Proposes hard-coding the timeout in Java to "make sure"

## Answer bands

### weak

- Keeps looking inside the repository and has no idea what else could set the value.
- Suggests hard-coding the number so nothing can override it.

### junior

- Knows the environment of the process and the command line beat the packaged file.
- Suggests printing or logging the value at startup to see what was resolved.

### mid

- Describes the stack of sources in rough order and places the packaged file in it.
- Knows the shouting-case name maps onto the dotted key, and would grep the manifest for it.
- Asks the running application which source supplied the value instead of inferring it.

## Follow-ups

- You have no shell on the pod and cannot add logging. What can the running app tell you?
  probes: whether they know the app exposes where each value came from
- The same key is set in two places outside the jar and one of them is a secret. Which wins?
  probes: whether the ordered stack is a rule they can apply, not a story about one case
- Someone proposes that nothing outside the repository may set a value, so this cannot happen
  again. What do you say?
  probes: the reason the stack exists at all; per-environment values and secrets

## Sources

- https://docs.spring.io/spring-boot/reference/features/external-config.html

## Notes

The ordered list in the reference documentation is the whole answer. `/actuator/env` shows every
source and which one won; `--debug` at startup does not, so a candidate who names it is close but
looking at the wrong report.
