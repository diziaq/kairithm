---
id: sap-jco-performance-nightly-bulk-extract-01
schema_version: 2
title: Two million rows a night through an RFC
category: sap-jco
topic: performance
level: lead
tags: [performance, operations, consistency, data-volume]
time_estimate_min: 10
order: 240
---

## Ask

You have to get two million rows of material and stock data out of SAP every night into your data
platform, inside a three-hour window, and the run has to survive being interrupted. How do you
approach it, and when would you tell the business that a function-call interface is the wrong
tool?

## Tests

Whether the candidate can design a bulk movement with a resumption story and a capacity budget,
and whether they will recommend leaving the tool they are being interviewed on when it does not
fit.

## Ideal minimal answer

Challenge the two million first — a delta with a periodic reconciliation is usually the right
shape — then chunk on a stable key so no call hits the dialog runtime limit and an interrupted
run resumes, with parallelism bounded by an agreed share of SAP capacity. Name the conditions
that make this the wrong tool, and say that replacing it is a commercial decision, not mine
alone.

## Listen for

- Breaks the problem into selection inside SAP, transfer, and load on their side, and says which
  they would measure first
- Chunking on a stable key so an interrupted run resumes instead of restarting, and so no single
  call runs long enough to hit the runtime limit on the SAP side
- Challenges the two million: a delta based on change records or a timestamp, with a periodic
  full reconciliation, is usually the right shape and nobody revisited it
- Parallelism bounded by an agreed share of SAP capacity rather than by their own thread pool
- Says when this is the wrong tool — sustained bulk movement, growing volume, a window that
  keeps tightening — and what else exists: a dedicated extraction or replication mechanism, or
  files
- Is honest that the alternatives cost licence, ownership and a new operational surface, and
  that the choice belongs to Basis, the data platform team and the business together
- How the consumer knows what they have: a clear "data as of" marker, and what happens when the
  run is late

## Expected knowledge

- A long single call inside SAP is bounded by the runtime limit on its work process
- A full reload and a delta have different failure and correctness properties

## Strong signals

- Designs for the run that dies at half past two: resume point, a load that tolerates a repeat,
  and no half-visible state for consumers
- Asks what the consumer actually needs before agreeing to move two million rows at all
- Says how completeness is proved, not assumed — counts or checksums reconciled against the
  source
- Names the point at which they would stop optimising and escalate the architecture decision

## Weak signals

- Answers only with threads and batch sizes
- Promises a full extract will always fit the window as volume grows
- Cannot say what a consumer sees while the load is halfway through

## Answer bands

### mid

- Chunks the extract and runs some of it in parallel.
- Knows a restart from the beginning would not fit the window.

### senior

- Makes the run resumable and says exactly what the resume point is.
- Moves to a delta and can defend the reconciliation that keeps it honest.
- Bounds parallelism by the far side's capacity and asks who owns that number.

### lead

- Puts the volume requirement itself on the table before designing around it.
- Names the conditions under which this interface should be replaced, and who decides.
- Weighs the alternatives on ownership and cost, not only on throughput.
- Defines what consumers are promised — freshness, completeness, and what happens when the run
  is late.

## Follow-ups

- The run dies at half past two. What does the data platform see at three?
  probes: partial visibility, and whether consumers are shielded from an incomplete run
- The business says a delta is too risky because something might be missed. How do you answer?
  probes: reconciliation as the control that makes a delta safe
- Volume doubles next year. Which part of your design breaks first?
  probes: whether they know where their own headroom runs out
- You propose a different mechanism and the answer is that there is no budget. What now?
  probes: living within constraints and stating the risk clearly

## Notes

Verified: the runtime ceiling the chunking argument rests on is real. A call from an external
client is executed in a dialog work process, which has a maximum runtime, and work that needs
longer belongs in background processing, which is not bound by it. The dialog-timeout card in the
work-processes topic owns that mechanism in detail.

NEEDS-REVIEW — retained deliberately and permanently. Re-examined against the decompiled JCo and
SAP IDoc jars, which settle nothing here and never will: a client library cannot tell you what a
customer is licensed for. The card asks the candidate when a function-call interface is the wrong
tool and what else exists. Product names, their availability on a given release, and above all
what a customer is entitled to use differ per landscape and per contract, so no verifiable
general statement is possible.
Credit a candidate for knowing that dedicated extraction and replication paths exist, that
choosing one is a commercial decision as much as a technical one, and that the decision is not
theirs alone. Do not credit or penalise a specific product name, and do not name one yourself —
whatever you have in mind may not be what this customer owns.

## Sources

- https://help.sap.com/doc/abapdocu_751_index_htm/7.51/en-US/abenrfc_dialog.htm
- https://help.sap.com/doc/abapdocu_751_index_htm/7.51/en-US/abenapp_server_resources.htm
