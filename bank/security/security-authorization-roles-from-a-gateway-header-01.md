---
id: security-authorization-roles-from-a-gateway-header-01
schema_version: 2
title: Another team starts calling the service directly
category: security
topic: authorization
level: mid
tags: [security, api-design, ownership]
time_estimate_min: 8
order: 130
links:
  related: [spring-web-layer-validation-missing-01]
---

## Ask

Our gateway checks the token and passes the user's roles on to each service in an `X-Roles`
header. The services read that header and nothing else. Another team has just started calling one
of those services pod to pod, to save the gateway hop. What worries you?

## Tests

Whether the candidate sees that a header is only worth something while every route in passes the
thing that sets it, and can say where the decision belongs instead.

## Ideal minimal answer

A caller that reaches the service without passing the gateway writes its own roles and the service
believes them. The header is worth something only while the gateway is the only way in. So either
the service checks the token itself, or the caller's identity is proved at the connection, or the
network stops anything but the gateway getting through.

## Listen for

- Says the header is a claim from the caller and the service has no way to tell who wrote it
- Asks what else reaches the service: another pod, a port forward, a scheduled job, a sidecar, an
  engineer's laptop
- Says the gateway removing the header on the way in does nothing for traffic that never goes
  through the gateway
- Offers a fix at the right layer: the service checks the token, or the caller proves itself on the
  connection, or the network admits only the gateway
- Separates the two questions the service is answering — who is calling, and what that caller may do

## Expected knowledge

- A header is data the caller sends and can set to anything
- A gateway can only enforce a rule on traffic that goes through it

## Strong signals

- Asks whether the other team's call should carry the end user at all, or its own service identity
- Points out every service behind that gateway has the same shape, and asks how many there are
- Wants the audit trail to record which caller the decision was made from
- Asks what the other team actually needed, because the hop they skipped may not be the problem

## Weak signals

- Says the gateway strips the header, so it cannot be forged
- Trusts the cluster network because it is internal
- Names mutual certificates as the whole answer without saying what then decides what the caller
  may do
- Tells the story of a past incident without saying what happens to this service
- Sets out verifying the token, proving the caller on the connection and closing the network, and
  will not say which one this service does

## Answer bands

### weak

- Says the gateway removes the header from outside traffic, so it cannot be faked.
- Treats the cluster as trustworthy because it is internal.

### mid

- Says the direct caller can put whatever roles it likes in the header.
- Names at least one other way into the service that misses the gateway.
- Proposes the service check the caller itself rather than read the header, once asked.

### senior

- Raises it themselves that the guarantee holds only while the gateway is the only door, and
  asks how that is enforced.
- Separates proving who the caller is from deciding what it may do, and says where each belongs.
- Asks how many other services share the same shape, and how they would be found.
- Says what the other team should be given instead, rather than only blocking them.

## Follow-ups

- The gateway team says it deletes that header on every request from outside, so it cannot be
  faked. Does that settle it?
  probes: that removing it covers only traffic that goes through the gateway
- The other team's job needs to read one customer's data. In whose name should that call be made?
  probes: the end user's identity versus the calling service's own
- You are asked how many of your services have the same shape. How do you find out by Friday?
  probes: whether they can sweep a fleet rather than fix one file

## Sources

- https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/
- https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- https://www.rfc-editor.org/rfc/rfc8705
- https://www.rfc-editor.org/rfc/rfc8693

## Notes

The trap is the reassuring reply, and it is technically true: a competent gateway does strip
inbound copies of its own trusted headers. It is also irrelevant, because the traffic in question
never touches the gateway. Candidates who have only ever drawn the architecture diagram stop at
the strip; candidates who have operated it ask what the ingress paths actually are.

Two distinct fixes, and they are not interchangeable:

- The service verifies the token itself (or re-derives roles from it). Removes the trust in the
  header entirely and works no matter how the request arrived. Costs every service a key source
  and a verify step.
- The network or the mesh makes the gateway the only reachable ingress, and service-to-service
  calls prove themselves with their own certificate (RFC 8705) rather than borrowing a header.

Worth pushing on the second follow-up. The right answer for the other team's job is usually its
own service identity plus a downstream token scoped to what it needs (RFC 8693 token exchange),
not the end user's access token forwarded onward — a forwarded user token is usable by every hop
it passes through, for everything the user can do.
