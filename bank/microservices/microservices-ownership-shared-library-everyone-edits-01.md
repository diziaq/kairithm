---
id: microservices-ownership-shared-library-everyone-edits-01
schema_version: 2
title: A common library fourteen teams depend on and nobody owns
category: microservices
topic: ownership
level: senior
tags: [ownership, operations, api-design, maintainability]
time_estimate_min: 9
order: 230
links:
  deeper: [microservices-ownership-paged-for-someone-elses-data-01]
---

## Ask

There is a `common` library that all fourteen of your services depend on. A security fix in it
means fourteen teams each have to upgrade and redeploy, and in practice half of them are still on
a version from last year. Who owns that library, and what would you change?

## Tests

Whether the candidate can reason about coupling introduced at build time, and turn "nobody owns
it" into a concrete arrangement.

## Ideal minimal answer

Split what is in there: plumbing that never diverges can stay shared, but business logic in a
build-time dependency means fourteen teams have to redeploy before a change takes effect, which
is the independence the split was meant to buy. Give it a named maintainer, a release cadence
and a support window, make who is on which version visible, and attack the cost of upgrading.

## Listen for

- Names the real cost: a change that fourteen teams must adopt has a lead time measured in
  quarters, and a security fix cannot wait that long
- Splits what is in there — plumbing that genuinely never diverges, versus logic that ended up
  shared because it was convenient
- Shared business logic couples the services at build time and takes away the independence the
  split was supposed to buy
- Says what ownership means concretely: a named maintainer, a release cadence, a support policy
  for old versions
- Wants visibility of who is on which version, because today nobody can answer that
- Makes upgrading cheap — automation, a tight compatibility promise, small releases — rather than
  making it mandatory

## Expected knowledge

- A dependency taken at build time only changes when the consumer redeploys
- The same logic behind an API changes for everyone at once, with its own consequences

## Strong signals

- Asks what is actually in the library before answering, and expects the answer to be mixed
- Points out that pushing shared logic behind a service trades a slow rollout for a runtime
  dependency, and says when that trade is worth it
- Has a view on how long old versions are supported and who pays for it

## Weak signals

- "Every team should just keep up to date"
- Proposes deleting the library and duplicating everything with no discussion
- Assigns ownership to a platform team with no capacity or mandate mentioned

## Answer bands

### mid

- Names a team to own it and wants a proper release process.
- Sees that the slow adoption is the core problem.
- Treats all the library's contents as one thing.

### senior

- Separates the contents by kind and gives different answers for each.
- Explains why shared logic at build time undercuts independent deployment.
- Defines ownership in terms someone could act on tomorrow, including version visibility.
- Attacks the cost of upgrading rather than the willingness of teams to upgrade.

### lead

- Sets a policy for what is allowed to be shared this way and what is not, and can defend it.
- Decides how long old versions are supported and who funds the maintenance.
- Weighs a fleet-wide runtime dependency against a slow rollout, using how often each fails.
- Says how the team would find out tomorrow that a service is on an unsupported version.

## Follow-ups

- How do you get all fourteen onto the new version by Friday?
  probes: whether they reach for a mandate or for making the upgrade nearly free
- Half of it is helper code and half of it is how a price is worked out. Does one answer cover
  both?
  probes: distinguishing shared plumbing from shared meaning
- A team forks it rather than upgrading. Good or bad?
  probes: judgement about divergence against coupling, and when a fork is the right call
