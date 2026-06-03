# Part III · 4. The Boolean Layer

[← Assertion Kinds](03-assertion-kinds.md) · [Table of contents](../README.md) · [Next: Sequences: Basics →](05-sequences-basics.md)

## Learning objectives

- Write boolean expressions that operate on sampled values.
- Detect edges and changes with `$rose`, `$fell`, `$stable`, `$changed`.
- Reach back in time with `$past`.
- Check one-hot, count, and unknown conditions with `$onehot`, `$onehot0`,
  `$countones`, `$isunknown`.

## The boolean layer

SVA is built in layers. At the bottom is the **boolean layer**: ordinary
expressions that evaluate to true or false on a single sampling point. Sequences
(Chapter 5) and properties (Chapter 7) are built on top of these booleans. Getting
the boolean layer right is the foundation for everything above it.

A boolean expression in a concurrent assertion uses the same operators as RTL —
`&`, `|`, `==`, `<`, `&&`, and so on — but it operates on **sampled values**
(Chapter 2), not live values. So `a && b` in an assertion means "the sampled `a`
and the sampled `b`, taken in Preponed before this clock edge."

```systemverilog
// Sampled values: a, b, and c as of this clock edge
assert property (@(posedge clk) (a && b) |-> c);
```

## Sampled-value functions

A boolean often needs to compare this cycle's value with the previous cycle's. The
sampled-value functions do exactly that, all relative to the assertion clock.

### $rose, $fell, $stable, $changed

These compare the sampled value now against the sampled value one clock earlier:

- **`$rose(e)`** — true when `e` changed from 0 to 1 since the previous cycle (a
  rising edge of the sampled value).
- **`$fell(e)`** — true when `e` changed from 1 to 0.
- **`$stable(e)`** — true when `e` is unchanged from the previous cycle.
- **`$changed(e)`** — true when `e` differs from the previous cycle (the negation
  of `$stable`).

```systemverilog
// A handshake: when req rises, gnt must follow on the next cycle
assert property (@(posedge clk) $rose(req) |=> gnt);

// Configuration must not change while the core is busy
assert property (@(posedge clk) busy |-> $stable(cfg));
```

`$rose` and `$fell` test a single bit (the least significant bit for a vector).
`$stable` and `$changed` work on the whole expression, including vectors. Because
they compare against the previous *sampled* value, they are the assertion-layer
way to talk about edges — do not try to reconstruct an edge with raw `==` against a
manually delayed copy.

### $past

`$past(e)` returns the sampled value `e` had a number of cycles ago:

```systemverilog
// $past(e) — e one cycle earlier
// $past(e, n) — e n cycles earlier
assert property (@(posedge clk) load |=> (q == $past(d)));
```

This says: one cycle after `load`, `q` equals the value `d` held *at* the load —
the classic register-capture check. The optional second argument reaches further
back:

```systemverilog
// data_out is the input delayed by exactly 3 cycles
assert property (@(posedge clk) data_out == $past(data_in, 3));
```

`$past` also accepts an optional gating expression and clock; in everyday use the
one- and two-argument forms cover most needs. Note that early in simulation, before
`n` cycles have elapsed, `$past` returns the reset/initial value — design
assertions so this start-up region does not produce false failures (Chapter 8's
`disable iff` and the implication's vacuity both help here).

## Bit-pattern functions

Several functions express invariants about the bits of a vector — exactly the kind
of fact a designer knows about a state register or a select line.

### $onehot and $onehot0

- **`$onehot(e)`** — true when exactly one bit of `e` is 1.
- **`$onehot0(e)`** — true when at most one bit of `e` is 1 (zero or one).

```systemverilog
// A one-hot state register: exactly one bit set, every cycle
assert property (@(posedge clk) disable iff (!rst_n) $onehot(state));

// At most one master may be granted at a time
assert property (@(posedge clk) $onehot0(grant));
```

`$onehot` is the natural way to state the invariant of a one-hot FSM or a mutually
exclusive grant vector. Use `$onehot0` when "all zero" is also a legal state (for
example, an idle bus with no grant).

### $countones

`$countones(e)` returns the number of bits set to 1 in `e`. It generalizes the
one-hot checks to any exact count:

```systemverilog
// Exactly two ports may be active in this mode
assert property (@(posedge clk) (mode == DUAL) |-> $countones(active) == 2);
```

### $isunknown

`$isunknown(e)` is true when any bit of `e` is `x` or `z`. It is the assertion-layer
guard against unknown values reaching a place they must not:

```systemverilog
// Control bus must never carry x or z once out of reset
assert property (@(posedge clk) disable iff (!rst_n) !$isunknown(ctrl));
```

This is a cheap, high-value check. Unknowns that slip through in simulation often
become real bugs in silicon; asserting `!$isunknown` on critical signals catches
them at the source.

> **Design intent.** The boolean layer is where a designer states the facts that
> must hold at a single edge: this vector is one-hot, this control word is never
> unknown, this register captured the right value. These are the invariants you
> carry in your head about each signal — the sampled-value functions let you write
> them down in the assertion clock's terms.

## Common pitfalls

- **Forgetting that booleans use sampled values.** `a && b` in an assertion is the
  sampled `a` and `b`, not their live values. This matters when an `always` block
  is updating them this step.
- **Hand-rolling edge detection.** Use `$rose`/`$fell` instead of comparing against
  a manually delayed copy; the sampled-value version is correct by construction.
- **Ignoring `$past` at start-up.** Before enough cycles have elapsed, `$past`
  returns the initial value. Gate such assertions with `disable iff (reset)` or
  rely on implication vacuity so the start-up region does not fire.
- **Using `$onehot` where `$onehot0` is meant.** If "no bit set" is a legal idle
  state, `$onehot` will wrongly fail on it. Pick `$onehot0` when zero is allowed.
- **Comparing a vector with `$rose`/`$fell`.** Those test a single bit. Use
  `$changed` or `$stable` for whole-vector change detection.

## Summary

- The boolean layer is ordinary expressions over **sampled values**, the
  foundation for sequences and properties.
- `$rose`, `$fell`, `$stable`, `$changed` compare this cycle to the previous one;
  `$past` reaches back a chosen number of cycles.
- `$onehot`, `$onehot0`, and `$countones` state bit-count invariants;
  `$isunknown` guards against `x`/`z`.
- Prefer these functions over hand-built equivalents; they are correct against the
  sampled-value model by construction.

---

[← Assertion Kinds](03-assertion-kinds.md) · [Table of contents](../README.md) · [Next: Sequences: Basics →](05-sequences-basics.md)
