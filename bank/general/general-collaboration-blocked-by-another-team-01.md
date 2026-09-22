---
id: general-collaboration-blocked-by-another-team-01
schema_version: 2
title: Another team agreed three weeks ago, and nothing has happened
category: general
topic: collaboration
level: mid
tags: [ownership, delivery, collaboration]
time_estimate_min: 7
order: 130
links:
  deeper: [general-collaboration-two-engineers-stuck-01]
  related: [microservices-service-boundaries-lockstep-deploys-01]
---

## Ask

Your work needs a small change to an interface owned by another team. They agreed to it three
weeks ago and nothing has appeared. Your own deadline is in two weeks. What do you do?

## Tests

Whether the candidate can unblock themselves — through direct contact, alternatives and
escalation in that order — instead of waiting, or going around the other team and creating a
worse problem.

## Ideal minimal answer

Goes back to the other team to find out what the change is competing with rather than only
asking for a date, offers a cheaper route such as writing the patch themselves, and keeps
working against the agreed shape meanwhile. Warns whoever owns the deadline while there is still
time to act.

## Listen for

- Talks to the person directly before anything else, and asks what it would take rather than
  when it will be done
- Finds out where it sits on their priorities, which may be honestly nowhere
- Looks for what can be done in the meantime: build against the agreed shape, use a temporary
  stand-in, deliver the part that does not depend on it
- Offers to do the work themselves in the other team's repository, and asks how they would want
  that handled
- Raises it with their own manager as information, not as a complaint, before the deadline is at
  risk rather than after
- Tells whoever owns the deadline that it is at risk, early

## Strong signals

- Distinguishes a team that has deprioritised the work from one that has forgotten, and responds
  differently
- Keeps the relationship intact, because they will need this team again next quarter
- Writes down what was agreed, in a place both teams can see, so the next three weeks are not a
  repeat

## Weak signals

- Keeps waiting and raises it after the deadline is missed
- Copies in managers as the first move
- Builds a private workaround that duplicates the other team's data and tells nobody
- Escalates to their manager and considers the problem handed over

## Answer bands

### weak

- Waits, and reports the deadline as blocked when it arrives.
- Goes straight to management without talking to the other team.
- Builds a duplicate of what they needed and hides it.

### junior

- Contacts the other team again and asks for a date.
- Tells their own manager that the work is at risk.
- Starts on the parts that do not depend on the change.

### mid

- Asks what the work is competing with on the other team's list, rather than only for a date.
- Offers a route that costs them less: a patch, a smaller version, help from your side.
- Builds against the agreed shape so the wait does not stop progress, and says what that assumes.
- Gives whoever owns the deadline a warning with enough time to act.

### senior

- Sets a point at which waiting stops and the alternative starts, before anyone tells them it is
  not coming, and says so to both sides.
- Treats escalation as a joint act with the other team rather than a report against them.
- Looks at whether the dependency should exist at all, and what would remove it for next time.

## Follow-ups

- They tell you honestly that it is not going to happen this quarter. What is your next move?
  probes: whether they can replan rather than keep pushing, and who they involve
- You write the change yourself and send it to them. Two days later it has not been looked at.
  What does that tell you?
  probes: reading capacity versus willingness, and what escalation is actually for
- Your manager tells you to just work around it. What do you do?
  probes: whether a workaround is a considered decision with a cost, or an order followed quietly
