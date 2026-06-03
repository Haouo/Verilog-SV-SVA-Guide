# Part II · 1. Why SystemVerilog for Design

[← Testbench Essentials](../part1-verilog/08-testbench-essentials.md) · [Table of contents](../README.md) · [Next: Enhanced Data Types →](02-enhanced-data-types.md)

## Learning objectives

- Understand why `logic` replaces both `wire` and `reg` in synthesizable RTL.
- Use `always_comb`, `always_ff`, and `always_latch` to make procedural intent
  explicit.
- Know how the specialized `always` blocks enable tool-checked design rules.
- Apply `unique` and `priority` to case statements to document decision intent.

## The problem with Verilog's types

Verilog requires you to declare a signal as either `wire` or `reg`. The
distinction is historical, not logical: `wire` is a net driven by a continuous
`assign` or a module port; `reg` is a variable that holds its value between
procedural assignments. Neither name tells you whether the hardware is
combinational or sequential.

The confusion runs deep. A `reg` does not mean a register. You can and should
use `reg` inside an `always @(*)` combinational block. The tool infers a latch or
combinational gate from the block's structure, not from the signal's declared
type. A designer reading code cannot tell from `reg` alone whether a flip-flop
was intended.

SystemVerilog introduces `logic`, a single 4-state type that can be used
everywhere `wire` or `reg` was used. It simplifies declaration, removes
confusion, and is the correct default type for RTL signals.

```systemverilog
// Verilog — two types, one concept
wire [7:0] bus;
reg  [7:0] count;

// SystemVerilog — one type for both
logic [7:0] bus;
logic [7:0] count;
```

The 4-state values (0, 1, X, Z) are preserved. Synthesis ignores X and Z
values; they exist for simulation modeling of uninitialized state and
high-impedance.

### When to keep `wire`

`logic` cannot be driven by multiple continuous sources (multiple `assign`
statements or multiple module outputs onto the same net). That case still
requires `wire` for tri-state buses. In practice, synthesizable RTL almost never
uses tri-state internally; use `wire` only where true multi-driver connectivity
is intended.

## Specialized always blocks

Verilog's `always @(*)` works, but it is generic: it does not document whether
you intend a flip-flop, a latch, or combinational logic, and neither the compiler
nor the simulator checks that the code matches your intent. SystemVerilog provides
three purpose-specific forms.

### `always_comb`

Use `always_comb` for combinational logic. The simulator automatically derives
the sensitivity list from all variables read in the block — you do not write
`@(*)` at all. More importantly, the tool checks that the block is truly
combinational: every output must be assigned on every path through the block, and
no feedback is allowed.

```systemverilog
always_comb begin
    // Combinational mux: no inferred latch
    if (sel)
        y = a;
    else
        y = b;
end
```

If you accidentally leave a variable unassigned on some path, a lint tool or
simulator reports a violation. With plain `always @(*)`, you would silently infer
a latch.

`always_comb` also starts one scheduler delta after time zero, which ensures the
block evaluates before any edge-triggered block reads its outputs. That matches
how combinational logic settles before a clock edge.

### `always_ff`

Use `always_ff` for clocked sequential logic. You must still write the
sensitivity list (the clock and any asynchronous reset). The tool checks that
only edge-sensitive signals appear in the list and that the block assigns using
non-blocking `<=`.

```systemverilog
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        count <= '0;
    else if (en)
        count <= count + 1;
end
```

A violation — such as using `=` instead of `<=` — is flagged as a lint error
rather than silently producing wrong behavior. The keyword documents intent to
every reader and every tool.

### `always_latch`

Use `always_latch` when a level-sensitive latch is genuinely required (rare in
RTL). The tool checks that the block is latch-like: incomplete assignments are
the mechanism, not a mistake.

```systemverilog
always_latch begin
    // Intentional latch: hold q when en is low
    if (en)
        q <= d;
end
```

