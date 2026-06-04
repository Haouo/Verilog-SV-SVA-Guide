# Part III · 1. Why Assertions

[← Verification Features Overview](../part2-systemverilog/07-verification-features-overview.md) · [Table of contents](../README.md) · [Next: Simulation Semantics →](02-simulation-semantics.md)

## Learning objectives

- State the difference between what RTL describes and what an assertion describes.
- Explain Assertion-Based Verification (ABV) and why it belongs to the designer.
- Place assertions in the design flow: simulation, formal, and emulation.
- Tell immediate from concurrent assertions at a glance.
- Understand why failing at the source beats failing downstream.

## Designer's mental model

An assertion is executable intent. It does not replace RTL, a testbench, or a
specification; it connects them by stating one rule the design must obey. The
best assertions are small enough to fail for one clear reason and close enough to
the RTL that the failing cycle explains the bug.

Start from English before syntax. "A request must be answered within four cycles"
is the intent; `req |-> ##[1:4] ack` is one encoding of it. If the English rule is
fuzzy, the property will be fuzzy too. Good SVA begins with a precise design
sentence.

## Start from the problem

Start with an ordinary debugging story: a downstream block receives bad data, but
the real cause was an extra FIFO write three hundred cycles earlier. With only
output checking, you see the symptom first. You still have to work backward to find
when the data went bad, which state first drifted, and which protocol rule was
violated.

Assertions close that distance. They place local rules at the source: "do not write
a full FIFO," "a grant cannot appear without a request," "the state vector remains
one-hot." This chapter first builds that motivation; immediate and concurrent
assertions, simulation, and formal verification are different ways that motivation
lands in tools.

## RTL says how; an assertion says what must be true

A piece of RTL describes *how* the hardware computes a result. It does not, on
its own, say what that result is *supposed* to be. The intent — that a request is
always acknowledged, that a state vector is one-hot, that a FIFO never overflows —
lives in your head, in a specification, or in a comment. None of those places is
checkable by a tool.

An **assertion** (斷言) is a checkable statement of intended behavior. It moves
the intent out of your head and into the source, in a form a simulator or a
formal tool evaluates automatically. The RTL and the assertion describe the same
design from two angles: the RTL says how it behaves, the assertion says what must
hold. When the two disagree, the assertion fires and tells you the RTL is wrong.

```systemverilog
// RTL: how the grant is produced
always_ff @(posedge clk)
    gnt <= req & ~busy;

// Assertion: what must be true — a grant implies a request was pending
assert property (@(posedge clk) gnt |-> $past(req));
```

The `always_ff` block is the implementation. The `assert property` is the
contract. Neither replaces the other.

## Assertion-Based Verification

**Assertion-Based Verification (ABV, 基於斷言的驗證)** is a methodology that puts
assertions at the center of how a design is checked. Instead of relying only on a
testbench that compares outputs at the boundary, you embed many small, local
checks throughout the design. Each check states one fact about one signal or
interface, close to where that fact is produced.

This matters for a designer because **you own the intent**. You know the protocol
on each port, the encoding of each state register, the invariant each counter
must keep. A verification engineer can rediscover some of this from a
specification, but you already hold it while you write the code. Capturing it then
— as an assertion next to the logic — records it while it is fresh and turns it
into a permanent, machine-checked contract that travels with the module.

ABV pays off in three ways:

- **Observability.** A bug that violates an invariant is caught at the invariant,
  not many cycles later when a corrupted value finally reaches an output.
- **Documentation.** An assertion is executable documentation. Unlike a comment,
  it cannot quietly drift out of date — if it becomes false, it fires.
- **Reuse.** The same assertions run in block-level simulation, in full-chip
  regression, and in formal, with no change.

## Where assertions live in the flow

The same assertion serves several tools across the design flow:

- **Simulation.** The assertion is evaluated every clock cycle against the actual
  signal values. A violation prints an error at the exact time and location.
- **Formal verification (形式化驗證).** A formal tool tries to *prove* the
  assertion holds for every legal input, or produces a counterexample trace if it
  cannot. Here assertions split into things to prove (`assert`) and assumptions
  about the environment (`assume`).
- **Emulation and silicon bring-up.** A synthesizable subset of assertions can run
  on emulators, and the intent they capture guides post-silicon debug.

Because one assertion serves all of these, writing it once during RTL development
multiplies its value.

## Two kinds at a glance

SystemVerilog has two broad assertion families. Later chapters treat each in
depth; here is the distinction.

An **immediate assertion** (即時斷言) is a procedural statement. It evaluates its
expression *now*, when control reaches it, exactly like an `if`. It checks a
condition at one instant.

```systemverilog
// Immediate: checked the moment this statement executes
always_comb
    assert (onehot_count <= 1);
```

A **concurrent assertion** (並行斷言) is clocked. It evaluates over time, sampling
its signals on a clock edge and reasoning about behavior across cycles. It checks
a temporal statement — something that unfolds over one or more clocks.

```systemverilog
// Concurrent: checked every clock, can span multiple cycles
assert property (@(posedge clk) req |=> gnt);
```

The rule of thumb: use an immediate assertion to check a condition at a point in
procedural code, and a concurrent assertion to check intended behavior over
clocked time. Most design intent about protocols, handshakes, and state machines
is temporal, so most of this part is about concurrent assertions.

## Failing at the source

The central benefit of an assertion is *where* it fails. Consider a corrupted
FIFO pointer. Without an assertion, the bad pointer is written, read back later,
and the wrong data leaves the FIFO; the symptom shows up several modules
downstream, perhaps thousands of cycles later, where it is hard to trace back to
the cause.

With an assertion on the pointer invariant, the failure is reported the moment the
pointer goes out of range — at the source, with the right cycle and the right
signal named. The distance between the cause and the symptom collapses to zero.
That is the difference between an afternoon of waveform archaeology and a
one-line message.

```systemverilog
// Catch the bad pointer where it happens, not downstream
assert property (@(posedge clk) disable iff (!rst_n)
    wr_ptr < DEPTH);
```

> **Design intent.** RTL captures the implementation; an assertion captures the
> promise the implementation must keep. Writing both, side by side, means a tool
> can tell you the instant the implementation breaks the promise — at the source,
> not three modules away.

## Common pitfalls

- **Treating assertions as a verifier-only concern.** The designer owns the
  intent and should write the assertions that capture it, while the logic is
  fresh.
- **Writing comments instead of assertions.** A comment cannot fire. If the intent
  is checkable, state it as an assertion so it stays honest.
- **Reaching for a concurrent assertion for a one-instant check.** A simple
  combinational invariant is an immediate assertion; do not wrap it in a clock it
  does not need.
- **Deferring all assertions to a separate verification phase.** The cheapest
  bugs to find are the ones an assertion catches the first time the code runs.

## Summary

- RTL says *how* the hardware behaves; an assertion says *what must be true*.
- ABV embeds many small checks throughout the design, owned by the designer who
  holds the intent.
- One assertion serves simulation, formal, and emulation across the flow.
- Immediate assertions check a condition at an instant; concurrent assertions
  check behavior over clocked time.
- Assertions fail at the source, collapsing the distance between cause and
  symptom.

---

[← Verification Features Overview](../part2-systemverilog/07-verification-features-overview.md) · [Table of contents](../README.md) · [Next: Simulation Semantics →](02-simulation-semantics.md)
