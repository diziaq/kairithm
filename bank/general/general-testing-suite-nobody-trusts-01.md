---
id: general-testing-suite-nobody-trusts-01
schema_version: 2
title: A quarter of the runs fail, and everybody just presses it again
category: general
topic: testing
level: senior
tags: [testing, correctness, operations, failure-modes]
time_estimate_min: 8
order: 170
links:
  related: [java-testing-mocks-assert-the-calls-01]
---

## Ask

Roughly one run in four of your team's test suite fails. Nobody investigates those failures any
more — people press the button again and it usually goes green the second time. A release is due
to go out this afternoon and the run in front of you is red. What do you do about this
afternoon, and what do you do about the habit?

## Tests

Whether the candidate can act when the team's main evidence of correctness has stopped being
believed: making a defensible shipping decision today without that evidence, and restoring the
signal as work with an order, an owner and a way to tell it came back.

## Ideal minimal answer

Says today's red run proves nothing in either direction, because a suite people re-run on
failure no longer separates a defect from noise, and names what they would establish before
shipping this afternoon instead. Sets the worst offenders aside to restore the signal, each with
an owner and a deadline, and goes looking for the defect that already escaped.

## Listen for

- Says plainly that a suite people re-run on failure no longer separates a real defect from
  noise, so today's red run tells them nothing in either direction
- Refuses to let pressing the button again stand as the decision about this afternoon's release,
  and says what they would establish instead before shipping
- Wants the history first — which tests fail, how often, since when — rather than only the one in
  front of them
- Asks whether any of the failures people waved through was ever real, and goes looking for a
  defect that reached customers that way
- Sets the worst offenders aside so that what remains is believable again, with a deadline and a
  named person on each one
- Separates being believed from being complete: a smaller suite the team acts on beats a larger
  one it does not

## Strong signals

- Points out that the habit has trained the team to ignore exactly the class of defect the suite
  exists to catch, and treats that as a correctness problem rather than an annoyance
- Makes the failure rate a visible number that is reported on, so the work can be argued for with
  evidence instead of with complaint
- Says what the team is allowed to do with a red run in the meantime — who may override it, on
  what grounds, and where that is written down
- Gets the change agreed with the team rather than imposing it, or doing it quietly at night

## Weak signals

- Presses the button again and ships on the second green
- Makes the failures stop appearing rather than stop happening
- Removes whatever is failing from the run
- Treats it as something the team has learned to live with
- Proposes starting the whole suite again from scratch

## Answer bands

### weak

- Runs it a second time and ships on the green, with no account of what that proved.
- Proposes deleting or permanently skipping whatever fails.
- Has no way of deciding which failure to look at first.

### mid

- Looks at the actual failures in today's run before deciding anything about the release.
- Collects which tests fail and how often, and works on the worst offenders first.
- Says what made each one unreliable instead of making it pass.

### senior

- States that the suite currently cannot fail meaningfully, so this afternoon's release is going
  out on no evidence, and says what they would put in its place for today.
- Sets the worst offenders aside to restore the signal at once, with a deadline and an owner on
  each, and a rule for what happens to one nobody comes back to.
- Goes looking for the defect that already escaped through the habit, and uses it as the argument
  for the work.
- Prefers a smaller suite the team believes to a larger one it does not, and says what is given
  up by that.

### lead

- Makes the case to whoever controls the roadmap in terms of escaped defects and decisions taken
  on no evidence, and secures the time rather than hoping for it.
- Sets a standard for new tests so the problem stops being refilled while it is being drained.
- Writes down what the team may do with a red run, so overriding it is a visible act with a name
  against it rather than a reflex.
- Puts a number on where the rate should be in a month and reports against it.

## Follow-ups

- Two weeks in, one run in twenty fails and people are still pressing the button again. What now?
  probes: whether they see that trust is a habit, rebuilt deliberately rather than earned by the
  numbers alone
- One of the ones you were about to set aside turns out to go wrong only when it runs after one
  particular other one. Is that a fault in the test, or in the code?
  probes: whether they will entertain that a failure the team waved through has been telling the
  truth about the system
- You look back over six months and find that exactly one of the failures people waved through
  was real. Does that change what the suite is worth keeping?
  probes: reasoning about the value of a signal from its hit rate, in both directions, rather
  than defending the suite or abandoning it
