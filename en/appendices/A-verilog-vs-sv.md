# Appendix A · Verilog vs SystemVerilog

[← Debugging and Anti-Patterns](../part3-sva/16-debugging-and-antipatterns.md) · [Table of contents](../README.md) · [Next: SVA Cheat-Sheet →](B-sva-cheatsheet.md)

A quick-reference comparing Verilog (IEEE 1364-2005) with the SystemVerilog
design improvements covered in Part II. For each feature, the table states what
changed and why it matters to a designer writing synthesizable RTL.

---

## Data types

| Feature | Verilog (1364-2005) | SystemVerilog (1800-2023) | Why it helps |
|---|---|---|---|
| Net vs variable | `wire` (net), `reg` (variable) — semantics differ | `logic` for both — same 4-state, one keyword | Eliminates the confusion between `wire` and `reg`; `logic` is driven by one source and works everywhere `reg` did. See [Part II · Ch 2](../part2-systemverilog/02-enhanced-data-types.md). |
| 2-state types | None | `bit`, `byte`, `shortint`, `int`, `longint` | 2-state simulation is faster and models intended behavior more directly; useful for testbench arithmetic. |
| Enumerated types | `parameter` or `localparam` encoding | `enum logic [1:0] { IDLE, BUSY, DONE }` | Named states; synthesis and tools report state names, not numbers. See [Part II · Ch 2](../part2-systemverilog/02-enhanced-data-types.md). |
| Structures | None | `typedef struct packed { ... }` | Group related fields; packed structs are synthesizable. |
| Unions | None | `typedef union packed { ... }` | Overlay encodings in the same bits; synthesizable when packed. |
| Void type | None | `void` for tasks that return nothing | Cleaner function/task signatures. |
| String type | None | `string` (dynamic) | Useful in non-synthesizable testbench and assertion messages. |
| Integer literals | `8'b0`, base required | `'0`, `'1`, `'x`, `'z` (width-inferred) | `q <= '0` resets every bit regardless of width — no magic number needed. |

---

## Procedural blocks

| Feature | Verilog (1364-2005) | SystemVerilog (1800-2023) | Why it helps |
|---|---|---|---|
| Combinational block | `always @(*)` | `always_comb` | No sensitivity-list errors; tool infers complete list. Missing signal in `@(*)` is a common Verilog latch bug. See [Part II · Ch 5](../part2-systemverilog/05-procedural-and-operators.md). |
| Clocked block | `always @(posedge clk)` | `always_ff @(posedge clk)` | Declared intent; lint and synthesis tools flag non-FF content inside `always_ff`. |
| Latch block | Inferred from incomplete `if` in `always @(*)` | `always_latch` | Explicit; latch intent is stated, not accidental. |
| Loop variables | Must declare before `begin` | `for (int i = 0; ...)` — inline declaration | Shorter, less error-prone loops. |
| `unique`/`priority` | None | `unique case`, `priority case` | Express designer knowledge about case completeness and priority; tools check it. |
| `case inside` | None | `case (expr) inside` with wildcard ranges | Match ranges and wildcards without repeated `casex`/`casez` caveats. See [Part II · Ch 5](../part2-systemverilog/05-procedural-and-operators.md). |

---

## Operators and expressions

| Feature | Verilog (1364-2005) | SystemVerilog (1800-2023) | Why it helps |
|---|---|---|---|
| Increment/decrement | None | `i++`, `i--`, `i += n` | Concise counters and loop bookkeeping. |
| Wildcard equality | None | `==?`, `!=?` | Compare with `x`/`z` as don't-care; useful for masks. |
| Streaming operators | None | `{>>{}}, {<<{}}` | Reverse or re-slice bit streams without manual indexing. |

---

## Packages and scope

| Feature | Verilog (1364-2005) | SystemVerilog (1800-2023) | Why it helps |
|---|---|---|---|
| Shared definitions | `include` of header files or `parameter` in every module | `package` with `import` | Single definition point for enums, structs, parameters; no copy-paste drift. See [Part II · Ch 3](../part2-systemverilog/03-packages-and-scope.md). |
| Scope qualifier | None | `pkg_name::item` | Explicit namespace avoids name collisions across packages. |
| Compilation unit | Per-file | `$unit` scope | Constants visible across the compilation unit without a package. |

---

## Interfaces

| Feature | Verilog (1364-2005) | SystemVerilog (1800-2023) | Why it helps |
|---|---|---|---|
| Port bundles | Repeated individual ports in every module | `interface` + `modport` | Bus signals declared once; modports enforce direction per role. See [Part II · Ch 4](../part2-systemverilog/04-interfaces-and-modports.md). |
| Protocol in ports | None | Assertions and tasks inside an interface | Tie protocol rules to the bus, not scattered across modules. |

---

## Parameterization

| Feature | Verilog (1364-2005) | SystemVerilog (1800-2023) | Why it helps |
|---|---|---|---|
| Parameter types | `parameter` (untyped or `integer`) | Typed parameters: `parameter int`, `parameter type T` | Catches width mismatches at elaboration. See [Part II · Ch 6](../part2-systemverilog/06-parameterization-and-generate.md). |
| `localparam` | Available but limited | Full expression support | Derived constants computed from other parameters. |

---

## Quick mapping summary

```
Verilog              SystemVerilog equivalent
───────────────────────────────────────────────
wire / reg           logic  (or wire logic)
always @(*)          always_comb
always @(posedge clk) always_ff @(posedge clk)
8'b0 reset           '0
casez / casex        case inside
parameter groups     package + import
repeated ports       interface + modport
```

---

[← Debugging and Anti-Patterns](../part3-sva/16-debugging-and-antipatterns.md) · [Table of contents](../README.md) · [Next: SVA Cheat-Sheet →](B-sva-cheatsheet.md)
