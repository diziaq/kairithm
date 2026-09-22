---
id: java-concurrency-condition-await-if-01
schema_version: 2
title: Two years of service, then null out of take() twice
category: java
topic: concurrency
level: senior
tags: [correctness, failure-modes, concurrency, testing]
time_estimate_min: 9
order: 630
links:
  shallower: [java-concurrency-unbounded-queue-oom-01]
  related: [java-memory-model-double-checked-locking-01]
---

## Ask

A hand-rolled bounded buffer on JDK 21 uses one lock and one condition. `take()` does
`if (queue.isEmpty()) notEmpty.await();` and then removes an element; both `put` and `take` call
`signal()`. It has been in production for two years. Last month a consumer got `null` back from
`take()` twice, three weeks apart. What is wrong with it?

## Tests

Whether the candidate can say what returning from a wait does and does not establish, and see the
second defect that one condition object for two kinds of waiter creates.

## Ideal minimal answer

Coming back from the wait only means the lock was reacquired; nothing says the thing waited for
is still true, because another consumer can have taken the element in between, and a wakeup is
permitted with no signal behind it at all. So the check has to be a loop, not an `if`. Separately,
one condition for both roles can wake a thread that cannot proceed.

## Listen for

- Says a waiting thread that is woken has to compete for the lock again, and by the time it holds
  it the state can have been changed by whoever was signalled first or got there first
- Adds that a return from waiting is permitted even where nothing signalled, so the predicate must
  never be assumed from the fact of waking
- Concludes the test has to be re-evaluated in a loop, and that this is the documented way to use
  the construct rather than a defensive habit
- Sees the second defect: with one condition serving producers and consumers, waking exactly one
  waiter can wake the wrong kind, which then goes back to sleep and the thread that could have
  made progress was never told
- Says that failure looks like a hang rather than a `null`, so it is a different symptom of the
  same design and would not have been caught by fixing the loop alone
- Names the two ways out and separates them: wake every waiter, or keep two conditions on the one
  lock so each kind is woken on its own
- Says two years of clean running is not evidence, because the window is a handful of
  instructions wide

## Expected knowledge

- A lock can carry more than one wait set, and that is the reason the construct exists separately
  from the intrinsic monitor
- Waking one waiter is cheaper than waking all of them, and is only safe when every waiter on that
  set can actually use the state change

## Strong signals

- Reconstructs the interleaving with two consumers and one producer and walks it through
- Says the `null` is the buffer's own invented answer, so the caller cannot tell it from an empty
  slot, and treats that as a third defect
- Asks what changed a month ago — consumer count, load, a machine with more cores — and treats the
  timing as information rather than coincidence
- Says the same reasoning applies to the intrinsic monitor's wait and notify, so a reviewer should
  read every one in the codebase the same way
- Proposes deleting the class in favour of the standard bounded queue, and says what is lost

## Weak signals

- Adds a null check at the call site
- Says the lock was not held, having been shown that it was
- Attributes it to a hardware or runtime defect because it is so rare
- Wakes every waiter, calls it fixed, and cannot say what it cost
- Tells the story of a past race and never returns to this code

## Answer bands

### mid

- Says the check must be repeated after waking rather than done once.
- Explains that another thread can empty the buffer in between.
- Does not raise the single wait set, or does so only after being asked.

### senior

- States, before the question is put to them, that returning from the wait establishes only that
  the lock is held again.
- Adds that a return is permitted with nothing having signalled, and treats that as a rule rather
  than a curiosity.
- Raises the single condition serving both roles before being asked, and predicts the hang.
- Says why two years of clean running tells you nothing about the width of the window.

### lead

- Chooses between waking everybody and splitting the wait sets, from the number of waiters and
  the cost of a wasted wake.
- Decides whether the class should exist at all against a standard one, and says what the team
  loses by switching.
- Says how a defect of this class would be caught before the next two years pass.
- Treats the invented `null` as an interface problem and says what the method should do instead.

## Follow-ups

- It ran for two years and then failed twice in one month. Does that make you more confident or
  less?
  probes: whether rarity is read as evidence of absence; what changed in load or thread count
- You make the change and the nulls stop. Six months later the whole thing stops making progress
  under load instead.
  probes: the single wait set, and a wake delivered to a thread that cannot use it
- A reviewer suggests just waking everybody every time as the cheap fix. What do you tell him?
  probes: whether they can price it, and say when it is nonetheless the right call
- Would you keep this class in the codebase at all?
  probes: reaching for the standard structure, and being able to say what is given up

## Sources

- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/Condition.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Object.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ArrayBlockingQueue.html

## Notes

The two documented facts this card rests on, both from the `Condition` javadoc.

On waking: "a 'spurious wakeup' is permitted to occur, in general, as a concession to the
underlying platform semantics. This has little practical impact on most application programs as a
Condition should always be waited upon in a loop, testing the state predicate that is being waited
for. An implementation is free to remove the possibility of spurious wakeups but it is recommended
that applications programmers always assume that they can occur and so always wait in a loop."

On the two wait sets — and this is the part candidates miss — the javadoc's own bounded buffer
example uses `notFull` and `notEmpty` on one `ReentrantLock`, and explains why: "We would like to
keep waiting put threads and take threads in separate wait-sets so that we can use the
optimization of only notifying a single thread at a time when items or spaces become available in
the buffer."

Note the order of the argument. The strongest version does not lead with spurious wakeups at all,
because it does not need them: two consumers waiting, a producer adds one element and signals,
consumer A is woken, and consumer B — woken earlier by an unrelated signal, or simply winning the
lock — takes the element first. A comes back from the wait holding the lock with an empty buffer
and, because the test was an `if`, walks straight past it. Credit a candidate who gets there
without invoking the platform's permission to wake a thread for no reason; credit them more if
they then add it as a second, independent reason.

Figures to release when asked: four consumers and one producer; the buffer holds 64; throughput
roughly doubled in the last quarter; the two occurrences are in the log as a null-pointer
exception three frames above `take`, which is why nobody connected them.

The intrinsic monitor's `wait` carries exactly the same rule, so a candidate who generalises to
every `wait`/`notify` in the codebase has understood it. A candidate who says "`await` can wake
spuriously" and stops has recited one sentence.
