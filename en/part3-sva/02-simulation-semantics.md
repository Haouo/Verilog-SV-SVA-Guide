# Part III · 2. Simulation Semantics

[← Why Assertions](01-why-assertions.md) · [Table of contents](../README.md) · [Next: Assertion Kinds →](03-assertion-kinds.md)

## Learning objectives

- Name the SystemVerilog event regions that matter for assertions.
- Define a sampled value and explain when it is taken.
- Explain why concurrent assertions sample in the Preponed region.
- Use the clock as the single reference for assertion timing.
- Predict what a concurrent assertion sees versus what procedural code sees.

## Designer's mental model

Concurrent assertions observe a sampled version of the design. They do not simply
read whatever a procedural block most recently assigned in the same time slot.
Sampling in the Preponed region makes the assertion see the value that existed at
the clock edge, which matches how flip-flops reason about synchronous logic.

This timing model is the foundation for almost every SVA surprise. If an
assertion seems one cycle off, or `$past` seems to disagree with a waveform, ask
which event region each value came from. Once sampling is clear, implication,
reset disabling, and local variables become much less mysterious.

## The problem sampling solves

Within a single simulation time step, many things happen: clock edges fire,
flip-flops update, combinational logic settles, and assignments race to complete.
If an assertion read signals at an arbitrary moment inside that turmoil, it might
see a value mid-update — sometimes the old value, sometimes the new one,
depending on scheduling order. The result would be non-deterministic.

SystemVerilog removes this ambiguity by defining an *ordering of regions* inside
each time step and by giving concurrent assertions a fixed, well-defined value to
read: the **sampled value** (取樣值). You do not need the full scheduling model to
write good assertions, but you do need the few regions below.

## The event regions that matter

A simulation time step is divided into ordered regions. For assertions, four
matter:

- **Preponed.** The very first region of the time step, before any design code
  runs. Values here are stable — nothing has updated yet this step. Concurrent
  assertions take their **sampled values** here.
- **Active.** Where normal design code executes: `always` blocks run, blocking
  assignments take effect, and combinational logic settles.
- **Observed.** After the Active region settles, concurrent assertion *properties*
  are evaluated using the values sampled back in Preponed.
- **Reactive.** Where testbench-side code and assertion **action blocks** (the
  pass/fail code attached to an assertion) execute.

The order is fixed: Preponed → Active → ... → Observed → Reactive. The key
takeaway is that sampling happens *first* (Preponed) and evaluation happens
*after* the design has settled (Observed).

## Sampled values

The **sampled value** of a signal is its value in the Preponed region of the
current time step — that is, its value just *before* the clock edge that is
driving the assertion. Concurrent assertions never read the live, mid-step value
of a signal; they read its sampled value.

This has a precise and important consequence. At a clock edge, a flip-flop's
output and the assertion both refer to the *same* sampled value: the value the
signal held going into the edge, before this edge's update takes effect.

```systemverilog
logic clk, a, b;

// On the posedge, this assertion sees the values a and b held
// *before* this edge, not the new values being computed now.
assert property (@(posedge clk) a |-> b);
```

So a concurrent assertion observes the design as a synchronous element does: it
sees the steady-state values that were valid at the edge, not the transient
values being assigned during the edge.

## Why concurrent assertions sample in Preponed

Sampling in Preponed makes assertion results independent of scheduling order. Two
signals that update in the same time step might race in the Active region — which
`always` block runs first is not guaranteed. If an assertion read them after they
updated, its result could depend on that race.

By reading the Preponed values instead — the values from *before* this step's
updates — the assertion sees a clean, settled snapshot. It cannot be fooled by a
half-finished non-blocking update or by the order of two `always` blocks. This is
exactly the behavior a designer wants: the assertion reasons about the same
stable values the flip-flops sampled.

```systemverilog
// Both blocks update q and r in the same step. The assertion is not
// affected by which block the simulator runs first, because it samples
// q and r in Preponed, before either update.
always_ff @(posedge clk) q <= d;
always_ff @(posedge clk) r <= q;

assert property (@(posedge clk) r == $past(q));
```

`$past(q)` here returns the value `q` had one clock earlier — itself a sampled
value — which is exactly what the second flip-flop captured.

## The clock is the reference

A concurrent assertion is meaningless without a clock. The clock defines two
things at once:

1. **When sampling happens** — values are sampled in Preponed, relative to the
   specified clock edge.
2. **What "one cycle later" means** — every temporal step in a sequence or
   property (`##1`, `|=>`, and so on) advances by one tick of that clock.

```systemverilog
// @(posedge clk) is the sampling and stepping reference for the whole property
assert property (@(posedge clk) start |=> ##2 done);
```

Here `start`, `done`, and the `##2` delay are all measured against `posedge clk`.
The assertion does not care about wall-clock time or delta cycles; it counts
edges of its clock. Chapter 8 covers how to set this clock once with a default
clocking block and how `disable iff` handles reset.

## Sampled value versus procedural value

Because procedural code (in an `always` block) runs in the Active region and
concurrent assertions sample in Preponed, the two can see different values in the
same time step. This is intended, and worth internalizing:

- An immediate assertion inside an `always` block sees the **current**,
  mid-execution values, like any procedural statement.
- A concurrent assertion sees the **sampled** (Preponed) values.

```systemverilog
always_comb begin
    x = a + b;            // x updates here, in the Active region
    assert (x < LIMIT);   // immediate: sees the new x right now
end

// concurrent: would sample x in Preponed — its value before this step
assert property (@(posedge clk) x < LIMIT);
```

If you mix the two, keep the distinction clear: immediate sees *now*, concurrent
sees *the value at the edge*.

> **Design intent.** Sampled values let an assertion reason about the design the
> way the flip-flops do — about the stable values present at the clock edge, not
> the transient churn of a single time step. That stability is what makes a
> concurrent assertion a reliable statement of intent rather than a hostage to
> scheduling order.

## Common pitfalls

- **Expecting a concurrent assertion to see a just-assigned value.** It samples in
  Preponed, so it sees the pre-edge value, not the value an `always` block is
  writing this step.
- **Confusing immediate and concurrent timing.** An immediate `assert` in
  procedural code sees current values; a concurrent `assert property` sees sampled
  values. They can differ within one step.
- **Writing a concurrent assertion with no clock and expecting it to "just work."**
  Without a clock (explicit or default), there is no sampling reference. Chapter 8
  covers default clocking.
- **Reasoning about delta cycles.** Assertions count clock edges, not deltas.
  Think in cycles of the assertion clock, not in simulator scheduling steps.

## Summary

- A time step is divided into ordered regions; Preponed, Active, Observed, and
  Reactive are the ones that matter for assertions.
- Concurrent assertions take **sampled values** in the Preponed region — the
  values just before the clock edge.
- Sampling in Preponed makes results independent of scheduling races.
- The clock is the single reference for both sampling and temporal stepping.
- Immediate assertions see current procedural values; concurrent assertions see
  sampled values, and the two can differ in the same step.

---

[← Why Assertions](01-why-assertions.md) · [Table of contents](../README.md) · [Next: Assertion Kinds →](03-assertion-kinds.md)
