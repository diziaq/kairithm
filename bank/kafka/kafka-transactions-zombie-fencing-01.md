---
id: kafka-transactions-zombie-fencing-01
schema_version: 2
title: Two instances think they own the same input partitions
category: kafka
topic: transactions
level: lead
tags: [transactions, idempotency, correctness, operations]
time_estimate_min: 12
order: 88
---

## Ask

A transactional producer freezes on a long garbage collection pause, the orchestrator declares it
dead and starts a replacement, and then the original wakes up and carries on writing. Both are
now producing for the same input partitions.

You own the platform every pipeline in the estate runs on. What stops the duplicates here, and
which way of naming a producer would you standardise on across all of them?

## Tests

Whether the candidate can explain what displaces an older producer, then choose an identity
scheme against how the instances are actually scheduled, and say what each candidate scheme costs
the people who run and rescale the pipelines.

## Ideal minimal answer

The transactional id makes the two processes one logical producer: the newer one raises the epoch
and the older one's writes are rejected, so it dies rather than corrupting the output, and the id
has to be derived from the work rather than the process. Put two naming schemes side by side,
pick one for the estate, and say what each costs when a topic is widened.

## Listen for

- Says the transactional id is what makes the two processes one logical producer, and the newer
  one raises an epoch that locks the older one out
- Knows the locked-out instance has its writes rejected and fails, rather than corrupting the
  output
- Points out the id must be stable and derived from the work being handled, not generated per
  process, or nothing is ever locked out
- Says an id made up fresh at every start gives two live writers and no defence at all
- Puts at least two schemes side by side — one identity per slice of input, or leaning on the
  group's own membership to do the fencing — and says which the estate can actually run
- Asks what happens to the naming when the topic is widened, since a scheme tied to the input
  layout has to be revisited the moment that layout changes

## Expected knowledge

- A producer with such an id finishes or rolls back its predecessor's transaction when it starts
- Only the most recent holder of an id is permitted to write

## Strong signals

- Notices that an id tied to the process breaks as soon as the work is handed to a different
  instance
- Says what the frozen instance experiences, and that it must be allowed to die rather than keep
  trying
- Asks how many such identities exist across the estate and what that costs the brokers

## Weak signals

- Says transactions make it safe, with no account of what identifies a producer
- Builds the id from the hostname or a random value and sees no problem
- Believes the orchestrator's decision is enough to stop the old process writing

## Answer bands

### mid

- Says both instances would otherwise write, and something has to lock one of them out.
- Knows the producer carries a name that outlives a single process.

### senior

- Names raising the epoch as the mechanism, and says what the older instance gets back when it
  writes.
- States that the name has to come from the work, not from the process.
- Describes what the locked-out process should do instead of trying again.

### lead

- Puts the candidate schemes beside each other and picks one for the estate, saying what each
  costs whoever rescales or reschedules a pipeline.
- Names what the chosen scheme leaves behind to maintain: names that have to be regenerated when
  the input is widened, or a dependency on a client version the older pipelines are not on.
- Says how the team would discover this was misconfigured before an incident rather than after.
- Decides which pipelines justify the machinery at all, and what the others get instead.

## Follow-ups

- The name is generated fresh at every start-up from a random value. Does anything still stop the
  older process writing?
  probes: whether they see that a new name is simply a second producer, not a replacement
- The work an instance handles moves to a different instance after a restart. Does the naming
  scheme survive that?
  probes: the identity has to follow the input partitions, not the process
- How would you find out today whether any pipeline on the platform has this wrong?
  probes: auditing and observability rather than trusting the original design
- The topic one of these pipelines reads is widened from six partitions to twenty-four. What does
  that do to the scheme you just chose?
  probes: that a name tied to the input layout has to be reissued, and who is on the hook for
  remembering

## Sources

- https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging
- https://cwiki.apache.org/confluence/display/KAFKA/KIP-447%3A+Producer+scalability+for+exactly+once+semantics

## Notes

The constraints are held back deliberately. Release them if the candidate asks what the estate
looks like, and credit the ones who ask before choosing: instances are rescheduled onto fresh
hosts several times a week, the topics they read are widened from time to time, and the estate
mixes hand-written read-process-write loops with Kafka Streams applications. A candidate who
picks a naming scheme without asking any of that has answered a smaller question than the one
being asked.

The classic guidance is to derive the transactional id from the input partitions an instance
handles, so that the identity follows the work rather than the process. Its cost is that the set
of names is a function of the input layout: widen the topic and the names have to be reissued.

Which alternative is available is version-dependent and the card should not assert one as
universal. Since KIP-447 (Kafka 2.5) a consume-transform-produce loop can send offsets with the
consumer group metadata, and the group coordinator fences on the group's generation, so Kafka
Streams no longer needs one transactional id per input partition. A candidate who answers in
those terms is right for a recent client and wrong to assume it everywhere — the older scheme is
still what a 2.4-or-earlier pipeline is running.

What matters either way is that they see a random or per-process name is not a weaker defence but
no defence: it makes the two instances two unrelated producers, so nothing is ever fenced.
