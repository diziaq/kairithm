---
id: security-web-security-strip-the-script-tag-01
schema_version: 2
title: The fix strips the script tag from the search box
category: security
topic: web-security
level: junior
tags: [security, correctness, testing]
time_estimate_min: 6
order: 150
links:
  related: [database-mybatis-placeholder-injection-01]
---

## Ask

Our search page echoes the query back: "No results for" and then what you typed. A tester pastes
a script tag into the box and gets a pop-up. The fix in the pull request removes `<script>` from
the text before it is used. Will that do?

## Tests

Whether the candidate knows that removing known-bad patterns is the wrong shape of fix, and can
name what the right one protects and where it happens.

## Ideal minimal answer

No. Plenty of things run without a script tag — an image tag with an error handler, for one — and
other spellings walk past a filter that matches one string. The value has to be escaped where it
is written into the page, so it is shown as text instead of read as markup.

## Listen for

- Gives one thing that gets past the filter: an image with an error handler, breaking out of an
  attribute, a different casing, a nested or split tag
- Says the value must be escaped at the point it goes into the page, not cleaned on the way in
- Knows the thing being fooled is the page, and the victim is whoever loads it
- Says a list of bad patterns is the wrong shape, and escaping for where the value lands is the
  right one
- Notices this page hands the text straight back, so a crafted link is enough and nothing has to
  be stored

## Expected knowledge

- Text put into a page raw is read as markup by the page
- Templates escape for you; building the page by hand skips that

## Strong signals

- Asks where else the value is written — inside an attribute, inside a link, inside a script block
  — and says the escaping is different in each
- Mentions a response header that stops inline script running even if something slips through, and
  calls it a second layer rather than the fix
- Asks whether the same text is later shown to other people, because that changes who gets hit
- Asks what the tester actually typed, rather than guessing

## Weak signals

- Adds more patterns to the list of things to remove
- Says validation on the form field solves it
- Says the library handles it, without knowing where this text is put into the page
- Says an attacker cannot reach the page without logging in

## Answer bands

### weak

- Adds more patterns to the list of things to remove.
- Cannot name anything that survives the filter.

### junior

- Names one thing the page runs that is not a script tag.
- Says the value should be escaped where it is written into the page.

### mid

- Says where the value lands decides how it has to be escaped, once asked.
- Points out a crafted link is enough here, with nothing saved anywhere.
- Treats a header restricting what script may run as a second layer rather than the fix.

## Follow-ups

- Give me one thing I could type that still runs after the pull request lands.
  probes: whether they have a concrete payload or only the category
- The same text also ends up inside a link on that page. Does your fix cover that?
  probes: that where the value lands changes what is safe
- This page saves nothing. Who gets hurt, and how do they end up on it?
  probes: a crafted link and somebody who clicks it, versus stored content

## Sources

- https://owasp.org/Top10/2025/A05_2025-Injection/
- https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy

## Notes

Two payloads to have ready if the candidate cannot produce one:
`<img src=x onerror=alert(1)>` has no script tag at all, and `<scr<script>ipt>` survives a single
pass that removes the literal string. Both are enough to show that matching known-bad text is the
wrong shape of defence.

The useful distinction to draw out: validation asks whether the input is the right shape for the
business, and happens once on the way in. Escaping asks what characters mean in the place the
value is about to be written, and happens at each output. They are not substitutes, and this bug
is an output problem being fixed at the input.

Injection moved to A05 in the OWASP Top 10 2025, down from A03 in 2021 — cite the current page
rather than a position a candidate may remember from an older list. Content Security Policy is
worth hearing about at the mid band, but a candidate who offers it *instead* of escaping has
inverted the order: it is the net under the fix, not the fix.
