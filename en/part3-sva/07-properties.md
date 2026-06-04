# Part III · 7. Properties

[← Sequence Operations](06-sequence-operations.md) · [Table of contents](../README.md) · [Next: Clocking and Reset →](08-clocking-and-reset.md)

## Learning objectives

- Distinguish a property from a sequence.
- Use overlapping `|->` and non-overlapping `|=>` implication.
- Identify the antecedent and consequent, and understand vacuous pass.
- Combine properties with `not`, `and`, `or`, and `if/else`.
- Use the temporal operators `nexttime`, `until`, `eventually`, and their strong
  forms.
- Name and parameterize a property.

## Designer's mental model

A property turns patterns into obligations. The antecedent names the trigger; the
consequent names what the design must do when that trigger occurs. Implication is
therefore a contract shape: if the left side happens, the right side must hold at
the specified time.

Most property bugs are contract bugs. The antecedent may be too broad, too rare,
or accidentally impossible; the consequent may start one cycle too early or too
late; the property may pass vacuously because the trigger never happened. Read
every implication as a sentence and check both halves.

## Start from the problem

A sequence only answers "did this time shape appear?" Design rules usually go
further: "if a request appears, a response must appear by the deadline," or "if a
FIFO is full, a write must never happen." Those sentences have a trigger and an
obligation after the trigger.

A property is where a shape becomes an obligation. The antecedent asks "what opens
the check?" The consequent asks "what does the design owe us after that?" The
`|->`, `|=>`, vacuity, and strong or weak temporal operators in this chapter refine
that contract: when the obligation starts, how long it lasts, and what it means if
the trigger never happens.

## Property versus sequence

A **sequence** (序列) describes a pattern that *matches* or does not. A
**property** (性質) is a statement that *holds* or *fails* — it is the thing an
`assert`, `assume`, or `cover` evaluates. Properties are built from sequences,
booleans, and the operators in this chapter. The most important of those operators
is implication.

## Implication

Implication links a triggering pattern to a required response. The left side is
the **antecedent** (前提); the right side is the **consequent** (後件). The
property says: *whenever the antecedent matches, the consequent must hold.*

There are two forms, differing only in when the consequent starts.

### Overlapping: |->

`|->` is **overlapping** implication. The consequent is checked starting at the
*same* cycle the antecedent completes:

```systemverilog
// In the same cycle req is high, gnt must already be high
assert property (@(posedge clk) req |-> gnt);
```

Read `a |-> b` as "when `a`, then `b` *now*."

### Non-overlapping: |=>

`|=>` is **non-overlapping** implication. The consequent is checked starting the
cycle *after* the antecedent completes:

```systemverilog
// One cycle after req, gnt must be high
assert property (@(posedge clk) req |=> gnt);
```

Read `a |=> b` as "when `a`, then `b` *next cycle*." It is exactly equivalent to
`a |-> ##1 b`. Choosing between `|->` and `|=>` is choosing whether the response is
simultaneous or one cycle later — a distinction that maps directly onto whether a
handshake is combinational or registered.

## Antecedent, consequent, and vacuity

When the antecedent does *not* match at a given start, the implication is
considered satisfied for that start — there was no obligation to meet. This is a
**vacuous pass** (空真 / 空泛成立).

```systemverilog
// If req is never high, this passes vacuously every cycle —
// the consequent gnt is never required
assert property (@(posedge clk) req |=> gnt);
```

Vacuity is correct and necessary: "every request is granted" should not fail simply
because no request occurred. But it has a trap. A property that *only ever* passes
vacuously is checking nothing, and gives false confidence. The remedy is a `cover`
on the antecedent, to confirm it actually happened:

```systemverilog
// Confirm the antecedent is real, not just vacuously satisfied
cover property (@(posedge clk) req);
```

Pairing an implication with a `cover` of its antecedent is a standard discipline:
the `assert` proves the response, the `cover` proves the trigger occurred.

## Property operators: not, and, or, if/else

Properties compose with logical operators of their own:

- **`not p`** — holds when property `p` fails. Use it to state that a behavior must
  *never* happen.
- **`p1 and p2`** — both must hold.
- **`p1 or p2`** — at least one must hold.
- **`if (cond) p1 else p2`** — choose a property based on a boolean condition.

```systemverilog
// An overflow must never follow a write to a full FIFO
assert property (@(posedge clk) not (wr_en && full ##1 overflow));

// Different latency depending on mode
assert property (@(posedge clk)
    start |=> if (fast_mode) done else ##1 done);
```

