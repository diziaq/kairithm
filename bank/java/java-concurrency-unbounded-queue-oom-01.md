---
id: java-concurrency-unbounded-queue-oom-01
schema_version: 2
title: The pool that would not refuse anything
category: java
topic: concurrency
level: mid
tags: [failure-modes, memory, operations, correctness]
time_estimate_min: 8
order: 620
links:
  deeper: [java-concurrency-virtual-thread-migration-01]
  related: [java-gc-retained-map-oom-01]
---

## Ask

An import service on JDK 21 runs its work through `Executors.newFixedThreadPool(8)`. During a
traffic spike the platform kills it for running out of memory instead of it refusing work.
Someone raised the figure to 64; the next spike killed it at exactly the same heap size. Why did
neither the small pool nor the large one shed any load?

## Tests

Whether the candidate knows what that factory method actually builds, and can see that the thing
filling the heap is the waiting work rather than the running work.

## Ideal minimal answer

That factory hands you a queue with no capacity, so submitting never fails and the tasks simply
accumulate on the heap — they are what fills it. With a queue that never fills, the larger figure
changes nothing, because extra threads are only created when the queue turns a task away. Build
the executor by hand with a bounded queue and decide what happens on overflow.

## Listen for

- Says the queue behind that factory method has no capacity, so a submission is never refused and
  the backlog has nowhere to stop
- Locates the memory: the objects held by queued tasks, not the eight or sixty-four being worked
  on, so the heap fills at the rate of arrival minus the rate of completion
- Explains why the larger figure was inert: threads beyond the core count are only started when
  the queue refuses a task, and this one never does
- Says the fix is to construct the executor directly with a queue of a stated capacity, at which
  point submission can fail
- Treats the failure as the feature: something has to be told no, and the question is who and what
  they are told
- Knows there is a choice of what happens to a task that will not fit, and can name more than one
  and say which they would pick here
- Asks what is upstream of the import, because the answer decides between dropping work and
  slowing the producer down

## Expected knowledge

- A pool has a core size, a maximum size and a queue, and the three interact in a defined order
- Killed from outside for exceeding a memory limit is not the same event as the runtime giving up

## Strong signals

- Asks how large one task is on the heap, and sizes the queue from that and a latency budget
  rather than picking a round number
- Says making the submitting thread run the task is a way to slow the producer down without
  losing work, and says when that is wrong
- Points out that a queue deep enough to smooth a burst is also deep enough to hold work nobody
  wants any more by the time it runs
- Asks whether the killed process left anything half done, and treats that as a separate defect
- Wants the queue depth on a graph before the next spike, not after it

## Weak signals

- Raises the maximum heap, or the pool size again
- Says the fix is a bigger machine
- Adds a check on the queue's size before submitting and stops there
- Blames the collector for not keeping up
- Recounts an outage with the same shape and never says what to change here
- Names all four things that can happen to a task that will not fit and will not say which one
  this import service should use

## Answer bands

### weak

- Says the pool was too small, or too large, with no account of where the memory went.
- Proposes more heap or a restart schedule.
- Cannot say what happens to a task when every thread is busy.

### junior

- Says the tasks wait somewhere and that somewhere is in memory.
- Knows the number given to that factory method is the thread count, not a limit on work accepted.
- Suggests putting a cap on how much is waiting.

### mid

- Says the queue has no capacity, so submitting always succeeds and the backlog is the leak.
- Explains why sixty-four behaved exactly like eight.
- Constructs the executor with a bounded queue and, once asked, says what the caller sees when it
  is full.

### senior

- Chooses the overflow behaviour from what is upstream before anybody puts the question to them,
  and says what each choice costs.
- Sizes the bound from memory per task and how long a task may reasonably wait.
- Separates shedding load from losing work, and says which one the business can live with.
- Says what is on the dashboard afterwards so the next spike is visible before the kill.

## Follow-ups

- They bound it at ten thousand and now the service throws during spikes instead of dying. Are
  they finished?
  probes: what the caller is told, and which of the standard behaviours on a full queue they pick
- The work arrives over HTTP from one upstream service that tries again on any failure.
  probes: pushing back on the producer rather than discarding, and what a retry storm does here
- What number would you actually put in, and how would you defend it to a reviewer?
  probes: sizing from memory per task and a waiting time, rather than a round figure
- Six months later somebody proposes running each import on its own thread instead of a pool.
  probes: whether they hold on to the bound as the point, independent of the threading model

## Sources

- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/Executors.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/RejectedExecutionHandler.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/ArrayBlockingQueue.html

## Notes

The javadoc says it in one sentence each and candidates still get it wrong. `newFixedThreadPool`
"creates a thread pool that reuses a fixed number of threads operating off a shared unbounded
queue". And on the pool itself: "Using an unbounded queue... will cause new tasks to wait in the
queue when all corePoolSize threads are busy. Thus, no more than corePoolSize threads will ever be
created. (And the value of the maximumPoolSize therefore doesn't have any effect.)" Followed
immediately by the warning that this "admits the possibility of unbounded work queue growth when
commands continue to arrive on average faster than they can be processed."

So the person who raised 8 to 64 changed a number that the class documents as having no effect in
this configuration. That is the moment the card is looking for.

Rejection only happens "when the Executor uses finite bounds for both maximum threads and work
queue capacity, and is saturated". The four supplied behaviours are worth knowing by what they do
rather than by name: throw at the submitter (the default), run the task on the submitting thread,
drop the new task silently, drop the oldest queued task. The second is the one that applies
back-pressure; the third and fourth lose work and the javadoc says the fourth "is rarely
acceptable".

Figures to release when asked: each queued task holds a parsed file of about 400 KB; the heap is
2 GB; a normal minute brings 30 imports and the spike brought 4,000 in ten minutes; the upstream
retries three times.

Where this sits against the virtual threads card: that one is about what happens when the pool is
removed altogether and the limit it was silently providing goes with it. This one is about a pool
that never provided a limit in the first place. If a candidate answers this by proposing virtual
threads, ask them what bounds the work then — that is the harder card.
