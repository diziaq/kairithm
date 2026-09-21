---
id: database-orm-platform-commitment-01
schema_version: 2
title: The engineer who wrote the mapping layer leaves in five weeks
category: database
topic: orm
level: lead
tags: [maintainability, operations, ownership, api-design]
time_estimate_min: 12
order: 405
links:
  related: [database-choosing-a-store-second-cluster-for-six-people-01, spring-auto-configuration-shared-starter-01]
---

## Ask

Four services on your platform share one entity mapping layer, written mostly by one engineer who
leaves in five weeks. A new team wants to start their service on something different and has
asked you to approve it. What do you need to know before you answer, and what does the platform
sign up for either way?

## Tests

Whether the candidate treats a data access choice as a long-lived commitment owned by an
organisation rather than by a project, and can price a second one honestly instead of ruling on
taste.

## Ideal minimal answer

Say up front what would make it a no, and plan the five weeks: what comes out of the leaver's
head, to whom, and how we know it worked. A second approach is paid for by the platform in
review, shared libraries, upgrades and on-call, so name what today's layer already costs, who
owns the four services afterwards, and the date and evidence that settle the trial.

## Listen for

- Asks what the departing engineer actually holds that is not in the repository: the conventions,
  the two or three odd mappings, and why they are that way
- Says a second approach is not free at the platform level and names where it lands: hiring,
  review, shared libraries, on-call runbooks, upgrades, the next security patch
- Separates one team trying something from the platform adopting it, and says what would have to
  be true to move from the first to the second
- Asks what must stay common across the boundary — a schema, a library, a transaction — before
  allowing the two to diverge
- Puts a date and a decision rule on the trial: what evidence gets collected, who reads it, and
  what happens if it is not convincing
- Asks who moves four services when a major version of the older stack lands

## Expected knowledge

- That a data access choice outlives the team that made it
- Roughly what it costs to move a live service from one layer to another, and that it is rarely
  a rewrite of one class

## Strong signals

- Uses the five weeks deliberately: names what has to come out of one head and how
- States in advance what would make them say no, not only what would make them say yes
- Asks what the platform already pays for today's choice, so the comparison has a real baseline
- Notices that four services on a layer nobody owns is already the bigger problem, with or
  without the new team

## Weak signals

- Refuses on the grounds of uniformity, with no cost stated on either side
- Approves it because the team is keen and morale matters
- Assumes the departing engineer can be replaced by reading the code
- Asks for a written proposal and stops there

## Answer bands

### mid

- Names the risk of one person holding the knowledge and asks for it to be written down.
- Says a second approach means two things for the platform to learn and keep working.

### senior

- Prices the second approach past the first sprint: review, shared code, upgrades, who is paged.
- Asks what has to stay common between services and what is allowed to diverge.
- Sets what the trial must show and by when, and says what happens if it does not.
- Separates the leaver problem from the new-team problem instead of treating them as one.

### lead

- States the condition for refusal up front, so the answer is not a matter of who argues longest.
- Plans the five weeks: what is transferred, to whom, and how anyone will know it worked.
- Names who owns the move if the new approach wins, and who keeps the four older services alive
  while attention is elsewhere.
- Says what the platform pays today, so the new cost is compared against something real.

## Follow-ups

- The new team ships, it goes well, and two more teams ask for the same thing. What did you put
  in place in month one that makes that conversation short?
  probes: whether the trial had a decision rule agreed in advance, or is settled by enthusiasm
- Six months on, nobody can say why one table is mapped the way it is. What should have happened
  in the five weeks?
  probes: getting knowledge out of one head before it walks, and what form it has to take
- A major version of the older stack lands and needs work in all four services. Who does it?
  probes: ownership of dull maintenance once the interesting work moved elsewhere
- The new team's service has to read a table the other four write. Does that change your answer?
  probes: shared schema as the real coupling; where the boundary should have been

## Notes

Either answer can be right. What separates a lead answer is whether the decision comes with a
condition, an owner and a date, and whether the candidate notices the leaver is the urgent half
of the question while the approval is the loud half.
