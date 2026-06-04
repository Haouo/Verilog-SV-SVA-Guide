# Part I · 8. Testbench Essentials (mention only)

[← Synthesis-Aware Coding](07-synthesis-aware-coding.md) · [Table of contents](../README.md) · [Next: Part II — Why SystemVerilog for Design →](../part2-systemverilog/01-why-sv-for-design.md)

> **Scope note.** This chapter is deliberately brief. Verification — building
> testbenches, UVM, constrained-random stimulus, coverage closure — is a large
> discipline with its own literature and is **not** the focus of this guide. The
> goal here is only to let a designer recognize the basic pieces and run a quick
> check on their own block. For real verification, see the references in
> [Appendix D](../appendices/D-references.md).

## Learning objectives

- Recognize the minimal structure of a testbench.
- Drive a clock and a reset to exercise your own block.
- Know where the line between design and verification falls.

## Designer's mental model

A simple testbench is a way to create stimulus and observe behavior, not proof
that the RTL is correct. It can show that one scenario worked, but it does not by
itself state the design rule that should always hold. That missing rule is where
assertions become useful.

For a designer, the value of a small testbench is speed and visibility. It lets
you bring up a block, see waveforms, and catch obvious wiring or reset mistakes.
The moment you find yourself repeatedly looking at a waveform to decide whether
something is "right," you have found a candidate assertion.

## What a testbench is

A testbench is non-synthesizable code that instantiates your design (the
*device under test*, DUT), drives its inputs, and checks its outputs. It is a
simulation program, so it freely uses the constructs Chapter 7 told you to keep
out of RTL: `initial`, delays, and system tasks.

## A minimal testbench

```verilog
module tb;
    reg        clk = 1'b0;
    reg        rst_n;
    reg        en;
    wire [7:0] count;

    // DUT instance
    counter #(.WIDTH(8)) dut (
        .clk(clk), .rst_n(rst_n), .en(en), .count(count)
    );

    // Clock: toggle every 5 time units -> 10-unit period
    always #5 clk = ~clk;

    // Stimulus
    initial begin
        rst_n = 1'b0; en = 1'b0;   // apply reset
        #20 rst_n = 1'b1;          // release reset
        #10 en = 1'b1;             // start counting
        #100 $finish;              // end simulation
    end

    // Simple monitor
    initial
        $monitor("t=%0t count=%0d", $time, count);
endmodule
```

The pieces:

- **Clock generation** — an `always` block with a delay toggles `clk`.
- **Stimulus** — an `initial` block applies reset, then drives inputs over time.
- **Observation** — `$monitor` or `$display` prints signal values; `$finish`
  ends the run.

This is enough to bring up a block and watch it behave. It is not enough to
*verify* it.

## Where design ends and verification begins

The testbench above prints values for a human to inspect. Real verification
replaces the human with self-checking code: it predicts the correct output and
flags any difference automatically, across many directed and random scenarios,
and measures coverage to know what was exercised. That machinery — scoreboards,
drivers, monitors, constrained-random generators, UVM — is the verification
engineer's domain.

There is, however, one piece of checking that belongs to the designer: the
assertion. An assertion lives with the design, states the intent the designer
holds, and is checked automatically in *any* simulation — including the simple
testbench above. That is the subject of Part III, and the reason this guide
treats SVA in depth while treating testbenches only here.

> **Design intent.** A printed waveform shows what happened; it does not say
> whether that was correct. The designer's contribution to checking is the
> assertion, which encodes the intended behavior so a tool — not a person reading
> a log — confirms it on every run.

## Common pitfalls

- **Eyeballing waveforms as "verification."** Manual inspection misses cases and
  does not scale. It is for bring-up, not sign-off.
- **Letting testbench constructs leak into RTL.** Keep `initial`, delays, and
  `$display` in the testbench (Chapter 7).
- **Skipping assertions** because "the testbench checks it." Assertions check the
  design from the inside, in every simulation, and catch failures at their
  source.

## Summary

- A testbench instantiates the DUT, generates clock and reset, and applies
  stimulus with non-synthesizable constructs.
- A minimal testbench is enough for bring-up but not for verification.
- Self-checking, coverage, and UVM are the verification engineer's domain — out
  of scope here.
- The designer's checking tool is the assertion, covered fully in Part III.

---

[← Synthesis-Aware Coding](07-synthesis-aware-coding.md) · [Table of contents](../README.md) · [Next: Part II — Why SystemVerilog for Design →](../part2-systemverilog/01-why-sv-for-design.md)
