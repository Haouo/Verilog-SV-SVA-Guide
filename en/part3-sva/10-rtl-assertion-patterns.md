# Part III · 10. RTL Assertion Patterns

[← Binding and Placement](09-binding-and-placement.md) · [Table of contents](../README.md) · [Next: Local Variables →](11-local-variables.md)

## Learning objectives

- Recognize the recurring shapes that real RTL checks take.
- Write assertions for handshakes, stable-until-accept, and arbitration.
- Encode one-hot and gray-code invariants directly as properties.
- State FIFO safety: no overflow, no underflow, no read-when-empty.
- Guard data against `X` and note the limits of CDC checking in SVA.

This chapter is a pattern library. Each pattern pairs a worked SVA snippet with the
design intent it captures, so you can lift it into a real block and adapt the signal
names. All snippets assume a `default clocking @(posedge clk)` and a
`default disable iff (!rst_n)` are in scope, so the clock and reset are omitted for
focus.

## Designer's mental model

Assertion patterns are reusable translations from common RTL contracts to SVA.
A handshake, FIFO boundary, one-hot state, or no-unknown rule appears in many
designs; each time, the same questions return: what triggers the rule, what must
remain stable, what latency is allowed, and what failure should mean.

Use patterns as starting points, not as magic macros. Before copying a property,
name the protocol rule in words and choose the clock, reset, latency, and
vacuity check that match your block. The pattern gives structure; the design
context gives truth.

## Start from the problem

The previous chapters teach the syntax pieces. When writing real RTL checks, you
usually do not start with "I need an `s_until`." You start with "after `valid`,
`data` must not move," "a full FIFO must not be written," or "only one requester
can receive a grant." These rules recur across designs, often changing only signal
names, latency bounds, and reset conditions.

The pattern chapter translates common intents into SVA shapes you can adapt. For
each pattern, read the bug it protects against before reading the property. If your
protocol story differs, adjust the property instead of copying it mechanically.

## Request / acknowledge handshake

The most common protocol shape: a request must be answered within a bounded window.

```systemverilog
// Every request is acknowledged within 1..N cycles
property req_ack;
    $rose(req) |-> ##[1:N] ack;
endproperty
assert property (req_ack);
```

> **Design intent.** A request that is *eventually* answered is a liveness idea;
> giving it a real deadline (`##[1:N]`) turns it into a safety check a simulation
> can actually fail. Bound the window to the protocol's worst-case latency.

## Request stable until acknowledge

A request must not be withdrawn or changed before it is accepted:

```systemverilog
// req holds steady from assertion until ack arrives
assert property ($rose(req) |-> req s_until ack);

// If a payload travels with the request, it must hold too
assert property ($rose(req) |-> $stable(addr) until ack);
```

Hold-until-accept is what lets the receiver sample the request and its payload on
*its* schedule. Without it, the sender could change the data mid-transaction.

## Valid / ready stable until accept (stream style)

An AXI-stream-style channel transfers on a cycle where `valid && ready`. Until that
accepting cycle, `valid` must stay high and the data must not change:

```systemverilog
// Once valid is asserted without ready, it stays asserted and data holds
property vr_stable;
    (valid && !ready) |=> (valid && $stable(data));
endproperty
assert property (vr_stable);
```

> **Design intent.** This is the core contract of a ready/valid stream: the
> producer may not retract or mutate an offered beat until the consumer takes it.
> One assertion encodes the entire stability rule of the handshake.

## One-hot and one-hot-zero state

A one-hot signal carries exactly one set bit; one-hot-zero allows all-zero too.
These are invariants, checked every cycle with no antecedent:

```systemverilog
// FSM state register is strictly one-hot
assert property ($onehot(state));

// Grant bus is one-hot, or all-zero when idle
assert property ($onehot0(gnt));
```

A bad encoding — two states active at once, or a corrupted grant — fails the cycle
it occurs. `$onehot0` is the right choice whenever "none active" is a legal idle
condition.

## FIFO safety

A FIFO has three classic safety properties. State each as something that must
*never* happen.

```systemverilog
// No write into a full FIFO (would overflow)
assert property (wr_en |-> !full);

// No read from an empty FIFO (would underflow)
assert property (rd_en |-> !empty);

// Count never wraps past its bounds (depth = DEPTH)
assert property (count <= DEPTH);
assert property (!(full && empty));   // cannot be both at once
```

