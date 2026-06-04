# Part II · 6. Parameterization and Generate

[← Procedural Constructs and Operators](05-procedural-and-operators.md) · [Table of contents](../README.md) · [Next: Verification Features Overview →](07-verification-features-overview.md)

## Learning objectives

- Declare typed `parameter` and `localparam` values.
- Use `$bits` and `$clog2` to compute derived parameters.
- Write `generate` blocks with `for`, `if`, and named scopes.
- Build parameterized, reusable design modules.

## Designer's mental model

Parameterization moves design choices to elaboration time. A parameterized module
is a template for a family of hardware, and `generate` selects or repeats
structure before simulation or synthesis begins. Think of parameters as part of
the module contract: callers choose legal values, and the module derives the
internal widths and instances that follow from them.

The danger is that a flexible module can become under-specified. Every parameter
should have a meaning, range, and consequence. Derived `localparam` values are
important because they turn caller choices into stable internal facts, making the
implementation easier to read and harder to misuse.

## Typed parameters

In Verilog, parameters are untyped integers. SystemVerilog allows parameters to
carry explicit types, which improves error checking and documents intent.

```systemverilog
module fifo #(
    parameter int          DEPTH     = 16,    // must be positive integer
    parameter int          DATA_W    = 8,     // bit width
    parameter bit          FALL_THRU = 1'b0  // boolean flag
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic [DATA_W-1:0] wdata,
    input  logic              push,
    output logic [DATA_W-1:0] rdata,
    output logic              pop_valid
);
```

Typing a parameter as `int` means the tool checks that the override value is a
compatible integer. Typing it as `bit` documents that it is a boolean. Typed
parameters catch overrides like `DEPTH = -1` or `FALL_THRU = 5` at elaboration,
not at simulation.

### `localparam`

`localparam` is a parameter that cannot be overridden at instantiation. Use it
for constants derived from other parameters:

```systemverilog
module fifo #(
    parameter int DEPTH  = 16,
    parameter int DATA_W = 8
) ( ... );

    localparam int PTR_W  = $clog2(DEPTH);    // pointer width
    localparam int BITS   = $bits(logic [DATA_W-1:0]) * DEPTH; // total storage

endmodule
```

`localparam` values appear in the elaborated hierarchy but cannot be changed by a
parent. Use `parameter` only for values that callers should be able to override.

## System functions for parameters

### `$bits`

`$bits(expression)` returns the total number of bits in an expression or type.
It evaluates at elaboration time.

```systemverilog
typedef struct packed {
    logic [15:0] addr;
    logic [31:0] data;
    logic [3:0]  byte_en;
    logic        valid;
} req_t;

localparam int REQ_BITS = $bits(req_t);   // 53
```

`$bits` is essential when a downstream module must know the width of a struct or
array without manually counting fields.

### `$clog2`

`$clog2(n)` returns the ceiling of log base 2 of `n`. It is the standard way to
compute the number of address bits needed for a memory of depth `n`.

```systemverilog
parameter int DEPTH = 1024;
localparam int ADDR_W = $clog2(DEPTH);   // 10

logic [ADDR_W-1:0] rd_addr, wr_addr;
```

`$clog2(1)` returns 0. For depths that are not powers of two, `$clog2` gives the
minimum number of bits to address all entries.

## `generate` blocks

`generate` blocks allow structural conditionals and loops at elaboration time.
They create hardware structure, not run-time behavior. Everything inside a
`generate` block is resolved before simulation or synthesis begins.

### `generate for` — replicating structure

`genvar` is an elaboration-time integer used as the loop variable in a generate
for loop. It does not exist as a hardware signal.

```systemverilog
module parity_tree #(
    parameter int N = 8   // number of input bits
) (
    input  logic [N-1:0] in,
    output logic         parity
);
    // Generate a reduction tree of XOR gates
    generate
        genvar i;
        for (i = 0; i < N; i++) begin : gen_xor
            if (i == 0)
                assign parity_stage[i] = in[i];
            else
                assign parity_stage[i] = parity_stage[i-1] ^ in[i];
        end
    endgenerate

    logic [N-1:0] parity_stage;
    assign parity = parity_stage[N-1];

endmodule
```

The `begin : gen_xor` label names the generate scope. Named scopes allow
hierarchical references to items inside them: `gen_xor[3].parity_stage` is
accessible from outside in a testbench. Labels are optional but recommended for
readability and debuggability.

A more common pattern is to instantiate replicated modules:

```systemverilog
module replicated_adder #(
    parameter int LANES  = 4,
    parameter int DATA_W = 8
) (
    input  logic [LANES-1:0][DATA_W-1:0] a,
    input  logic [LANES-1:0][DATA_W-1:0] b,
    output logic [LANES-1:0][DATA_W:0]   sum
);
    generate
        genvar i;
        for (i = 0; i < LANES; i++) begin : gen_add
            assign sum[i] = {1'b0, a[i]} + {1'b0, b[i]};
        end
    endgenerate

endmodule
```

