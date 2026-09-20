---
id: java-exceptions-lost-in-cleanup-01
schema_version: 1
title: The morning spent on disk space
category: java
topic: exceptions
level: mid
tags: [failure-modes, correctness, observability]
time_estimate_min: 7
order: 505
links:
  deeper: [java-exceptions-client-library-contract-01]
  related: [java-runtime-shutdown-signal-01]
---

## Ask

A nightly export writes a file and then uploads it. The code is
`try { write(out); } finally { out.close(); }`. Last night the job died with an `IOException`
coming from the close call, and the team spent the morning on disk space. Two days later someone
finds the write itself had already gone wrong, for an entirely different reason, and nobody ever
saw it. How did that error disappear, and what do you change?

## Tests

Whether the candidate knows that a cleanup block which throws replaces the failure already on its
way out, and can say what a failure from closing something being written actually means.

## Listen for

- Whatever is thrown from the `finally` block leaves the method in place of the exception that was
  already travelling; the first one is gone and nothing records that it existed
- `try`-with-resources closes the same thing and attaches the second failure to the first instead
  of discarding it, so the operator sees both with the cause named first
- A failure from closing an output is not a formality: buffered bytes are flushed on close, so the
  file may be short or empty — swallowing that would lose data quietly
- Separates closing something that was being read, where there is nothing left to lose, from
  closing something that was being written
- Asks what happened to the partly written file: whether the upload step runs over it anyway, and
  whether it was written under its final name before it was known to be complete
- Wants both failures in the log, not a choice between them

## Expected knowledge

- `try`-with-resources, and that it keeps the second failure attached to the first
- Closing a buffered output flushes it, so the close can fail for a real reason

## Strong signals

- Asks whether any other job in the codebase is written the same way, and treats that as the fix
- Says what last night's log should have contained, and counts the wasted morning as part of the
  defect
- Would have the job write to a temporary name and rename only once the bytes are known to be
  there

## Weak signals

- Wraps the close in its own block and swallows whatever it throws
- Offers "never put code in `finally`" as a rule, with no account of what happened here
- Accepts the disk as the cause, which is what the team already did
- Logs the close failure and considers the incident explained

## Answer bands

### weak

- Takes the disk as the cause and talks about capacity.
- Silences the close so it cannot fail again, and says nothing about the bytes.
- Cannot say where the first error went.

### junior

- Says the second error replaced the first one on the way out of the method.
- Reaches for the language construct that closes the file, rather than the hand-written block.
- Wants the original error to reach the log.

### mid

- Explains that both errors exist and describes how the second can be carried alongside the first
  rather than destroying it.
- Says a failure while closing something being written can mean the bytes never landed, and
  refuses to swallow it.
- Treats reading and writing differently when deciding what a close failure is worth.
- Asks what happened to the partly written file and whether anything downstream has already taken
  it.

### senior

- Counts the morning spent on the wrong cause as part of the damage, and says what the log had to
  show for that morning not to happen.
- Says what the job should do with output it cannot vouch for: where it writes it, when it renames
  it, what tonight's run finds left over.
- Goes looking for the same shape across the codebase instead of fixing the one file.

## Follow-ups

- Someone proposes an empty catch around the close so the job stops dying there. What breaks?
  probes: bytes that never reached the file; hiding the second error instead of the first
- The same shape appears in a job that is reading a file rather than writing one. Does your answer
  change?
  probes: whether the direction of the stream changes what a close failure means
- The upload is a separate step that looks for the file by name. What does it send tonight?
  probes: a partly written file treated as complete; writing under a temporary name
- The incident report has one line in it: disk full. What should it have said?
  probes: the first error as the cause and the second as context, both present

## Sources

- https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html#jls-14.20.3
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Throwable.html#addSuppressed(java.lang.Throwable)
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/BufferedWriter.html
