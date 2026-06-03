# Part I · 7. Synthesis-Aware Coding

[← Finite State Machines](06-finite-state-machines.md) · [Table of contents](../README.md) · [Next: Testbench Essentials →](08-testbench-essentials.md)

## Learning objectives

- Write RTL that simulates and synthesizes to the same hardware.
- Recognize and avoid the constructs that cause mismatch.
- Apply a short checklist of synthesis-safe habits.

## The golden rule: simulation must match synthesis

A synthesis tool builds gates from your RTL. A simulator runs your RTL as a
program. They should agree, but several Verilog features let them diverge. Most
RTL bugs that survive to silicon come from such mismatches. This chapter collects
the habits that keep the two in step. Several were introduced earlier; here they
form one checklist.

## Latch avoidance

Covered in Chapter 4, and worth repeating because it is the most common
synthesis surprise. A combinational `always` block that does not assign every
output on every path infers a latch. Defaults at the top of the block, or a
complete `if`/`else` and `case`/`default`, prevent it.

```verilog
always @* begin
    y = 1'b0;          // default assignment
    if (sel) y = a;    // override; no latch
end
```

## Complete and correct sensitivity

Use `always @*` for combinational logic so the sensitivity list is complete by
construction (Chapter 4). A hand-written list that omits a signal makes the
simulator miss an update that the synthesized hardware performs anyway.

## Blocking versus non-blocking

Use `<=` in clocked blocks and `=` in combinational blocks (Chapter 5). This
single rule prevents the most common class of simulation/synthesis races. Never
mix the two for the same signal, and give each register exactly one driver.

## Reset every state element that needs it

An unreset flip-flop powers up as `x` in simulation and as an undefined value in
hardware. Decide which state needs a defined reset value and reset it. Keep one
reset style per clock domain (Chapter 5).

## Avoid non-synthesizable constructs in RTL

Some constructs belong only in testbenches. Keep them out of synthesizable
modules:

- `initial` blocks (except for FPGA RAM/ROM initialization that your tool
  supports).
- Delays such as `#10`.
- `$display`, `$finish`, and other system tasks.
- `===` and `!==` (they reference `x`/`z`, which hardware lacks).
- `real` and `time` types.
- Unbounded `while`/`forever` loops. Use `for` loops with constant bounds, which
  the tool unrolls.

## Don't depend on `x`-optimism or pragmas

Two specific traps:

- **`full_case` / `parallel_case`** (Chapter 4) tell the synthesis tool to assume
  things the simulator does not. Avoid them; write complete `case` statements.
- **`casex`** treats `x` as a don't-care during matching, which can hide a real
  `x` in simulation while synthesis builds different logic. Prefer `casez`, or a
  plain `case` with `default`.

## Keep arithmetic widths explicit

Width inference (Chapter 3) is silent. An intermediate that overflows because the
expression width came from a narrow operand will simulate and synthesize the same
*wrong* way — a logic bug, not a mismatch, but just as damaging. Size
intermediate signals so the intended range is explicit.

## A synthesis-safe checklist

Before you consider an RTL block done:

- [ ] Combinational blocks use `always @*` and assign every output on every path.
- [ ] Clocked blocks use `<=`; combinational blocks use `=`.
- [ ] Each register has exactly one driver and a defined reset where needed.
- [ ] One reset style per clock domain.
- [ ] Every `case` has a `default`; no `full_case`/`parallel_case`; no `casex`.
- [ ] No `initial`, delays, or system tasks in synthesizable code.
- [ ] Arithmetic widths are explicit where overflow is possible.

> **Design intent.** Synthesis-aware coding is the intent that "what I simulate is
> what I build." Each habit on the checklist removes one way for the two views to
> disagree. Assertions (Part III) are the complementary tool: they state intent
> the structure alone cannot, and they fire the instant simulation departs from
> it — including the mismatches this chapter works to prevent.

## Common pitfalls

- Relying on a simulator's handling of `x` to mean the design is correct.
- Leaving a stray `initial` or delay in a module meant for synthesis.
- Assuming the tool will "do what I meant" with an incomplete `case` — it follows
  the language, not your intent.

## Summary

- The goal is a single behavior shared by simulation and synthesis.
- Avoid latches, use complete sensitivity, follow the `<=`/`=` rule, and reset
  state that needs it.
- Keep testbench-only constructs out of RTL.
- Avoid `case` pragmas and `casex`; keep widths explicit.

---

[← Finite State Machines](06-finite-state-machines.md) · [Table of contents](../README.md) · [Next: Testbench Essentials →](08-testbench-essentials.md)
