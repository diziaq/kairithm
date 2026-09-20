---
id: spring-proxying-final-method-01
schema_version: 1
title: A final keyword that switches off an annotation
category: spring
topic: proxying
level: mid
tags: [correctness, failure-modes, api-design]
time_estimate_min: 7
order: 50
links:
  deeper: [spring-proxying-interface-vs-class-01]
---

## Ask

`ReportService` implements no interface. Someone marks one of its `@Transactional` methods
`final` so nobody can override it in a test. The application starts normally, every test passes,
and in production that method no longer runs in a transaction. Why is there no error? And what
would have happened if they had marked the whole class `final` instead?

## Tests

Whether the candidate knows how the annotation is physically applied to a class with no
interface, and can therefore derive which language constructs it cannot reach — rather than
having memorised a list of rules.

## Listen for

- With no interface, the container builds a subclass at runtime that overrides each method and
  puts the behaviour around the call
- A method that cannot be overridden cannot have anything wrapped around it, so the call goes
  straight to the original code
- Marking the class itself unextendable makes the subclass impossible, so that one fails loudly
  at startup instead
- Derives the same conclusion for methods that cannot be overridden for other reasons
- Notices the asymmetry: one mistake is loud, the other is silent, and the silent one is worse

## Expected knowledge

- The two ways the container can wrap a bean, and which one applies with no interface
- That the wrapper is a different object from the target

## Strong signals

- Says the framework does log that it could not wrap the method, and that nobody reads that log
  line, so the real defence is a test that asserts behaviour
- Points out the test passed because the test never exercised a rollback
- Notes that in a language where classes and members are final unless explicitly opened, this is
  the default outcome rather than an accident, and knows what has to be added to make it work

## Weak signals

- Says the keyword is "not allowed with Spring" with no mechanism
- Believes the annotation is read at each call
- Cannot say why one of the two variants fails at startup and the other does not

## Answer bands

### weak

- Asserts a rule about the keyword without saying how the behaviour is attached.
- Cannot predict which of the two variants fails at startup.

### junior

- Knows the container puts something in front of the bean and that the keyword interferes.
- Cannot say how, or what happens with the whole class marked.

### mid

- Describes the generated subclass and the overridden methods.
- Explains that an unoverridable method cannot be wrapped, so the call reaches the original.
- Predicts that an unextendable class fails at startup rather than silently.

### senior

- Derives the rule for other unoverridable shapes instead of listing them.
- Points out the test suite proved nothing because it never provoked a rollback, and says what
  the test should assert.
- Says which of the two mechanisms was in play and why the class having no interface chose it,
  rather than treating the keyword as the whole cause.

## Follow-ups

- The reviewer says the tests all passed, so the change is safe. What is wrong with that?
  probes: the tests never provoked the behaviour the annotation provides
- The class is changed so it implements an interface, and the context is configured to wrap
  through that instead. Does the keyword still matter?
  probes: whether the limitation follows from the mechanism or is believed to be a rule about
  the keyword itself
- How would you stop this shape of change reaching production again?
  probes: a behavioural test, or a build-time check, rather than reviewer vigilance

## Sources

- https://docs.spring.io/spring-framework/reference/core/aop/proxying.html
- https://docs.spring.io/spring-framework/reference/core/aop-api/autoproxy.html

## Notes

With no interface the container uses a generated subclass; a `final` method cannot be overridden
so it is not advised, and Spring logs at INFO that it could not proxy it — which nobody reads. A
`final` class cannot be subclassed at all and bean creation fails at startup, which is the loud
half of the pair. With an interface-based proxy the limitation disappears for methods declared on
the interface, because the proxy implements the interface rather than extending the class. In
Kotlin, classes and members are final unless opened, which is why Spring ships a compiler plugin
that opens the annotated ones.
