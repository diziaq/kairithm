---
id: sap-jco-troubleshooting-oncall-without-sap-access-01
schema_version: 2
title: On call at two in the morning for a system you cannot log into
category: sap-jco
topic: troubleshooting
level: lead
tags: [operations, observability, ownership, failure-modes]
time_estimate_min: 10
order: 250
---

## Ask

Your team has just picked up out-of-hours support for six SAP interfaces. At two in the morning
almost every question — did it post, why did it fail, is anything piling up — can only be
answered on the SAP side. Basis work office hours, and security will not give your on-call
engineers logins to the production system. What do you put in place, and what does each option
cost the people who have to live with it?

## Tests

Whether the candidate can choose between access, pushing the other system's state out, and making
their own side self-sufficient, under a real constraint — and can price each one in work that
somebody keeps doing after the project ends.

## Ideal minimal answer

Start from the decision at two in the morning (wait, re-run, or wake somebody) and buy only the
evidence it needs. Price each route in standing effort: a display-only role is a quarterly
access review; having SAP publish error and backlog counts outward lives on another team's
transport schedule; recording outcomes on our own side covers all six but cannot see a dump;
then fund the six differently.

## Listen for

- Starts from the decision that has to be made at two in the morning — wait, re-run, or wake
  somebody — and works back to the minimum evidence that decision needs, rather than asking for
  everything that could be visible
- Option one, a narrow display-only role for the named people on the rota: cheapest to build,
  but it is an access review every quarter, a joiner-leaver process, and four uses a year means
  nobody remembers how by the time they need it
- Option two, having the SAP side publish its state outward — error and backlog counts into the
  same dashboards and alerts as everything else: the best answer at two in the morning, but the
  code lives in another team's landscape, moves on their transport schedule, and goes quietly
  stale when nobody is testing it
- Option three, making the Java side answer for itself — every call carrying an identifier, the
  outcome and the document keys recorded: fully owned by the team, but it is work on all six
  interfaces, it costs retention, and it still cannot see a dump, a queue, or anything SAP did on
  its own
- Option four, changing the contract instead: paying for cover on the SAP side, or agreeing with
  the business that some of these interfaces simply wait until morning
- Says which interfaces need which: an overnight extract that can be re-run at seven is not the
  one that stops lorries leaving at six
- Detection and the runbook matter more than access: knowing at 02:05 that nothing has moved
  since midnight beats being able to browse at 09:00

## Expected knowledge

- Errors on the SAP side live in places the Java team cannot reach — short dumps, the tRFC and
  queue monitors, IDoc status
- Anything built on the ABAP side is owned, transported and released by another team

## Strong signals

- Asks what the business actually loses per hour for each of the six before deciding what to fund
- Proposes a different answer per interface instead of one policy for all of them
- Counts the standing cost of every option in somebody's week, not just the build
- Pushes back on "24/7 support" for interfaces where the only safe night action is to wait
- Puts a date on reviewing whether the alerts still fire, because a silent monitor is worse than
  none

## Weak signals

- Asks for broad production access and treats the refusal as an obstacle rather than a constraint
- Proposes a dashboard with no owner, no threshold and nobody to wake
- Accepts on-call for six interfaces without asking what the engineer is meant to do at two in
  the morning
- Answers with a list of transaction codes the on-call would need

## Answer bands

### mid

- Asks for read access and an escalation path to Basis.
- Wants more logging on the Java side, without saying what question it answers.

### senior

- Names two or three routes and picks one, with reasons tied to the constraint given.
- Specifies alerts with thresholds and an owner, not a screen someone might look at.
- Writes down, per interface, what the night action is and when it is safe to re-run.

### lead

- Puts a price on each route in continuing effort and says who carries it every week.
- Separates the interfaces by what an hour of delay costs, and funds them differently.
- Negotiates the support contract as one of the options, rather than absorbing it silently.
- Says how they will know a year later that the arrangement still works.

## Follow-ups

- Basis offer your on-call a read-only login tomorrow. What do you still want after that?
  probes: whether access alone answers the 02:00 question, and who trains the rota
- The other team agrees to build the piece on their side, in their next release, three months
  out. What do you do in the meantime?
  probes: an interim that the team owns, and not letting the gap sit unmanaged
- One of the six can safely wait until the morning. Who gets to decide that, and how does the
  engineer at two in the morning know it?
  probes: pushing the decision into a written runbook instead of a judgement call at night
- A year on, an alert has been firing into a channel nobody reads. How would you have caught that
  earlier?
  probes: treating the detection path as something that is itself tested

## Notes

This is a trade-off card, not a transaction-code card. A candidate naming `ST22`, `SM58` or
`SMQ2` has not answered it; a candidate who says what each route costs the team every week for
the next two years has.

The strongest answers treat detection time as the variable that matters and access as one of
several ways to buy it.
