---
id: database-document-stores-review-array-grows-01
schema_version: 1
title: Forty thousand reviews inside one product document
category: database
topic: document-stores
level: junior
tags: [data-modelling, performance, scalability]
time_estimate_min: 6
order: 300
links:
  deeper: [database-document-stores-surname-in-eleven-thousand-orders-01]
---

## Ask

A product catalogue in MongoDB keeps each product as one document, with every customer review
embedded in an array inside it. One popular product now carries forty thousand reviews in its
document and the product page has become slow. What is happening, and what would you change?

## Tests

Whether the candidate can say what embedding costs once the embedded list has no natural bound,
and choose between keeping it and moving it out for a stated reason.

## Listen for

- Loading the product loads every review with it, even though the page shows a handful
- The array has no upper bound — reviews only ever arrive, so the document only ever grows
- A document is the unit of read and write, so adding one review touches the whole record
- Proposes reviews as their own records carrying the product's id, with the page fetching them
  separately
- Keeps the small, bounded things on the product — a count, an average rating, the few newest —
  so the common page stays a single read
- Knows MongoDB refuses a document over a fixed size, so this shape eventually stops working
  outright rather than just getting slow

## Expected knowledge

- A document is read and written as a whole, not field by field
- MongoDB refuses a document above a fixed size ceiling

## Strong signals

- Asks what the product page actually renders before deciding what belongs in the document
- Separates data that is bounded and always wanted with its parent from data that accumulates
  forever

## Weak signals

- Says embedding is always right because a review belongs to a product
- Proposes an index over the array and expects the page to get faster, without noticing the whole
  record still travels
- Blames MongoDB as a product rather than the shape that was chosen

## Answer bands

### weak

- Says the wrong database was chosen and a relational one would be faster, without saying what
  the slow read is doing.
- Proposes an index and expects that to fix the page.
- Treats embedding as automatically correct because a review belongs to a product.

### junior

- Says the entire record, all forty thousand reviews included, is fetched to render a page that
  shows a few.
- Notices the array has no limit and keeps growing while the rest of the record does not.
- Proposes storing reviews separately, keyed by the product they belong to.

### mid

- Sorts the fields into those that are bounded and read with the parent and those that grow
  without end, and places each accordingly.
- Keeps a small rolled-up summary on the product so the common page is still one fetch, and names
  what that summary can get wrong.
- Says what the split costs: a second round trip, and two places that can disagree.
- Raises the hard size ceiling as the point where the current shape fails outright.

## Follow-ups

- The page only ever shows the ten newest of them. Does that change what you keep on the product?
  probes: whether they shape the record from the read the page actually makes, rather than from
  what belongs to what
- A customer posts one new review. What work does that single review cause?
  probes: that the unit of update is the whole record, and what that means at this size
- The reviews move out, and the page now makes two round trips where it made one. Is that still a
  win?
  probes: whether they can price the split honestly instead of presenting it as free

## Notes

Figures to release when asked, and credit the candidate who asks: the page shows the ten newest
reviews and the average rating; reviews average roughly 400 bytes; the worst product is a little
over 15 MB and still growing. MongoDB's BSON document limit is 16 MB.

A candidate who says "keep the newest few embedded and the rest outside" has given a good answer,
not a hedge — that is the shape most catalogues end up with.

## Sources

- https://www.mongodb.com/docs/manual/core/document/
- https://www.mongodb.com/docs/manual/data-modeling/
