# Part III · 3. Assertion Kinds

[← Simulation Semantics](02-simulation-semantics.md) · [Table of contents](../README.md) · [Next: The Boolean Layer →](04-boolean-layer.md)

## Learning objectives

- Distinguish immediate, deferred, and concurrent assertions.
- Choose between `assert`, `assume`, `cover`, and `restrict`.
- Write action blocks for the pass and fail branches of an assertion.
- Pick the right severity task: `$error`, `$fatal`, `$warning`, `$info`.

## Designer's mental model

The same Boolean or temporal expression changes meaning depending on the
assertion kind and keyword around it. An immediate assertion checks a condition at
a procedural point. A concurrent assertion checks behavior over clocked time.
`assert`, `assume`, `cover`, and `restrict` then say whether the expression is a
design guarantee, an environment promise, or a reachability question.

This distinction matters most when moving between simulation and formal. In
simulation, an `assume` may act like a check or constraint depending on the tool.
In formal, a bad `assume` can remove the very behavior you needed to find. Treat
the keyword as part of the intent, not as a wrapper around a property.

## Immediate assertions

An **immediate assertion** (即時斷言) is a procedural statement. It evaluates its
expression the moment control reaches it, like an `if`, and uses the current
values of its operands. It belongs inside procedural code — an `always` block, an
`initial` block, or a task.

```systemverilog
always_comb begin
    next_state = decode(opcode);
    // Checked right here, with the value next_state just got
    assert (next_state != INVALID);
end
```

If the expression is true (or a non-zero, non-x value), the assertion passes. If
it is false, it fails and, by default, reports an error. Immediate assertions are
the right tool for a condition that must hold at a single point in procedural
flow — a decoded value, a function precondition, a case selector that should never
be the default.

## Deferred assertions

A plain immediate assertion can fire on a *glitch*: a combinational signal may
momentarily take a wrong value mid-step before settling, and an immediate
assertion would report that transient. A **deferred assertion** (延遲斷言) avoids
this by postponing its report until the end of the time step, after the design has
settled. If the condition is true again by then, nothing is reported.

There are two forms:

```systemverilog
// Observed-deferred: report at the end of the current time step
always_comb
    assert #0 (a == b);

// Final-deferred: report in the Final region (end of simulation step set)
always_comb
    assert final (a == b);
```

`assert #0` defers the report to the Observed region of the same step;
`assert final` defers it further. Both suppress reports caused by intermediate
glitches, which makes deferred assertions the preferred form for checking
combinational invariants without false alarms from transient values.

## Concurrent assertions

A **concurrent assertion** (並行斷言) is clocked and reasons over time. It samples
its signals on a clock edge (Chapter 2) and checks a temporal property that may
span many cycles. It is written with `assert property`.

```systemverilog
// Over clocked time: every request is granted on the next cycle
assert property (@(posedge clk) req |=> gnt);
```

Concurrent assertions can appear in a module, an interface, a program, or a
`checker`, and they run continuously, starting a fresh evaluation attempt on every
clock edge. This is the form used for protocols, handshakes, and FSM behavior, and
it is the focus of the rest of this part.

## assert, assume, cover, restrict

A property can be used in four roles. The keyword chooses the role.

- **`assert`** — the property *must hold*. A violation is a failure. This is the
  default way to state design intent.
- **`assume`** — the property is *taken as given*. In simulation an `assume` is
  checked like an `assert`; in formal verification it constrains the environment,
  telling the tool which inputs are legal. Use it to model the contract the design
  expects from the outside.
- **`cover`** — not a check but a *measurement*. It records whether the behavior
  actually happened, so you can confirm a scenario was exercised. A `cover` never
  fails; it either gets hit or it does not.
- **`restrict`** — like `assume`, but used only in formal to *prune* the state
  space (for example, to constrain a configuration input to one value). It has no
  effect in simulation.

```systemverilog
// Intent we are checking
assert property (@(posedge clk) wr_en |-> !full);

// Environment contract: the source never writes when full
assume property (@(posedge clk) full |-> !wr_en);

// Did we ever actually fill the FIFO during this test?
cover  property (@(posedge clk) full);

// Formal only: pin the mode input to streaming for this proof
restrict property (@(posedge clk) mode == STREAM);
```

The distinction between `assert` and `assume` is central to formal: assertions are
*obligations to prove*, assumptions are *premises you are allowed to use*.

> **Design intent.** The same property text states different intents depending on
> the keyword. `assert` says "my design guarantees this." `assume` says "the
> environment promises me this." `cover` says "I want to see this happen at least
> once." Choosing the keyword is choosing whose responsibility the behavior is.

## Action blocks

Every assertion can carry an **action block**: code that runs on pass, on fail, or
both. It follows the assertion like the branches of an `if`.

```systemverilog
assert property (@(posedge clk) req |=> gnt)
    else $error("grant did not follow request at %0t", $time);
```

The general shape has a pass branch and a fail branch:

```systemverilog
assert property (p)
    pass_count++;            // pass action (optional)
else
    $error("property p failed");   // fail action
```

The pass action is optional and often omitted. The fail action is where you report
the failure; if you omit it, the simulator still issues a default error, but a
custom message with context (cycle, signal values) is far more useful during
debug. Action blocks run in the Reactive region, after the property is evaluated.

## Severity tasks

The fail action usually calls a severity system task. They differ in how the tool
reacts:

- **`$info`** — informational; no error status. Useful inside a `cover` or for
  trace messages.
- **`$warning`** — a warning; simulation continues.
- **`$error`** — an error; simulation continues but the run is marked failed. This
  is the normal choice for a violated `assert`.
- **`$fatal`** — a fatal error; simulation stops immediately. Reserve it for
  conditions so broken that continuing is pointless.

```systemverilog
assert property (@(posedge clk) wr_ptr < DEPTH)
    else $fatal(1, "FIFO pointer overflow — design is corrupt");
```

Choose `$error` for ordinary intent violations so a regression keeps running and
reports every failure, and `$fatal` only when further simulation would be
meaningless.

## Common pitfalls

- **Using a plain immediate assertion on a glitchy combinational signal.** It can
  fire on a transient value. Use a deferred assertion (`assert #0` or
  `assert final`) for combinational invariants.
- **Confusing `assume` with `assert`.** In formal, an over-broad `assume` can hide
  real bugs by ruling out the inputs that would expose them. Assume only what the
  environment genuinely guarantees.
- **Expecting a `cover` to fail.** A `cover` measures; it never fails. If you want
  a check, use `assert`.
- **Defaulting to `$fatal`.** Stopping the run on the first violation hides every
  later failure. Use `$error` so a regression reports them all.
- **Omitting the fail message.** The default report lacks context. A custom
  `$error` with the time and key signals saves debug effort.

## Summary

- Immediate assertions check a condition at a point in procedural code; deferred
  assertions postpone the report to avoid glitch-driven false alarms.
- Concurrent assertions are clocked and reason over time with `assert property`.
- The keyword sets the role: `assert` (must hold), `assume` (given), `cover`
  (measure), `restrict` (formal pruning).
- Action blocks run on pass or fail; the fail branch reports the violation.
- Use `$error` for ordinary failures so the run continues; reserve `$fatal` for
  unrecoverable conditions.

---

[← Simulation Semantics](02-simulation-semantics.md) · [Table of contents](../README.md) · [Next: The Boolean Layer →](04-boolean-layer.md)
