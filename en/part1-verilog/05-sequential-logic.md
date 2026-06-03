# Part I · 5. Sequential Logic

[← Combinational Logic](04-combinational-logic.md) · [Table of contents](../README.md) · [Next: Finite State Machines →](06-finite-state-machines.md)

## Learning objectives

- Infer flip-flops with a clocked `always` block.
- Use non-blocking assignments for sequential logic and know why.
- Choose between synchronous and asynchronous reset.
- Avoid the classic blocking/non-blocking race.

## Inferring a flip-flop

Sequential logic has state that updates on a clock edge. You infer a flip-flop
with an `always` block triggered by a clock edge:

```verilog
always @(posedge clk) begin
    q <= d;
end
```

This says: on each rising edge of `clk`, `q` takes the value of `d`. That is a
D flip-flop. The `posedge` (or `negedge`) edge in the sensitivity list is what
makes the logic sequential rather than combinational.

## Non-blocking assignment for sequential logic

Inside clocked blocks, use the non-blocking assignment `<=`, not the blocking
`=`. This is one of the most important rules in Verilog.

- **Blocking (`=`)** executes immediately, in order, like a software statement.
- **Non-blocking (`<=`)** samples all right-hand sides first, then updates all
  left-hand sides together at the end of the time step.

Non-blocking assignment models how real flip-flops behave: they all sample their
inputs on the edge, then all update together. Consider a shift register:

```verilog
// Correct: all three FFs sample, then all update
always @(posedge clk) begin
    q1 <= d;
    q2 <= q1;
    q3 <= q2;
end
```

With `<=`, `q2` gets the *old* `q1`, exactly as hardware does, giving a 3-stage
shift register. If you used `=` here, `q1` would update first, then `q2` would
read the *new* `q1`, collapsing the shift register into a single stage. The
keyword choice changes the hardware.

The matching rule from Chapter 4 completes the pair:

- **Sequential (clocked) logic → non-blocking `<=`.**
- **Combinational logic → blocking `=`.**

Follow this and you avoid most assignment-related bugs.

## Reset

A flip-flop usually needs a reset to reach a known state. There are two styles.

### Synchronous reset

Reset is sampled on the clock edge, like any other input:

```verilog
always @(posedge clk) begin
    if (rst)
        q <= '0;
    else
        q <= d;
end
```

Synchronous reset keeps everything in the clocked domain, which is friendly to
timing analysis and to most FPGA fabrics. Its drawback: it needs a running clock
to take effect.

### Asynchronous reset

Reset takes effect immediately, independent of the clock, by appearing in the
sensitivity list:

```verilog
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        q <= '0;
    else
        q <= d;
end
```

Asynchronous reset (here active-low `rst_n`) forces the state the moment reset
asserts, even with no clock. Its drawback is reset *release*: if reset
de-asserts too close to a clock edge, the flip-flop can go metastable, so the
release must be synchronized.

Choose one style and apply it consistently across a clock domain. Mixing reset
styles within a domain causes trouble.

> **Design intent.** A reset is a promise: "after reset, every state element holds
> a known value." Writing the reset branch for every flip-flop, with a consistent
> style, states that promise. An assertion such as "after reset, `q == 0`" (Part
> III) turns the promise into something a tool checks.

## The blocking/non-blocking race

If you assign the same variable with `=` in one block and read it in another in
the same time step, the result depends on the order the simulator runs the
blocks — a race. Following the two rules above (`<=` for clocked, `=` for
combinational, and never mixing them for the same signal) eliminates these races.
Do not assign one variable from two `always` blocks, and never mix `=` and `<=`
to the same variable.

## A complete register example

```verilog
module counter #(
    parameter int WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             en,
    output reg  [WIDTH-1:0] count
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= '0;
        else if (en)
            count <= count + 1'b1;
    end
endmodule
```

Note the structure: asynchronous reset first, then the synchronous behavior.
`count` holds when `en` is low — that is intended state retention in a clocked
block, not a latch.

## Common pitfalls

- **Blocking assignment in clocked logic.** It breaks shift registers and creates
  races. Use `<=`.
- **Mixing `=` and `<=`** to the same variable. Pick one per block per the rules.
- **Two blocks driving one register.** Each state element has exactly one driver.
- **Inconsistent reset style** within a clock domain. Choose sync or async and
  stick to it.
- **Forgetting reset on state that needs it.** Unreset flip-flops start at `x`.

## Summary

- A clocked `always @(posedge clk)` block infers flip-flops.
- Use `<=` in clocked logic and `=` in combinational logic.
- Synchronous reset stays in the clock domain; asynchronous reset acts at once
  but needs a synchronized release.
- Keep one driver per register and a consistent reset style per domain.

---

[← Combinational Logic](04-combinational-logic.md) · [Table of contents](../README.md) · [Next: Finite State Machines →](06-finite-state-machines.md)
