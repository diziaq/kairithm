---
id: java-testing-mocks-assert-the-calls-01
schema_version: 2
title: Nineteen tests broke on a refactor that changed nothing
category: java
topic: testing
level: senior
tags: [testing, maintainability, correctness, api-design]
time_estimate_min: 8
order: 905
links:
  deeper: [java-testing-slow-suite-strategy-01]
  related: [general-testing-bug-escaped-with-green-tests-01]
---

## Ask

The tests for one service class build five mocks each and assert the exact calls made on them, in
order. Last month a refactor that moved code around without changing what the class does broke
nineteen of them. Last week a change that did alter what the class does broke none of them. The
team's plan is to update the nineteen. What is your view?

## Tests

Whether the candidate sees false failures and false passes as one defect — tests bound to how the
class is written rather than to what it does — and can say what to assert instead without banning
test doubles outright.

## Ideal minimal answer

Puts the two events together: tests bound to which calls were made fail when the code moves and
say nothing when the behaviour changes. Asserts instead on what the class returns or leaves
behind, keeps only the calls that are themselves the behaviour, says what each of the nineteen
was buying, and deletes the ones buying nothing.

## Listen for

- Connects the two events: assertions about which calls were made fail when the calls move, and
  say nothing when the result changes
- Nothing in those tests looks at what comes out — the returned value, the state left behind, the
  one message that genuinely leaves the process
- Keeps a stand-in where the collaborator is slow, remote or has an effect outside the process,
  and uses the real object where it is plain data or logic
- A stubbed collaborator encodes a claim about how that other class behaves; if nothing ever
  checks the claim, the stub and the code can be wrong together and both stay green
- Names the calls that really are the behaviour — the charge taken, the mail sent — and keeps
  asserting those deliberately
- Asks what the class is for before deciding where the test should sit; five collaborators in one
  class is itself worth a comment
- Changes them as the surrounding code is worked on, starting where last week's defect got out,
  rather than one sweeping rewrite

## Expected knowledge

- The difference between a stand-in that merely lets the test run and one whose calls are the
  assertion
- Asserting on a result or on resulting state, rather than on the route taken to it

## Strong signals

- Asks what did catch last week's change, and what would have
- Is willing to delete a test rather than rewrite it, and says what each one was buying
- Prices the nineteen updates against the next refactor, which will pay the same bill again
- Wants the stub's claim about the real collaborator checked somewhere against the real thing

## Weak signals

- Updates the nineteen to match the new call sequence and closes the ticket
- Offers "mocks are bad, use real objects" with nothing said about speed or external effects
- Adds tests at a higher level and leaves the nineteen exactly as they are
- Worries about the count of tests dropping, as though that were the measure

## Answer bands

### weak

- Rewrites the assertions to match the new sequence and treats it as finished.
- Says the tests are fine now because they pass.
- Blames the refactor for touching too much.

### junior

- Notices the tests check which calls happened rather than what came out.
- Says something should have failed last week and nothing did.
- Suggests asserting on the returned value instead.

### mid

- Puts the two events together as one problem rather than two unrelated annoyances.
- Asserts on what the class returns or leaves behind and drops the ordering of the calls.
- Keeps a stand-in for the collaborator that is slow or reaches outside, and uses the real object
  for the rest.
- Changes the tests alongside the code instead of in one sweep.

### senior

- Says what each of the nineteen was buying, and will delete the ones buying nothing rather than
  rewrite them.
- Keeps the assertions on the calls that are themselves the behaviour, and can say which those are
  here.
- Points out that the stubs encode assumptions about other classes that nothing verifies, and says
  where that gets verified.
- Reads five collaborators in one class as evidence about the design, not only about the tests.
- Starts where the real defect escaped and justifies leaving the rest alone for now.

## Follow-ups

- Somebody proposes deleting all nineteen and writing one test that drives the whole thing through
  the HTTP endpoint. What do you say?
  probes: feedback speed and how precisely a failure points at the cause; choosing the level
- One of the five calls being checked is the one that actually charges the customer. Does that
  check stay?
  probes: separating an interaction that is the behaviour from one that is a detail of the route
- You put the real class back in place of one of the five, and it turns out to need a database.
  Where do you stop?
  probes: where the seam belongs; what widening the test costs on every run
- Six months on, the class that one of the five imitates starts doing something new and no test
  notices. What would have caught it?
  probes: whether anything ever checks the imitation against the real thing

## Notes

The build-time card on this topic is about where the minutes go. This one is about what the tests
assert, so keep it there: if the candidate starts redesigning the suite's runtime, take the point
and steer back to the nineteen.
