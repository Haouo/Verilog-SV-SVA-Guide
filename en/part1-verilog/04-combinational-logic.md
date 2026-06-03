# Part I · 4. Combinational Logic

[← Operators and Expressions](03-operators-and-expressions.md) · [Table of contents](../README.md) · [Next: Sequential Logic →](05-sequential-logic.md)

## Learning objectives

- Describe combinational logic with `assign` and with `always`.
- Write a correct sensitivity list with `always @*`.
- Use `if` and `case` without inferring latches.
- Understand `full_case` / `parallel_case` and why to avoid them.

## Two ways to write combinational logic

Combinational logic has outputs that depend only on present inputs, with no
state. Verilog offers two styles.

### Continuous assignment

`assign` drives a net continuously from an expression. It is the natural choice
for simple logic.

```verilog
assign y     = a & b;
assign sum   = a + b;
assign mux_o = sel ? in1 : in0;
```

### Procedural combinational logic

For anything with `if`/`case` structure, use an `always` block. In plain Verilog
this is `always @*` driving `reg` variables.

```verilog
reg [3:0] result;
always @* begin
    if (op == 2'b00)      result = a + b;
    else if (op == 2'b01) result = a - b;
    else                  result = a & b;
end
```

The target is a `reg` (see Chapter 2), but this is still combinational logic, not
a register — there is no clock.

## The sensitivity list

`always @*` (equivalently `always @(*)`) tells the tool to trigger the block when
*any* signal it reads changes. Always use it for combinational logic. The old
style of listing signals by hand, `always @(a or b or sel)`, is error-prone: omit
one signal and simulation no longer matches synthesis, because synthesis builds
combinational logic regardless of your list.

```verilog
// Good: complete sensitivity, by construction
always @* begin ... end

// Bad: hand-listed, easy to get wrong
always @(a or b) begin
    result = a + b + c;   // c is missing -> simulation mismatch
end
```

## Avoiding latches

This is the central hazard of combinational `always` blocks. If a variable is
*not assigned on every path* through the block, the tool must hold its previous
value — which means it infers a latch. Latches in RTL are almost always a
mistake: they create timing problems and usually signal an incomplete
description.

```verilog
// Latch inferred: result is not assigned when en is 0
always @* begin
    if (en) result = a + b;
end
```

Two reliable fixes:

1. **Assign a default first**, then override:

   ```verilog
   always @* begin
       result = 4'b0000;        // default covers every path
       if (en) result = a + b;
   end
   ```

2. **Make every branch assign every output**, including a final `else` and a
   `default` in `case`.

Either way, the rule is simple: every output of a combinational block must get a
value on every path.

## `case` statements

`case` is the clear way to express multi-way selection, such as a multiplexer or
a decoder. Always include a `default`.

```verilog
always @* begin
    case (sel)
        2'b00: y = in0;
        2'b01: y = in1;
        2'b10: y = in2;
        2'b11: y = in3;
        default: y = 1'bx;   // unreachable here, but defends against x on sel
    endcase
end
```

When `sel` could be `x` (for example during reset propagation), a `default`
sending `y` to a known value — or to `x` to expose the problem — prevents a latch
and makes intent explicit.

`casez` treats `z`/`?` bits as don't-cares and is useful for priority decoders.
`casex` treats `x` as don't-care too, which can mask bugs — prefer `casez`.

## `full_case` and `parallel_case`

These are synthesis pragmas you will see in older code:

- `full_case` claims every possible `case` value is covered.
- `parallel_case` claims the items are mutually exclusive.

Avoid both. They tell the synthesis tool to assume something the simulator does
not, so simulation and synthesis can diverge — exactly the mismatch assertions
exist to catch. Write a complete `case` with an explicit `default` instead, and
let the tool see the truth.

> **Design intent.** A combinational block is meant to be a pure function of its
> inputs. A latch breaks that intent by introducing hidden state. The discipline
> — `always @*`, a default assignment, a `default` in every `case` — is how you
> state "this is pure combinational logic" so the tool builds exactly that.

## Common pitfalls

- **Incomplete assignment → latch.** Assign every output on every path.
- **Hand-written sensitivity lists.** Use `always @*`.
- **Missing `case default`.** It can infer a latch and hides `x` on the selector.
- **`full_case`/`parallel_case` pragmas.** They invite simulation/synthesis
  mismatch. Write complete `case` statements instead.
- **`casex`.** It treats `x` as don't-care and can hide real bugs; use `casez`.

## Summary

- Use `assign` for simple logic and `always @*` for `if`/`case` logic.
- `always @*` gives a complete sensitivity list automatically.
- Assign every output on every path to avoid inferred latches.
- Write complete `case` statements with `default`; avoid the case pragmas.

---

[← Operators and Expressions](03-operators-and-expressions.md) · [Table of contents](../README.md) · [Next: Sequential Logic →](05-sequential-logic.md)
