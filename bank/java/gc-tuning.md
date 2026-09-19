---
title: A service pauses for two seconds every few minutes. How do you find out why?
difficulty: 4
tags: [jvm, gc, performance, diagnosis]
time_minutes: 7
order: 30
---

## Ask

A Java service pauses for about two seconds every few minutes. Latency graphs show it, the CPU
graphs do not. What do you look at, in what order?

## Look for

- Asks for evidence before changing a flag: GC logs, the pause type, the collector in use
- Separates a long young collection from a full collection and from a safepoint pause that is not
  garbage collection at all
- Names one non-GC cause, for example a long safepoint from biased lock revocation or a slow
  `System.gc` from a library
- Changes heap size or collector only after the log says which one is the problem

## Red flags

- Starts by raising the heap
- Suggests calling `System.gc` more often
- Cannot name a single flag that turns GC logging on

## Follow-ups

- The log shows a two second young collection. What does that tell you about the live set?
- How would you tell a GC pause apart from a blocked thread pool?
