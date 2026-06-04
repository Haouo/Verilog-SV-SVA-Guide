# Part III · 8. Clocking and Reset

[← Properties](07-properties.md) · [Table of contents](../README.md) · [Next: Binding and Placement →](09-binding-and-placement.md)

## Learning objectives

- Attach a clock to a concurrent assertion explicitly and by default.
- Use `default clocking` to set the assertion clock once.
- Disable an assertion during reset with `disable iff`.
- Reason about multiclock assertions and clock flow across `##` boundaries.
- Sample on the correct edge for the design's convention.

## Designer's mental model

Clocking tells an assertion which timeline to use. Reset tells it when the rule
is not supposed to apply. Without those two pieces, even a correct temporal
property can fail during initialization or sample the wrong edge of a protocol.

Treat `disable iff` as part of the contract, not as an afterthought. During reset,
some signals are intentionally unstable or being forced into known values. After
reset releases, the assertion resumes and the design's normal promises matter
again. The reset expression should match that design story.

## The assertion clock

Every concurrent assertion needs a clock. The clock fixes when sampling happens
(Chapter 2) and what "one cycle" means for every `##` and implication. The explicit
form names it inline:

```systemverilog
// Sampling and stepping reference: posedge clk
assert property (@(posedge clk) req |=> gnt);
```

Writing `@(posedge clk)` on every assertion is repetitive and error-prone — a
single mistyped edge changes the meaning silently. For a block with one clock,
declare it once.

## default clocking

A `default clocking` block sets the clock for every concurrent assertion in its
scope that does not name its own. Inside the block, assertions read cleanly with no
per-line clock:

```systemverilog
module fifo_ctrl (input logic clk, rst_n, /* ... */);

    default clocking cb @(posedge clk);
    endclocking

    // No @(posedge clk) needed — the default supplies it
    assert property (wr_en |-> !full);
    assert property (rd_en |-> !empty);

endmodule
```

The default clocking is the recommended style: it states the clock once, keeps the
assertions readable, and removes the chance of an inconsistent edge. An assertion
may still override it by naming its own clock when it genuinely runs on a different
one.

## disable iff: handling reset

During reset, the design is not yet obeying its protocol, so its assertions should
not fire. `disable iff (cond)` turns an assertion off whenever `cond` is true — the
standard use is an asynchronous reset:

```systemverilog
// While rst_n is low, this assertion is disabled
assert property (@(posedge clk) disable iff (!rst_n)
    req |=> gnt);
```

`disable iff` is **asynchronous**: the moment its condition becomes true, any
in-flight evaluation of the property is aborted and reported as neither pass nor
fail. This matches an asynchronous reset, which can assert between clock edges and
must immediately void any pending check. It differs from a boolean guard in the
antecedent, which is only sampled at the clock edge.

```systemverilog
// Guarding in the antecedent (sampled at the edge) — NOT the same as disable iff
assert property (@(posedge clk) (rst_n && req) |=> gnt);
```

Use `disable iff` for reset and other asynchronous "abandon the check" conditions;
use an antecedent guard for synchronous conditions that should be sampled on the
edge. Mixing them up is a common source of confusing reset-time failures.

A common pattern is one reset condition for the whole block, factored into the
default clocking style with a `default disable iff`:

```systemverilog
module core (input logic clk, rst_n, /* ... */);

    default clocking cb @(posedge clk);
    endclocking
    default disable iff (!rst_n);   // applies to every assertion below

    assert property (req   |=> gnt);
    assert property (start |-> ##[1:8] done);

endmodule
```

`default disable iff` states the reset convention once, just as `default clocking`
states the clock once. Both keep the per-assertion text focused on intent.

## Multiclock assertions

A single assertion can span more than one clock. When a sequence crosses a `##`
delay into a differently clocked region, the assertion *flows* from one clock to
the next at that boundary:

```systemverilog
// Antecedent sampled on clk_a; consequent sampled on clk_b
assert property (@(posedge clk_a) req ##1 @(posedge clk_b) ack);
```

The rules for multiclock assertions are deliberately strict:

- A clock change can only occur at a `##` cycle-delay boundary, where the design
  hands off from one clock domain to another.
- Across the boundary, `##1` means "the first `clk_b` edge after the `clk_a`
  match," not a fixed time. The assertion counts edges of whichever clock is
  currently in effect.
- Operators that require a single common clock — such as `intersect`, `and` over
  overlapping spans, or `throughout` — cannot straddle a clock change.

Multiclock assertions are the right tool for checking a clock-domain crossing
handshake, where a request is launched in one domain and acknowledged in another.
Keep each side on its own clock and let the `##` boundary carry the handoff.

## Sampling on the correct edge

The edge in `@(posedge clk)` must match the design's sampling convention. If the
RTL captures data on the rising edge, assertions should sample on `posedge` too, so
the assertion sees the same values the flip-flops do. Asserting on the wrong edge
samples half a cycle off and produces results that look mysteriously inconsistent.

```systemverilog
// RTL captures on posedge; the assertion must too
always_ff @(posedge clk) q <= d;
assert property (@(posedge clk) load |=> (q == $past(d)));
```

For a design that uses both edges (dual-edge logic), clock each assertion on the
edge that captures the signal it checks. When in doubt, match the assertion clock
to the clock and edge of the logic that produces the asserted signal.

> **Design intent.** The clock and reset settings tell the tool *when* an
> assertion's promise applies: which edge defines its cycles, and during which
> windows (reset) the promise is suspended. `default clocking` and `default
> disable iff` state these once for a block, so each assertion can express pure
> intent — what must be true — while the surrounding declarations say when to
> check it.

## Common pitfalls

- **Repeating `@(posedge clk)` on every assertion.** Use `default clocking` to set
  it once and avoid an inconsistent edge slipping in.
- **Putting reset in the antecedent instead of `disable iff`.** An antecedent guard
  is sampled at the edge; `disable iff` is asynchronous and aborts in-flight
  checks. For asynchronous reset, use `disable iff`.
- **Forgetting reset entirely.** Without a reset guard, assertions fire during the
  unknown start-up window. Add `disable iff (!rst_n)` or a `default disable iff`.
- **Crossing clocks outside a `##` boundary.** A clock change is only legal at a
  cycle-delay boundary; single-clock operators cannot straddle it.
- **Sampling on the wrong edge.** Match the assertion clock and edge to the logic
  that produces the signal, or the assertion samples off by half a cycle.

## Summary

- Every concurrent assertion needs a clock; `default clocking` sets it once per
  scope.
- `disable iff` turns an assertion off asynchronously — the standard handling for
  asynchronous reset — and `default disable iff` states the reset convention once.
- A boolean guard in the antecedent is synchronous (sampled at the edge), unlike
  the asynchronous `disable iff`.
- Multiclock assertions flow between clocks only at `##` boundaries; single-clock
  operators cannot straddle the change.
- Sample on the edge that matches the design's capture convention.

---

[← Properties](07-properties.md) · [Table of contents](../README.md) · [Next: Binding and Placement →](09-binding-and-placement.md)
