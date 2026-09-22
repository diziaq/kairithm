---
id: spring-proxying-interface-vs-class-01
schema_version: 2
title: The injected object is not the class you wrote
category: spring
topic: proxying
level: senior
tags: [correctness, failure-modes, testing, configuration]
time_estimate_min: 9
order: 51
links:
  deeper: [spring-proxying-retry-transaction-order-01]
---

## Ask

`PricingService` implements `Pricing`, and one of its methods is annotated `@Transactional`. A
new component asks for `PricingService` by its concrete type and startup fails, saying the bean
named `pricingService` is of type `jdk.proxy2.$Proxy91` and not `PricingService`. A colleague
fixes it by flipping a property, and now everything starts — but a scheduled job that used to
read a field straight off that bean now reads null. Explain both halves.

## Tests

Whether the candidate can reason about what object is actually in the container after advice is
applied, and predict which ordinary Java assumptions stop holding for it.

## Ideal minimal answer

What is registered is a stand-in satisfying `Pricing`, not an object of the concrete type, which
is why startup failed. The property switches to a generated subclass that does satisfy it, but
the state still lives on the real object and only method calls are forwarded, so the field read
finds nothing; the fix is an accessor, and the flip is global.

## Listen for

- What is registered is a stand-in, not the written class; it satisfies the interface but is not
  of the concrete type
- The property switches the mechanism to a generated subclass, which does satisfy the concrete
  type, which is why it starts
- The generated subclass forwards method calls but holds none of the state, so reading a field
  off it directly returns nothing
- Asking for the interface would have been the right fix, and the property is a workaround
- The same effect explains annotations, `getClass()` and `equals` behaving unexpectedly on the
  injected object

## Expected knowledge

- The two mechanisms and when each is chosen by default
- That advice is applied by delegation, so only method calls go to the real object

## Strong signals

- Says the scheduled job was reaching past the API of the bean, and the fix is an accessor, not
  a different wrapping mechanism
- Knows how to unwrap to the real object in a test when they genuinely need it, and why they
  usually should not
- Points out that switching the mechanism globally changes behaviour for beans they have not
  looked at

## Weak signals

- Says "Spring uses proxies" and cannot say what changes for the caller
- Treats the property flip as the correct fix with no cost
- Believes both mechanisms produce an object that carries the original fields

## Answer bands

### weak

- Names the wrapper but cannot explain the type failure or the null field.
- Applies the property because it makes the error go away.

### mid

- Explains that the bean is a stand-in satisfying the interface, not the concrete class.
- Knows the property picks the other mechanism and why that satisfies the concrete type.
- Suggests asking for the interface instead, once asked whether the property was the right fix.

### senior

- Explains that state lives on the real object and only method calls are forwarded, so the
  field read after the flip finds nothing.
- Says the right fix is an accessor, and the field read was reaching past the bean's API.
- Notes, before anyone asks what the flip costs elsewhere, that it is global and changes beans
  nobody inspected.

### lead

- Decides whether the codebase should use one mechanism everywhere and states the trade-off for
  people writing new beans.
- Says what would have made both faults visible in a test rather than at startup and in a job.

## Follow-ups

- In a test, a mock of the collaborator is never matched because the object under test is not
  the one they stubbed. Same root cause?
  probes: unwrapping to the real object, and when that is legitimate
- Code elsewhere looks the injected bean up at runtime for a marker its class carries, and
  finds none. Why?
  probes: annotations live on the real class, not necessarily on the stand-in
- How much does the flip cost the rest of the application?
  probes: a global switch versus a local fix; blast radius again

## Sources

- https://docs.spring.io/spring-framework/reference/core/aop/proxying.html
- https://docs.spring.io/spring-framework/reference/core/aop-api/autoproxy.html

## Notes

Spring Boot sets `spring.aop.proxy-target-class=true` by default, so most Boot applications use
the generated subclass already; this card assumes an application that has turned that off or a
context configured for interface-based wrapping. `AopTestUtils.getTargetObject` and
`AopProxyUtils.ultimateTargetClass` are the unwrapping tools worth hearing named.
