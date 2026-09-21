---
id: spring-transactions-partial-save-01
schema_version: 2
title: The second save failed and the first one stayed
category: spring
topic: transactions
level: junior
tags: [transactions, correctness, failure-modes]
time_estimate_min: 5
order: 39
links:
  deeper: [spring-transactions-self-invocation-01]
---

## Ask

`CustomerService.register()` calls `customerRepository.save(customer)` and then
`addressRepository.save(address)`. The second save fails on a database constraint and the
failure reaches the caller. You expected to find nothing in either table, but the customer row
is sitting there. There is no `@Transactional` anywhere in this class. Why is that row still
there, and what do you change?

## Tests

Whether the candidate treats a transaction boundary as something somebody has to draw around a
unit of business work, rather than assuming consecutive writes are already grouped — and whether
they can say where that boundary belongs and how they would prove it holds.

## Ideal minimal answer

Nothing was holding the two writes together, so the first one was already committed by the time
the second ran. Declare one boundary on the service method so both writes are covered by it and
the failure undoes both; after that a failing second save leaves both tables empty.

## Listen for

- Nothing was holding the two writes together, so the first one was already committed by the
  time the second ran
- Says that "no annotation" does not mean "no transaction": the data-access layer opened and
  closed its own boundary around each call
- Puts the annotation on the service method, so both writes are covered by one boundary and the
  failure undoes both
- Knows the failure still reaches the caller; the change is about what is left in the tables,
  not about hiding it
- Would check the fix by making the second write fail on purpose and looking at the first table

## Expected knowledge

- That the framework starts a transaction when the annotated method is entered and ends it when
  the method returns or throws
- That a failure has to leave the method for the framework to act on it

## Strong signals

- Asks whether these two writes should be one write of a customer and its address together, so
  the situation cannot arise
- Says the boundary belongs where the business operation is, not on each data-access call
- Wonders whether every kind of failure would have undone the work, rather than assuming so

## Weak signals

- Deletes the first row by hand in a catch block
- Believes the database groups consecutive statements on its own
- Catches the failure, logs it, and returns normally
- Puts the annotation on the repository interface and cannot say what changed

## Answer bands

### weak

- Says the database should have undone both, with no account of what would have decided that.
- Proposes removing the first row by hand after the failure.
- Swallows the failure so the caller stops seeing it.

### junior

- Says the method needs one declared boundary around both writes, and puts it on the service.
- States that the first write had already been committed on its own before the second ran.
- Expects both tables to be empty after the fix and says how to see that for themselves.

### mid

- Explains that each data-access call opened its own boundary because none was already open.
- Says the boundary belongs at the entry to the business operation and can say why putting it
  further out or further in is worse.
- Points out that the failure still propagates, and separates that from what the tables hold.
- Writes the test that makes the second write fail and asserts the first table is empty.

## Follow-ups

- A third step in the same method sends the customer a welcome email. Does that get undone too?
  probes: effects outside the database that no rollback can reach
- Somebody moves your fix up onto the web endpoint that calls this method instead. Better or
  worse?
  probes: whether they can argue about where the boundary belongs, not just that it exists
- How would you show me the fix works, without clicking through the application?
  probes: a test that fails the second write deliberately and asserts on the table
- Suppose the second save had failed by throwing a type this team wrote, one the method
  signature has to declare. Would you still expect an empty table?
  probes: the ceiling — whether they know the framework treats failures differently

## Sources

- https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/annotations.html
- https://docs.spring.io/spring-data/jpa/reference/jpa/transactions.html

## Notes

Spring Data JPA's `SimpleJpaRepository` is annotated `@Transactional`, so each `save()` runs in
its own transaction when the caller has not started one, and joins the caller's when it has.
That is why the first row committed. The last follow-up is the doorway to the checked-exception
card and is not needed to pass this one.
