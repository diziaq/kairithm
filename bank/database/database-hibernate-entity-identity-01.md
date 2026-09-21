---
id: database-hibernate-entity-identity-01
schema_version: 2
title: Two new lines go into the set and one comes out
category: database
topic: hibernate
level: mid
tags: [correctness, data-modelling, failure-modes]
time_estimate_min: 8
order: 415
links:
  deeper: [database-hibernate-batch-insert-01]
  related: [spring-testing-rollback-never-commits-01]
---

## Ask

An `Order` holds its lines in a `Set`. A test builds two brand-new `OrderLine` objects, adds both
to the set, and the set has one element. `equals` and `hashCode` are the generated ones, built
from the id. In another test one line is added, the order is saved, and then `set.contains(line)`
comes back false. Explain both.

## Tests

Whether the candidate can reason about an object's identity across its whole lifecycle — before
the row exists, while it is being watched, and after — instead of treating `equals` as a
formality the IDE fills in.

## Ideal minimal answer

Both objects are new, so their ids are null and equals sees one object; after the insert the id
changes, the hash changes with it, and the set looks in the wrong bucket. A hash must not change
while the object is in the collection, so give the entity an identity assigned before the row
exists, or a constant hashCode with equals still comparing the id.

## Listen for

- Before the row is written there is no id, so two fresh objects look like the same object to
  anything that compares on it
- Writing the row changes the value the hash was built from, so the object now sits in a bucket
  the set no longer looks in
- States the rule being broken: the hash must not change while the object is inside a hash-based
  collection
- Offers an identity that exists before the row does — a natural key, or a value assigned in the
  constructor — or a fixed hash with the id still compared
- Knows that inside one open unit of work the same row hands back the same instance, which is why
  `==` seems to work there and stops working across two of them
- Says where else the same defect bites: keys in a map, caches, and removing an element

## Expected knowledge

- That the id may be handed out by the database when the row is written
- The rule tying `equals` and `hashCode` together
- Hibernate 6 still returns one instance per row inside one open unit of work

## Strong signals

- Says a lazily loaded stand-in for a row must still compare equal to the loaded object, and what
  a naive `getClass()` check does to that
- Points out that an identifier the application assigns up front makes the whole question go away
  and costs almost nothing
- Distinguishes the test passing from the code being right: notes which of these two faults never
  shows up in a single-transaction test

## Weak signals

- Swaps the `Set` for a `List` and declares it fixed
- Deletes `equals` and `hashCode` and cannot say what stops working
- Puts every field in `equals`, including the collection of children
- Says the framework should handle this

## Answer bands

### weak

- Blames the framework or the test and gives no account of what the set is comparing.
- Believes two different objects cannot collide inside a set.

### junior

- Says neither new object has an id yet, so the set treats them as one.
- Says the value the set filed the object under changed when the row was written.

### mid

- States that the hash has to stay put while the object is inside the collection.
- Proposes an identity that exists before the row, or a fixed hash with the id compared.
- Says a list is not a fix, only a different set of problems, and names one of them.

### senior

- Explains that one row yields one instance inside one open unit of work, and why that hides the
  fault in some tests and not others.
- Handles the stand-in object that has not been read yet without breaking the comparison.
- Names the other places it bites: map keys, caches, removing from a collection.
- Says which convention the codebase should adopt for every entity, not just this one.

## Follow-ups

- A teammate swaps the set for a list and both tests go green. What did that settle, and what did
  it leave open?
  probes: whether they see the duplicate reaching the table rather than being caught in memory
- Inside one service method, two loads of the same row are compared with `==` and it does the
  right thing. Why should that not reassure you?
  probes: one instance per row inside one boundary, and what happens across two of them
- The child is reached through its parent and has not actually been read from the database yet.
  Does your rule still hold for it?
  probes: the stand-in object, and a class check that fails against it

## Sources

- https://docs.jboss.org/hibernate/orm/6.4/userguide/html_single/Hibernate_User_Guide.html#entity-pojo-identifier
- https://in.relation.to/2016/09/20/hibernate-tips-how-to-implement-equals-and-hashcode/

## Notes

The two symptoms are the same fault at two moments: a null id before insert, and a changed hash
after. Hibernate's own guidance is a natural key where one exists, or a constant `hashCode` with
`equals` comparing an id that is assigned early. A candidate who reaches for a UUID in the
constructor has given a legitimate answer — ask what it costs on the index.