In most designs, an `always_latch` block is a warning that design intent should
be reconsidered. Prefer registered logic. But when a latch is intentional —
for example, in a clock-gate enable path — using `always_latch` makes that
explicit and suppresses false lint warnings.

> **Design intent.** `always_comb`, `always_ff`, and `always_latch` map each
> procedural block to one hardware category. A reader sees the intent in the
> keyword, not by decoding the sensitivity list and assignment style. Tools
> can then check that the code matches the keyword — turning a coding convention
> into an enforceable rule.

## `unique` and `priority` case modifiers

A plain `case` statement in Verilog implies no coverage guarantee. If no branch
matches, the outputs retain their current value (implying a latch in a
combinational block) or are simply not updated. SystemVerilog adds two modifiers
that document and check the decision structure.

### `unique case`

`unique case` declares two things:

1. The cases are mutually exclusive (no two branches can match at once).
2. The case is complete (at least one branch matches for any legal input).

```systemverilog
always_comb begin
    unique case (op)
        2'b00: result = a + b;
        2'b01: result = a - b;
        2'b10: result = a & b;
        2'b11: result = a | b;
    endcase
end
```

With `unique`, a synthesis tool may optimize assuming the cases are exclusive.
A simulator issues a run-time warning if the case expression matches more than
one branch or matches none. This eliminates priority encoding and inferred latches
from a case that is supposed to be fully decoded.

### `priority case`

`priority case` declares that the branches are evaluated in order and the first
match wins — like a chain of `if / else if`. It also declares that the case is
complete: at least one branch will always match.

```systemverilog
always_comb begin
    priority case (1'b1)          // one-hot check
        req[0]: grant = 4'b0001;
        req[1]: grant = 4'b0010;
        req[2]: grant = 4'b0100;
        req[3]: grant = 4'b1000;
    endcase
end
```

`priority case` is appropriate when a priority encoder or a first-match arbitration
is exactly what is intended. It is not for cases that are genuinely exclusive —
use `unique` there.

### `unique if` and `priority if`

The same modifiers apply to `if / else if` chains:

```systemverilog
// All conditions mutually exclusive and complete
unique if (state == IDLE)   next = FETCH;
else if (state == FETCH)    next = DECODE;
else if (state == DECODE)   next = EXECUTE;
else if (state == EXECUTE)  next = IDLE;
```

Using `unique if` on a fully decoded FSM state transition tells the tool that
every legal state is covered and no two conditions overlap. The tool checks both
at simulation and can optimize at synthesis.

## Common pitfalls

- **Using `reg` when you mean `logic`.** The name misleads; switch to `logic` for
  all RTL signals that are not true multi-driver nets.
- **Writing `always @(*)` for sequential logic.** An `always @(*)` block that
  reads a clock edge has a non-obvious sensitivity list. Use `always_ff` and put
  the clock in the list explicitly.
- **Forgetting `always_comb` checks completeness.** It does not silently allow
  incomplete branches — that is the point. Add a `default` or cover all cases.
- **Using `unique` on an incomplete set.** If the input can legally fall outside
  the listed cases, do not use `unique`; you will get spurious simulation warnings.
- **Mixing `always_ff` with blocking assignment `=`.** Lint tools flag this as a
  violation of the `always_ff` contract. Use `<=`.

## Summary

- `logic` unifies `wire` and `reg` for RTL signals; use it everywhere except
  true multi-driver nets.
- `always_comb`, `always_ff`, and `always_latch` make procedural intent explicit
  and enable tool-checked design rules.
- `unique case` declares exclusive, complete decisions; `priority case` declares
  priority-ordered, complete decisions; both are checked at simulation.
- These features cost nothing at synthesis — they add information, not hardware.

---

[← Testbench Essentials](../part1-verilog/08-testbench-essentials.md) · [Table of contents](../README.md) · [Next: Enhanced Data Types →](02-enhanced-data-types.md)