`not` is the natural form for a **safety property** (安全性性質) — "something bad
never happens." The `if/else` form lets one assertion cover several configurations
without duplicating the antecedent.

## Temporal property operators

Beyond implication, properties have temporal operators borrowed from temporal
logic. Each comes in a *weak* and a *strong* form; the strong form additionally
requires the awaited event to actually occur within the trace.

### nexttime and s_nexttime

- **`nexttime p`** — `p` must hold in the next cycle (weak).
- **`s_nexttime p`** — `p` must hold in the next cycle, and that next cycle must
  exist (strong).

```systemverilog
assert property (@(posedge clk) start |-> nexttime busy);
```

### until, s_until, until_with, s_until_with

- **`p until q`** — `p` holds every cycle up to (but not including) the cycle `q`
  becomes true; weak, so `q` need not ever occur.
- **`s_until`** — strong: `q` *must* eventually become true.
- **`until_with` / `s_until_with`** — same, but `p` must also hold *at* the cycle
  `q` becomes true (the endpoint is included).

```systemverilog
// req must stay asserted until ack, and ack must eventually arrive
assert property (@(posedge clk) $rose(req) |-> req s_until ack);
```

The weak/strong choice answers "must the release event actually happen?" For a
handshake where `ack` is guaranteed, use the strong form so a missing `ack` is a
failure; for a best-effort condition, the weak form is right.

### eventually and s_eventually

- **`s_eventually p`** — `p` must hold at some future cycle (strong, may be
  unbounded). This is the form for a **liveness property** (活性性質) — "something
  good eventually happens."
- **`eventually [m:n] p`** — the weak, *bounded* form: `p` must hold within the
  given cycle window.

```systemverilog
// After request, a grant must eventually be issued (liveness)
assert property (@(posedge clk) req |-> s_eventually gnt);
```

Liveness properties cannot be falsified by any finite simulation trace — there is
always "more time" — so `s_eventually` is mainly a formal-verification tool. In
simulation, prefer a bounded form (`##[1:N]` or `eventually [1:N]`) that imposes a
real deadline.

## Naming properties

As with sequences, declare a reusable or complex property with `property`, and give
it arguments to serve many instances:

```systemverilog
// Reusable request/acknowledge property
property req_ack(req, ack, int n);
    @(posedge clk) $rose(req) |-> ##[1:n] ack;
endproperty

assert property (req_ack(rd_req, rd_ack, 4));
assert property (req_ack(wr_req, wr_ack, 8));
```

A named property documents the intent once and applies it everywhere the pattern
recurs, which keeps a fleet of similar checks consistent and easy to maintain.

> **Design intent.** A property is the full statement of intent: *this trigger
> demands this response.* Implication names the trigger (antecedent) and the
> obligation (consequent); `not` states what must never happen; the temporal
> operators state what must hold until, or happen by, some event. Vacuity keeps
> the statement honest about cases the trigger never fired — pair it with a
> `cover` so you know the trigger was real.

## Common pitfalls

- **Confusing `|->` and `|=>`.** Overlapping checks the consequent in the same
  cycle; non-overlapping checks it the next cycle. Match the form to whether the
  response is combinational or registered.
- **Ignoring vacuity.** An implication that only passes vacuously checks nothing.
  Cover the antecedent to confirm it occurs.
- **Using `s_eventually` in simulation.** A liveness property has no finite
  counterexample. Use a bounded window for a real deadline in simulation; reserve
  `s_eventually` for formal.
- **Forgetting the endpoint with `until`.** Plain `until` excludes the cycle `q`
  holds; use `until_with` when `p` must also hold at that cycle.
- **Picking the weak form when the event is guaranteed.** If the release event must
  occur, use the strong `s_` form so its absence is a failure, not a silent pass.

## Summary

- A sequence matches; a property holds or fails and is what `assert`/`cover`
  evaluates.
- `|->` checks the consequent in the same cycle; `|=>` checks it the next cycle.
- A vacuous pass occurs when the antecedent never matches; cover the antecedent to
  keep the check meaningful.
- `not`, `and`, `or`, and `if/else` compose properties; `not` expresses safety.
- `nexttime`, `until`/`until_with`, and `eventually` have weak and strong forms;
  strong forms require the awaited event to occur and suit formal, while bounded
  forms suit simulation.

---

[← Sequence Operations](06-sequence-operations.md) · [Table of contents](../README.md) · [Next: Clocking and Reset →](08-clocking-and-reset.md)
