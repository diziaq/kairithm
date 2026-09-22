---
id: java-runtime-default-charset-upgrade-01
schema_version: 2
title: Question marks in customer names the week after the upgrade
category: java
topic: runtime-behaviour
level: mid
tags: [correctness, operations, maintainability, failure-modes]
time_estimate_min: 7
order: 650
links:
  deeper: [java-runtime-container-memory-limit-01]
---

## Ask

A batch job has read the same supplier files for six years. The week the service moved from JDK
17 to JDK 21, customer names started coming out with question marks in them. The code did not
change, the files did not change, and it still reads them correctly on two developers' laptops.
Where do you look?

## Tests

Whether the candidate knows that a read without a stated encoding takes one from somewhere, and
can find a defect that was latent for six years and was exposed by a default changing underneath
it.

## Ideal minimal answer

The files are not UTF-8 and the code never said what they were, so it had been picking up
whatever the platform default happened to be. From JDK 18 that default is UTF-8 everywhere,
regardless of the locale the server is started with. The laptops were already UTF-8, which is why
they show nothing. Name the encoding explicitly at every read.

## Listen for

- Says a reader or a string conversion with no encoding given uses a default, and the code has
  therefore never stated what these files are
- Knows the default stopped being derived from the operating system and the locale, and became
  one fixed value, in a specific release between the two in play
- Explains the laptops: they were already on that value, so they were never exercising the old
  behaviour and could not have caught this
- Says the question marks are the replacement character being written out — the bytes were already
  misread on the way in, and the damage is upstream of wherever it was noticed
- Fixes it by naming the encoding at the point of reading, not by changing a default back
- Asks what the files actually are, and notes that nobody can tell from the bytes with certainty
- Points out the same defect exists on every write, and that a round trip can hide it

## Expected knowledge

- A file is bytes; turning it into text requires a decision, and the library will make one if you
  do not
- The developers' machines and the server can disagree about that decision, so it is a class of
  fault that does not reproduce locally

## Strong signals

- Asks whether anything already stored in the database was written by this job since the upgrade,
  and treats cleaning that up as a separate task
- Knows there is a switch that restores the old derivation, and treats it as a stopgap with an
  owner and a date rather than the answer
- Knows the streams the process writes to are governed separately from the file default, so the
  log can be wrong while the files are right, or the reverse
- Asks how the team would notice the next time, and proposes a test that pins the encoding rather
  than one that runs wherever it happens to run
- Asks the supplier what the files are, in writing

## Weak signals

- "It must be the database collation"
- Replaces the offending characters, or strips anything outside the ASCII range
- Adds a flag to the command line and closes the ticket
- Says it cannot be the upgrade because nothing in the code changed
- Cannot reproduce it and therefore treats it as not happening
- Recounts an encoding mess at a previous job and never says what this batch job should do now

## Answer bands

### weak

- Blames the files, the supplier or the database with nothing to connect it to the upgrade.
- Proposes stripping or substituting the characters that come out wrong.
- Cannot say what turns bytes into text.

### junior

- Says an encoding is involved and the code does not state one.
- Connects the timing to the upgrade rather than calling it a coincidence.
- Cannot say what specifically changed between the two releases.

### mid

- Says the default was derived from the environment before and is now one fixed value, and names
  roughly where that changed.
- Explains why the laptops are silent on it.
- Names the encoding at the point of reading rather than reaching for a global switch.

### senior

- Asks what has been written since the upgrade and treats the corrupted rows as their own problem.
- Separates the file default from what the process writes to its streams.
- Says how the rest of the codebase gets found and how a test would hold the line afterwards.
- Arrives at the six silent years as the finding without being led there: the defect predates the
  upgrade.

## Follow-ups

- Somebody proposes a flag on the command line that puts the old behaviour back. Would you ship
  that?
  probes: whether it is treated as a stopgap with a date, or as the fix
- The same upgrade also changed what the service prints for those names to its log, but only when
  it runs under the scheduler and not from a terminal.
  probes: the streams being governed separately, and a pipe behaving unlike a console
- How would you find the other places in this codebase with the same defect, before a customer
  does?
  probes: a sweep for the calls that take no encoding, and a test that fixes the environment
- The supplier's answer is that the files are "plain text".
  probes: that this has to be agreed and written down, not guessed from the bytes

## Sources

- https://openjdk.org/jeps/400
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/charset/Charset.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/System.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/InputStreamReader.html

## Notes

The change is JEP 400, delivered in **JDK 18**, which specifies UTF-8 as the default charset of
the standard Java APIs. Before it, the default was chosen by an algorithm using "the user's
operating system, locale, and other factors". A team moving 17 to 21 crosses it without ever
reading a release note about it, which is exactly how this arrives.

Three system properties are worth knowing and they do different jobs:

- `file.encoding` set to `COMPAT` restores the pre-18 derivation. The JEP describes it in those
  terms; it is the stopgap in the first follow-up, and it buys time rather than fixing anything.
- `native.encoding` reports what the old algorithm *would* have chosen, whatever the default is
  now, so a program can still find out what the host thinks.
- The standard output and error streams have their own encodings, separate from the file default.
  That is the second follow-up: a scheduler redirecting the output to a pipe and a developer
  watching a console can genuinely see different results from the same code.

JEP 400's own compatibility note is the sentence to have in mind: applications "which implicitly
depend on the default charset... will behave incorrectly when processing data produced when the
default charset was unspecified."

Figures to release when asked: the files are ISO-8859-1 and always have been; the job uses a
`FileReader` and a `String` constructor with no encoding argument; the server's locale used to be
a Latin-1 one, which is why it had worked; both laptops are macOS, where the old algorithm already
produced UTF-8; about 40,000 rows have been written with damaged names since the upgrade, and
nobody has counted them yet.

The finding worth drawing out at the end: the code was wrong for six years and the upgrade did
not break it, it stopped hiding it. A candidate who says that unprompted has understood the card
better than one who names the release.
