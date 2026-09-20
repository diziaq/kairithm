---
id: database-choosing-a-store-forty-thousand-sensors-01
schema_version: 1
title: Forty thousand sensors, and two very different queries
category: database
topic: choosing-a-store
level: senior
tags: [data-modelling, scalability, performance]
time_estimate_min: 10
order: 360
links:
  deeper: [database-choosing-a-store-second-cluster-for-six-people-01]
  related: [database-column-oriented-orders-in-bigquery-01]
---

## Ask

Forty thousand sensors each send three numbers every ten seconds. Nothing is ever edited or
deleted. Customers look at one sensor's last 24 hours on a chart; analysts chart monthly averages
across the whole fleet. Pick a store, and tell me what you give up by not picking the other two
you considered.

## Tests

Whether the candidate can turn a stated workload into a concrete choice and reject the
alternatives by the queries they handle badly, rather than by listing properties of each product.

## Listen for

- Reads the workload back as two unlike queries: a narrow slice of one sensor over a day, and one
  number swept across everything for a month
- Picks something that keeps a sensor's history contiguous by time, so the customer chart is a
  range read and the fleet chart touches one number per row
- Uses "nothing is ever edited" as evidence, and says what that removes the need to protect
  against
- Turns down a key-value or wide-column option by naming the fleet-wide query it cannot answer
  without a second system alongside it
- Turns down a document store on the per-item overhead at this rate, while acknowledging that
  purpose-built time-series support exists there too
- Turns down a plain row store on the write rate and on the month-long sweep, with an estimate
  rather than a slogan
- Asks how long data is kept and how old data leaves, because at this rate that is part of the
  choice
- Asks how fresh each of the two audiences needs the data to be

## Expected knowledge

- A store that answers a key-range read quickly does not thereby answer a whole-field sweep
  quickly
- At this arrival rate, how data is aged out is part of choosing, not an afterthought

## Strong signals

- Works out an order of magnitude for arrivals per second and bytes per day before choosing
- Names the point at which one store stops covering both queries and says what the second system
  would then be
- Asks what the team already runs before treating every option as equally free

## Weak signals

- Names a product and defends it with a general property rather than with one of the two queries
- Says relational databases do not scale
- Answers "it depends" and does not say what on

## Answer bands

### weak

- Names a product and defends it with a general property — it is fast, it scales, everyone uses
  it for this.
- Says relational databases cannot handle this, with no number behind it.
- Says it depends, and cannot say what it depends on.

### mid

- Pulls the two queries apart and says they pull the design in different directions.
- Makes a choice and ties it to one of the two queries.
- Rejects one alternative for a reason taken from the workload rather than from a list of
  features.

### senior

- Says how rows would be laid out — by sensor, then by time — and why both queries are then cheap
  reads rather than searches.
- Rejects each alternative by naming the query it serves badly, not the feature it lacks.
- Uses the fact that nothing is edited to justify dropping machinery a general-purpose store
  would insist on.
- Estimates arrival rate and stored volume out loud, and says which figure would change the
  choice.
- Asks how long the data is kept and how it leaves before committing.

### lead

- Names the threshold at which one store stops serving both audiences, and what the split looks
  like then.
- Weighs what the team can already operate against what the workload would ideally have.
- Says what would have to be true in six months for the choice to be revisited.

## Follow-ups

- The analysts now want to filter by a sensor's model, its firmware and its site. Those live in
  another system, forty thousand rows of them. Does your pick survive?
  probes: pairing a tiny descriptive set with an enormous measurement set, and whether the chosen
  store can do it at all
- A customer exercises their right to have everything from their 300 sensors erased. How bad is
  that for you?
  probes: removal from a store optimised for arrival, and whether they thought about how data
  leaves
- Same question, a tenth of the size: four thousand sensors, one reading a minute. Same answer?
  probes: whether the choice was driven by the shape of the queries or only by the big number

## Notes

Figures to release when asked, and credit the candidate who asks: 40,000 sensors at one reading
per ten seconds is about 4,000 arrivals a second and roughly 345 million rows a day; three
numeric fields plus a sensor id and a timestamp; kept 13 months; customer charts must answer in
well under a second for around 50 concurrent users; analysts tolerate ten seconds or more.

There is no single right product. ClickHouse, TimescaleDB and InfluxDB are all defensible; so is
a row store plus a rolled-up summary table if the candidate prices it honestly. What is being
marked is whether the rejections are argued from the two queries. Accept a rejection of Cassandra
or DynamoDB only if it names the fleet-wide sweep, and accept a rejection of MongoDB only from a
candidate who knows it has time-series collections and says why they still would not.

Expect compression to be large on this shape — repeated ids and slowly changing numbers — but do
not hold a candidate to a ratio.

## Sources

- https://clickhouse.com/docs/en/intro
- https://www.mongodb.com/docs/manual/core/timeseries-collections/
- https://docs.timescale.com/use-timescale/latest/hypertables/
