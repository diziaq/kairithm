---
id: spring-persistence-optimistic-locking-01
schema_version: 1
title: Two edits, one survivor
category: spring
topic: persistence
level: lead
tags: [consistency, transactions, retries, correctness]
time_estimate_min: 11
order: 82
links: {}
---

## Ask

Two support agents open the same customer record, each change a different field, and each save.
The second save silently wipes the first agent's change — the record ends up with only the second
agent's edit. Separately, a nightly job that touches the same table has started failing in bursts
with conflicts. You own both. What do you put in place, and how do you decide between the
options?

## Tests

Whether the candidate can choose a concurrency strategy from the access pattern rather than by
habit, knows where a conflict is detected and where it must be handled, and can say what the
human on the other end sees.

## Listen for

- Loading, editing and saving a whole record means the save carries stale fields, so the later
  write overwrites the earlier one — nothing is lost at the database, it is lost by the read
- A counter on the row turns the silent overwrite into a detectable conflict at write time
- Detecting a conflict is not handling it: someone has to decide between retrying, merging, and
  telling the user
- Holding a lock on the row for the duration of a human's edit is not an option, and why
- The job and the interactive path want different answers: a retry is fine for one and wrong
  for the other
- The retry must be outside the failed unit of work, with the record re-read each time

## Expected knowledge

- The difference between detecting a conflict at write time and preventing one by holding the
  row against everyone else
- That a conflict surfaces at flush or commit, not at the line of code that changed the field

## Strong signals

- Asks whether the save should be sending the whole record at all, or only the changed fields
- Says that a bounded, jittered retry for the job and an explicit conflict response for the
  agent is the right split, and names who sees what
- Points out that the counter only protects rows, and any rule spanning rows needs the database
  to enforce it
- Asks how the agents are supposed to recover: what the screen shows and whether their typing
  survives

## Weak signals

- Reaches for the strictest isolation level as the answer
- Locks the row while the agent has the screen open
- Retries the conflicting write in a loop with no bound and no re-read
- Treats the burst of failures as noise to be suppressed

## Answer bands

### mid

- Identifies that the second save carried stale values read before the first one.
- Adds a counter on the row so the second write is rejected instead of winning.

### senior

- Explains where the conflict is detected relative to the code that made the change.
- Splits the two paths: bounded retry with a fresh read for the job, explicit conflict handling
  for the agent.
- Rejects holding a lock across a human's thinking time and says what it would cost.
- Knows the retry must wrap a fresh unit of work, not sit inside the failed one.

### lead

- Decides from the access pattern and the cost of a lost edit, and says which option they would
  not take and why.
- Defines what the agent actually sees and whether their unsaved typing survives.
- Puts rules that span rows into the database rather than into application code.
- Says what is measured: conflict rate as a signal that the design or the workflow is wrong.

## Follow-ups

- The job now retries and mostly succeeds. Two weeks later it retries constantly. What does that
  tell you?
  probes: treating the rate as a signal about contention, not as noise to suppress
- The agent gets told their save failed. They have typed two paragraphs. What happens to them?
  probes: whether the design includes the human, or stops at the exception
- Someone proposes locking the row when the agent opens the screen. Talk me through a day of
  that.
  probes: lock held across human latency; abandoned sessions; the queue behind it
- The rule is that a customer may not have two active mandates. Does your mechanism cover that?
  probes: per-row protection versus a rule across rows; where invariants belong

## Sources

- https://docs.spring.io/spring-data/jpa/reference/jpa/locking.html
- https://jakarta.ee/specifications/persistence/3.1/

## Notes

`@Version` is the per-row counter; a stale write raises `ObjectOptimisticLockingFailureException`
at flush or commit. `@Lock(LockModeType.PESSIMISTIC_WRITE)` is the other option and is
appropriate for short server-side contention, never for the duration of a user's editing
session. The retry point is the same one as in the proxying card: it must wrap a new unit of
work that re-reads the row.