Four adders are elaborated, one per lane. The parameter `LANES` controls how many.
A parent that needs 8 lanes overrides `LANES = 8` and gets 8 adders without
editing the module.

### `generate if` — conditional structure

`generate if` selects between alternative hardware structures at elaboration time.
It is an elaboration-time conditional, not a run-time `if`.

```systemverilog
module registered_adder #(
    parameter int  DATA_W    = 8,
    parameter bit  PIPELINED = 1'b1   // 1 = add a register stage
) (
    input  logic             clk,
    input  logic [DATA_W-1:0] a, b,
    output logic [DATA_W:0]  sum
);
    generate
        if (PIPELINED) begin : gen_pipe
            logic [DATA_W:0] sum_comb;
            always_comb  sum_comb = {1'b0, a} + {1'b0, b};
            always_ff @(posedge clk) sum <= sum_comb;
        end else begin : gen_comb
            always_comb  sum = {1'b0, a} + {1'b0, b};
        end
    endgenerate

endmodule
```

When `PIPELINED = 1'b1`, the tool elaborates the `gen_pipe` branch and discards
`gen_comb`. When `PIPELINED = 1'b0`, the reverse applies. The resulting hardware
is completely different, but the module interface is the same.

### Omitting the `generate` keyword

In SystemVerilog, the `generate` / `endgenerate` keywords are optional. A `for`
loop or `if` that appears directly in a module body with a `genvar` is still a
generate construct. Omitting the keywords is legal and common in modern code:

```systemverilog
module gray_encoder #(parameter int N = 4) (
    input  logic [N-1:0] bin,
    output logic [N-1:0] gray
);
    assign gray[N-1] = bin[N-1];

    for (genvar i = 0; i < N-1; i++) begin : gen_bits
        assign gray[i] = bin[i+1] ^ bin[i];
    end

endmodule
```

Both styles — with and without `generate` / `endgenerate` — are correct. Pick one
and be consistent within a project.

## A complete parameterized example

```systemverilog
package mem_pkg;
    parameter int DEFAULT_DEPTH = 256;
    parameter int DEFAULT_WIDTH = 8;
endpackage

module sync_ram
    import mem_pkg::*;
#(
    parameter int DEPTH = DEFAULT_DEPTH,
    parameter int WIDTH = DEFAULT_WIDTH
) (
    input  logic                  clk,
    input  logic                  we,
    input  logic [$clog2(DEPTH)-1:0] waddr,
    input  logic [WIDTH-1:0]         wdata,
    input  logic [$clog2(DEPTH)-1:0] raddr,
    output logic [WIDTH-1:0]         rdata
);
    localparam int ADDR_W = $clog2(DEPTH);

    logic [WIDTH-1:0] mem [DEPTH];

    always_ff @(posedge clk) begin
        if (we)
            mem[waddr] <= wdata;
        rdata <= mem[raddr];
    end

endmodule
```

This module works for any power-of-two depth and any width. The address width
is computed automatically with `$clog2`. Parameters come from a package for
project-wide consistency.

> **Design intent.** A parameterized module is a reusable specification, not just
> a specific piece of hardware. The parameter list is the contract: callers
> declare their requirements, and the module adapts. `localparam` derived values
> are promises: "given your `DEPTH`, I will compute the right address width" —
> and the tool verifies the arithmetic at elaboration.

## Common pitfalls

- **Using `genvar` as a run-time signal.** A `genvar` only exists at elaboration.
  It cannot be used in `always` blocks or `assign` statements outside the generate
  loop header. Use a regular `int` in procedural code.
- **Forgetting `begin : label` on multi-statement generate bodies.** Without
  `begin / end`, only the first statement is in the generate loop. This is the
  same rule as for `if` and `for` in procedural code — include the block even
  for one-statement bodies in generate to make the scope visible.
- **Using `generate if` on a run-time condition.** The condition must be a
  constant expression evaluable at elaboration. A condition that depends on a
  run-time signal is not a generate condition; write a run-time `if` in an
  `always` block instead.
- **`$clog2(0)` is undefined.** If `DEPTH` could be 0, guard the computation:
  ensure `DEPTH >= 1` through an assertion or parameter constraint.
- **Parameter type mismatch.** Passing a negative value or a real number to an
  `int` parameter is caught only if the parameter is typed. If you omit the type,
  the tool may silently truncate or coerce the value.

## Summary

- Typed `parameter` values document intent and enable elaboration-time checking.
- `localparam` expresses derived constants that callers cannot override.
- `$bits` measures any type at elaboration; `$clog2` computes the minimum address
  width for a given depth.
- `generate for` replicates structure; `generate if` selects between alternatives;
  both resolve at elaboration, before simulation or synthesis.
- Named generate scopes (`begin : label`) improve readability and enable
  hierarchical references.

---

[← Procedural Constructs and Operators](05-procedural-and-operators.md) · [Table of contents](../README.md) · [Next: Verification Features Overview →](07-verification-features-overview.md)