> **Design intent.** Overflow and underflow corrupt data silently and are hard to
> see in a waveform. As assertions they become loud, immediate failures at the
> exact cycle the rule breaks — the single most valuable check on a FIFO.

If push and pop happen together on a full or empty FIFO, the count must stay in
range; the bound `count <= DEPTH` plus the per-operation guards cover the corners.

## Gray-code single-bit change

A gray-coded counter (often a FIFO pointer crossing clock domains) must change by
exactly one bit per step. The check uses `$past` and `$countones`:

```systemverilog
// At most one bit differs between consecutive gray values
assert property ($countones(gray ^ $past(gray)) <= 1);
```

> **Design intent.** The whole reason to gray-code a pointer is that a single-bit
> change is safe to sample across a clock domain. This assertion verifies the
> property the synchronizer depends on; a multi-bit jump means the encoder is
> broken and the CDC is unsafe.

## Mutual exclusion and one-grant arbitration

An arbiter must grant at most one requester at a time. That is one-hot-zero on the
grant vector, restated as mutual exclusion:

```systemverilog
// At most one grant asserted
assert property ($onehot0(gnt));

// A grant implies a matching request (no spurious grant)
assert property ((gnt != '0) |-> (gnt & req) == gnt);
```

The first line forbids two simultaneous grants; the second forbids granting a port
that did not ask. Together they pin down the arbiter's core contract.

## Pulse versus level

Some control signals must be a single-cycle pulse, not a held level. Assert that the
signal returns low the next cycle:

```systemverilog
// 'start' is a one-cycle strobe, never held high two cycles
assert property (start |=> !start);
```

The inverse intent — a level that must persist — uses `throughout` or a hold check
instead. State which one the protocol requires; treating a pulse as a level (or the
reverse) is a frequent integration bug.

## Signal never X when valid

When a beat is valid, its payload must carry real data, not `X` or `Z`. The
`$isunknown` function flags any unknown bit:

```systemverilog
// While valid, data must be fully known (no X/Z)
assert property (valid |-> !$isunknown(data));
```

> **Design intent.** An `X` on a valid payload usually means an uninitialized
> register or an unconnected path leaked into the data — a real bug that RTL `X`
> values can otherwise mask through optimistic or pessimistic propagation. This
> check turns a silent `X` into an explicit failure.

## CDC intent: a note, not a single assertion

Clock-domain-crossing correctness is mostly *not* a one-clock SVA property. The data
on a crossing is, by definition, unstable relative to the receiving clock, so a
naive same-clock assertion on it is meaningless or false. What SVA *can* state is the
intent the CDC structure relies on:

```systemverilog
// Gray pointer changes one bit at a time (sampled in the source domain)
assert property (@(posedge wr_clk) $countones(wptr_gray ^ $past(wptr_gray)) <= 1);
```

For the crossing itself — synchronizer depth, settling time, no combinational logic
on a metastable net — use a dedicated CDC tool or a multiclock assertion that flows
at the `##` boundary (Chapter 8). Treat structural CDC sign-off as a separate
discipline; use SVA to pin the *encoding* invariants the structure assumes.

## Common pitfalls

- **Unbounded handshake checks in simulation.** `req |-> s_eventually ack` cannot
  fail in finite time. Use a bounded window `##[1:N]`.
- **Forgetting payload stability.** Checking `valid` holds but not that `data`
  holds lets the producer mutate an offered beat. Add `$stable(data)`.
- **Using `$onehot` where idle is legal.** A grant bus that is all-zero when idle
  needs `$onehot0`, not `$onehot`.
- **Same-clock assertions on a CDC net.** They are meaningless on an unstable
  signal. Check the source-domain encoding invariant, and leave settling to a CDC
  flow.
- **Confusing pulse and level intent.** Decide whether the protocol wants a one-cycle
  strobe or a held level, and assert exactly that.

## Summary

- Handshakes: bound the acknowledge window and require the request (and payload) to
  hold until accepted.
- Stream channels: once offered, `valid` and `data` are stable until `ready` takes
  the beat.
- One-hot and gray-code invariants map directly to `$onehot`, `$onehot0`, and a
  single-bit-change check.
- FIFO safety is three "never" properties: no overflow, no underflow, count in
  range.
- Guard valid payloads against `X` with `$isunknown`; treat CDC settling as a
  separate flow and use SVA only for the encoding invariants it assumes.

---

[← Binding and Placement](09-binding-and-placement.md) · [Table of contents](../README.md) · [Next: Local Variables →](11-local-variables.md)
