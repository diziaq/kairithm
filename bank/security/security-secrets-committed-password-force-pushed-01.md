---
id: security-secrets-committed-password-force-pushed-01
schema_version: 2
title: The password was force-pushed out of the history
category: security
topic: secrets
level: mid
tags: [security, operations, ownership]
time_estimate_min: 8
order: 170
links:
  related: [general-incidents-first-fifteen-minutes-01]
---

## Ask

Somebody finds our production database password in a commit from eight months ago. They rewrite
the history to take it out, force-push, and close the ticket. Is the ticket closed?

## Tests

Whether the candidate puts rotation first and understands what a history rewrite does and does not
reach.

## Ideal minimal answer

No. Treat the password as disclosed and change it first; the rewrite is tidying up. It does not
reach forks, other people's clones, build logs, or the host's own cached views of the old commits.
Eight months is long enough that you also go looking for whether anybody used it.

## Listen for

- Puts changing the password first and the rewrite second
- Says the old commit survives where the rewrite cannot reach: forks, clones on other machines,
  build logs, the host's cached view of the object
- Treats the eight months as the point — assume it was read, then go and look
- Says what changing it means concretely: a new password, the old one disabled, every consumer
  updated, in an order that does not take the service down
- Adds something that catches the next one: a scan before the push, and somewhere secrets are
  meant to live instead

## Expected knowledge

- A rewrite of Git history does not remove the old objects from copies of the repository
- A secret that has been readable must be treated as used

## Strong signals

- Asks what that password reaches, because that sets how fast this has to move
- Says the rewrite has its own cost: everyone resets their clone, and open branches break
- Goes into the access logs for the eight months rather than assuming nothing happened
- Says who has to be told, and whether anything here is reportable
- Asks how it got there, and whether the same value is in other places too

## Weak signals

- Accepts the rewrite as the fix
- Schedules the change for the next release window
- Says the repository is private, so nobody outside could have seen it
- Recounts a past leak without saying what happens to this one
- Changes the password and says nothing about what else has to change with it

## Answer bands

### weak

- Says the secret is gone because it is no longer in the history.
- Does not mention changing the password.

### mid

- Says the password has to be changed and the rewrite alone does not do it.
- Names one place a copy of the old commit still sits, once asked.

### senior

- Puts changing the password first and the cleanup second before being asked, and says why that
  order.
- Names what the password reaches and uses it to set how fast this moves.
- Goes looking for use over the eight months rather than assuming there was none.
- Names the control that catches the next one before it lands.

## Follow-ups

- They ask why it matters, given the old commit is no longer on the default branch. What do you
  say?
  probes: the copies a rewrite cannot reach
- Changing that password takes four services down if you get the order wrong. How do you sequence
  it?
  probes: rotation as an operation with a plan, not a single click
- It is eight months old. What do you do beyond changing it?
  probes: looking for evidence of use, and who needs telling
- How do you stop the next one landing?
  probes: a check before the push, and where secrets are supposed to live

## Sources

- https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
- https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning
- https://owasp.org/Top10/2025/A02_2025-Security_Misconfiguration/

## Notes

GitHub's own page on this is unambiguous about the order, and is worth quoting to a candidate who
gets it backwards: "if the sensitive data you need to remove is a secret (e.g.
password/token/credential), as is often the case, then as a first step you need to revoke and/or
rotate that secret." On the rewrite it says the commits "may still be accessible elsewhere" — in
clones or forks of the repository, in cached views on the host, and in references attached to pull
requests — and that you cannot remove them from a colleague's clone yourself.

So the rewrite is not worthless; it is just second, and it is the part with the operational cost.
Everybody's local clone has to be reset, and in-flight branches are rebased or lost.

The strongest signal on this card is usually the third follow-up. Changing a database password is
not one action: it is provisioning a second credential, rolling consumers onto it, then disabling
the first — and a candidate who has done it says so, rather than treating rotation as a button.
The second strongest is going to look. Eight months of access logs either show a login from
somewhere that makes no sense, or they do not, and either answer is worth having before anybody
decides whether this is a breach.
