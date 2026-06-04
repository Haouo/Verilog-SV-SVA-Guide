# Part I · 6. Finite State Machines

[← Sequential Logic](05-sequential-logic.md) · [Table of contents](../README.md) · [Next: Synthesis-Aware Coding →](07-synthesis-aware-coding.md)

## Learning objectives

- Structure an FSM into clear, separate concerns.
- Write the recommended two-block style.
- Understand Moore versus Mealy outputs.
- Choose a state encoding and avoid lockup states.

## Designer's mental model

An FSM is a named control contract. The state register says which phase the block
is in; the next-state logic says what transitions are legal; the output logic
says what each phase promises to the rest of the design. Keeping those roles
separate makes the machine easier to debug and easier to assert.

Do not read an FSM only as a collection of `case` branches. Read it as a graph:
which states are legal, which edges are allowed, what events cause movement, and
what recovery path exists if the state becomes illegal. That graph is often the
best place to derive assertions later.

## What an FSM is in RTL

A finite state machine (FSM) is control logic modeled as a set of states, the
transitions between them, and the outputs each state produces. Most control paths
in a design — handshakes, protocols, arbiters — are FSMs. The challenge is not
the concept but writing it so the code is clear and synthesizes cleanly.

An FSM has three concerns:

1. **State register** — the clocked storage of the current state.
2. **Next-state logic** — combinational logic deciding the next state.
3. **Output logic** — combinational logic producing outputs.

Coding styles differ in how they group these concerns.

## The two-block style (recommended)

Separate the clocked state register from the combinational next-state and output
logic. This keeps the sequential and combinational parts cleanly divided.

```verilog
module fsm (
    input  wire clk,
    input  wire rst_n,
    input  wire start,
    input  wire done,
    output reg  busy
);
    // State encoding (see encoding section)
    localparam [1:0] IDLE = 2'd0,
                     RUN  = 2'd1,
                     WAIT = 2'd2;

    reg [1:0] state, next;

    // Block 1: state register (sequential)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) state <= IDLE;
        else        state <= next;
    end

    // Block 2: next-state and output logic (combinational)
    always @* begin
        next = state;     // default: hold state, avoids a latch
        busy = 1'b0;      // default output
        case (state)
            IDLE: if (start) next = RUN;
            RUN:  begin
                      busy = 1'b1;
                      if (done) next = WAIT;
                  end
            WAIT: next = IDLE;
            default: next = IDLE;   // recover from illegal states
        endcase
    end
endmodule
```

The defaults at the top of the combinational block are essential: `next = state`
and `busy = 1'b0` guarantee every path assigns both signals, so no latch is
inferred (Chapter 4).

Some designers prefer a *three-block* style that splits next-state and output
into two separate combinational blocks. It is equally valid; use it when the
output logic is large enough to benefit from its own block. A *one-block* style
that puts everything in a clocked block also works but registers the outputs,
which changes their timing — know that before choosing it.

## Moore versus Mealy

- **Moore** outputs depend only on the current state. `busy` above is Moore: it
  is set by the state, not by the inputs. Moore outputs are stable for the whole
  state and easy to reason about.
- **Mealy** outputs depend on the current state *and* the inputs. They can react
  one cycle earlier but can also glitch with the inputs and complicate timing.

Prefer Moore outputs for control signals unless you specifically need the earlier
response of a Mealy output.

## State encoding

The `localparam` values choose how states map to bits:

- **Binary** — `2'd0, 2'd1, ...`. Fewest flip-flops; more next-state logic.
- **One-hot** — one bit per state (`4'b0001, 4'b0010, ...`). More flip-flops,
  simpler and faster next-state logic. Common on FPGAs, where flip-flops are
  plentiful.
- **Gray** — adjacent states differ by one bit; useful in specific cases.

Use named `localparam` constants regardless of encoding, so the encoding is one
decision in one place. Many synthesis tools can re-encode an FSM automatically,
but explicit named states keep the source readable.

## Illegal states and recovery

With binary encoding of, say, three states in two bits, the value `2'b11` is
unused. Noise, an SEU, or a bug could land the FSM there. The `default: next =
IDLE` branch sends any unexpected state back to a safe one. Always provide it.
This is also a natural place for an assertion: "state is always one of the legal
values" (Part III).

> **Design intent.** An FSM *is* design intent made explicit: these are the legal
> states, these are the allowed transitions, this is what each state drives. The
> two-block style, named states, and a recovering `default` write that intent
> plainly. Assertions later prove the machine never takes a transition you did
> not allow.

## Common pitfalls

- **No default in the combinational block.** Missing `next = state` or a default
  output infers a latch.
- **Magic-number states.** Use named `localparam` constants.
- **No illegal-state recovery.** Add a `default` that returns to a safe state.
- **Unintended Mealy outputs.** Reading inputs in the output logic makes outputs
  combinational on those inputs; do it only when intended.
- **Registering outputs by accident** with a one-block style when you wanted
  combinational outputs.

## Summary

- An FSM has a state register, next-state logic, and output logic.
- The two-block style cleanly splits sequential from combinational; default the
  combinational outputs to avoid latches.
- Prefer Moore outputs for stable control signals.
- Name states with `localparam`, pick an encoding deliberately, and always
  recover from illegal states.

---

[← Sequential Logic](05-sequential-logic.md) · [Table of contents](../README.md) · [Next: Synthesis-Aware Coding →](07-synthesis-aware-coding.md)
