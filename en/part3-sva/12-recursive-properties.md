# Part III · 12. Recursive Properties

[← Local Variables](11-local-variables.md) · [Table of contents](../README.md) · [Next: Coverage and Vacuity →](13-coverage-and-vacuity.md)

## Learning objectives

- Define a **recursive property** (遞迴性質) that refers to itself.
- State an unbounded temporal requirement compactly.
- Apply the rules that keep a recursive property well-formed.
- Recognize when recursion expresses intent more clearly than a long operator chain.

## Designer's mental model

Recursive properties describe intent that repeats its own shape. They are not
needed for most RTL checks, but they can express unbounded or inductive behavior
more naturally than a long chain of fixed delays. The designer must still provide
a clear exit condition, or the recursion becomes impossible to reason about.

Reach for recursion only when the protocol itself is self-similar: continue this
rule until a terminating event, keep accepting the same form of progress, or
prove a structure by induction. If a bounded window is enough, a simpler sequence
is usually clearer.

## Start from the problem

Most design rules have a clear deadline: respond in one to four cycles, hold for
three cycles, or drop on the next cycle. Delays, repetitions, and until operators
cover those cases. A smaller class of rules looks like "until this ends, apply the
same rule again," such as staying busy forever after lock, or carrying an
obligation forward one cycle at a time.

Recursive properties are only worth introducing for that self-similar shape. They
are not a trick for making properties smarter; they are a compact way to write
"this holds now, and next cycle we are back to the same question." This chapter
shows that unfolding before warning when recursion is the wrong tool.

## What a recursive property is

A named property may mention itself in its own body. Each reference applies the same
property one cycle further along, so a finite definition describes an obligation that
extends over unbounded time. This is a **recursive property**.

The canonical example is "hold forever after a trigger." Without recursion you would
need an unbounded operator; with recursion the definition is one line that re-invokes
itself each cycle:

```systemverilog
// Once 'lock' is set, 'busy' must stay high for every following cycle
property stays_busy;
    busy and nexttime stays_busy;
endproperty

assert property ($rose(lock) |-> stays_busy);
```

Read `stays_busy` as: "`busy` holds now, *and* `stays_busy` holds from the next
cycle." Unrolling it gives `busy ##1 busy ##1 busy ...` without end — a compact way
to state an invariant that must persist indefinitely.

## A recursion with an exit

A recursion that never stops states a pure "forever" requirement. More often the
obligation continues *until* some condition releases it. An `if/else` (or implication)
gives the recursion a base case:

```systemverilog
// After 'grant', 'hold' must remain high every cycle until 'done',
// and 'done' ends the obligation
property hold_until_done;
    hold and (done or nexttime hold_until_done);
endproperty

assert property ($rose(grant) |-> hold_until_done);
```

Each cycle the property requires `hold`, and then either `done` arrives (the
recursion stops, satisfied) or the property re-applies next cycle. The recursive
form makes the "every cycle until release" intent explicit in a way a single operator
sometimes cannot, especially when the per-cycle obligation is more than a plain
boolean.

## Rules for well-formed recursion

Recursion in SVA is restricted so that every instance is decidable. The key rules:

- **Advance through time.** A recursive instance must be reached only after a
  positive time step — that is, behind a `nexttime`, `##1`, or equivalent delay. A
  property that re-invokes itself at the *same* cycle would have no base in time and
  is illegal.
- **No negation around the recursion.** A recursive property may not appear under
  `not`, nor on the left of an implication, nor anywhere its truth would have to be
  known "negatively." Recursion is allowed only in a positive position.
- **Mutual recursion is allowed**, subject to the same constraints: two properties
  may each reference the other, provided every cycle of the loop advances time and
  stays positive.
- **No local-variable hazards.** A recursive property generally may not pass local
  variables through the recursion in a way that would require unbounded distinct
  storage; keep per-cycle state in the design or in bounded form.

These rules guarantee the recursion either terminates at a base case or makes
definite progress each cycle, so the tool can evaluate it.

## When to reach for recursion

Most everyday checks need no recursion: bounded windows (`##[1:N]`), `until`, and
`throughout` cover the common cases and read clearly. Recursion earns its place when:

- the per-cycle obligation is a richer property than a single boolean, so a plain
  `until` cannot carry it; or
- the requirement is genuinely unbounded and you want it stated as a self-similar
  rule rather than a strong temporal operator; or
- the structure is naturally inductive, such as a protocol whose each step imposes
  the same shape on the remainder.

```systemverilog
// Each transfer in a burst must look the same as the burst contract,
// applied to the remaining beats
property beat_then_rest;
    beat_ok and (last or nexttime beat_then_rest);
endproperty

assert property (burst_start |-> beat_then_rest);
```

> **Design intent.** A recursive property states an intent that is *self-similar in
> time*: "this rule holds now, and the same rule holds for what follows." It lets a
> designer write an unbounded or inductive requirement as one clear, finite
> definition, instead of an awkward chain of operators. Used sparingly, it captures
> "keep behaving this way until released" exactly as the protocol means it.

## Common pitfalls

- **Recursing at zero delay.** A self-reference without a time step is illegal and
  has no base in time. Always advance through `nexttime` or `##1`.
- **Recursion under negation.** Placing a recursive property under `not` or on the
  antecedent side breaks the positivity rule. Keep recursion in a positive position.
- **Forgetting the base case.** A recursion with no exit states a strict "forever"
  rule. If the obligation should end, add a releasing condition (`done`, `last`).
- **Using recursion where a bounded operator fits.** For a fixed window or a simple
  hold-until, `##[1:N]`, `until`, or `throughout` are clearer. Reserve recursion for
  unbounded or inductive intent.

## Summary

- A recursive property references itself, applied one cycle later, to describe an
  unbounded or inductive obligation in a finite definition.
- Each cycle must advance time and stay in a positive position; same-cycle or negated
  recursion is illegal.
- An `if/else` or implication base case lets the obligation end at a release
  condition.
- Reach for recursion when the per-cycle obligation is richer than a boolean, or the
  requirement is naturally self-similar in time; otherwise prefer bounded operators.

---

[← Local Variables](11-local-variables.md) · [Table of contents](../README.md) · [Next: Coverage and Vacuity →](13-coverage-and-vacuity.md)
