# Part III · 5. Sequences: Basics

[← The Boolean Layer](04-boolean-layer.md) · [Table of contents](../README.md) · [Next: Sequence Operations →](06-sequence-operations.md)

## Learning objectives

- Describe a sequence as a pattern of booleans over clock cycles.
- Use fixed and ranged cycle delays `##n` and `##[m:n]`.
- Use unbounded delays `##[*]` and `##[+]`.
- Repeat with consecutive `[*n]`, goto `[->n]`, and non-consecutive `[=n]`.
- Name a reusable sequence with the `sequence` construct.

## What a sequence is

A **sequence** (序列) describes events over clock cycles: a pattern of boolean
conditions that must hold at successive sampling points. Where the boolean layer
(Chapter 4) talks about one edge, a sequence talks about a run of edges. Sequences
are the building blocks of properties (Chapter 7).

The simplest sequence is a single boolean — it matches at one cycle. Sequences get
their power from *cycle delays* that string booleans together across time.

## Cycle delays: ##n

The cycle-delay operator `##n` advances `n` clocks of the assertion clock. Read
`a ##1 b` as "`a` this cycle, then `b` the next cycle":

```systemverilog
// req this cycle, gnt the very next cycle
sequence req_then_gnt;
    req ##1 gnt;
endsequence
```

`##0` means "the same cycle" — both booleans are sampled at the same edge, so
`a ##0 b` is equivalent to `a && b`. Larger numbers skip cycles:

```systemverilog
// start, then exactly two cycles later, done
sequence start_done;
    start ##2 done;        // start at cycle k, done at cycle k+2
endsequence
```

The cycles in between are not constrained by `##2` — only the endpoints are
checked. If you need to constrain the gap, use repetition (below) or a sequence
operation (Chapter 6).

## Ranged delays: ##[m:n]

A delay can be a *range*, meaning "somewhere between `m` and `n` cycles later":

```systemverilog
// done arrives 1 to 3 cycles after start
sequence start_done_window;
    start ##[1:3] done;
endsequence
```

This matches if `done` is true at *any* cycle in the window. It is the natural way
to express a latency that has slack — "the result comes back within three cycles"
— rather than a fixed pipeline depth. A ranged delay can produce several matches
of the same sequence; Chapter 6's `first_match` trims that to the earliest.

## Unbounded delays: ##[*] and ##[+]

Two shorthands cover open-ended waits:

- **`##[*]`** is `##[0:$]` — zero or more cycles, unbounded.
- **`##[+]`** is `##[1:$]` — one or more cycles, unbounded.

```systemverilog
// After req, gnt happens eventually (some cycle, 1 or more later)
sequence req_eventually_gnt;
    req ##[+] gnt;
endsequence
```

The `$` means "no upper bound." Use unbounded delays for "eventually" patterns
where no fixed deadline applies. Be aware that in pure simulation an unbounded wait
may never complete within the test; pair such patterns with a strong property
(Chapter 7) or a bounded window when you need a real deadline.

## Consecutive repetition: [*n] and [*m:n]

`b[*n]` means the boolean `b` holds on `n` consecutive cycles. It is shorthand for
writing `b ##1 b ##1 ...`:

```systemverilog
// stall held high for exactly 4 consecutive cycles
sequence stall4;
    stall[*4];
endsequence

// busy held high for 2 to 5 consecutive cycles
sequence busy_run;
    busy[*2:5];
endsequence
```

Consecutive repetition is how you state "held for N cycles" — a hold time, a fixed
stall, a minimum pulse width. A sequence can also be repeated, not just a boolean:
`(a ##1 b)[*3]` repeats the two-cycle pattern three times back to back.

## Goto repetition: [->n]

`b[->n]` is the **goto** repetition: it matches at the cycle of the `n`-th
occurrence of `b`, where the occurrences need not be consecutive. The match point
is exactly when the count reaches `n`:

```systemverilog
// From req, wait until the 3rd ack (acks may be spread out), then ready
sequence three_acks;
    req ##1 ack[->3] ##1 ready;
endsequence
```

Here `ack[->3]` advances through cycles until `ack` has been true three times, and
the match lands on that third `ack`. The `##1 ready` then checks the cycle right
after the third `ack`. Use goto repetition to count occurrences of an event that
arrives irregularly.

## Non-consecutive repetition: [=n]

`b[=n]` is the **non-consecutive** repetition. Like goto, it counts `n`
occurrences of `b` that need not be consecutive, but the match point is *not*
pinned to the last occurrence — it may extend past it, allowing cycles where `b`
is false after the `n`-th match:

```systemverilog
// Exactly two writes occur, then (later) a flush
sequence two_writes_then_flush;
    wr[=2] ##1 flush;
endsequence
```

The difference from goto is subtle but real:

- `b[->n] ##1 c` requires `c` the cycle immediately after the `n`-th `b`.
- `b[=n] ##1 c` allows idle cycles (where `b` is false) between the `n`-th `b` and
  `c`.

Use `[->n]` when the next event must immediately follow the counted one, and `[=n]`
when there may be a gap.

## Naming sequences

A sequence written inline is fine for one use. When a pattern is reused, or is
complex enough to deserve a name, declare it with the `sequence` construct, which
can take arguments:

```systemverilog
// Parameterized, reusable handshake sequence
sequence ack_within(int n);
    req ##[1:n] ack;
endsequence

assert property (@(posedge clk) $rose(req) |-> ack_within(4));
```

Naming a sequence documents intent and lets the same pattern be asserted, covered,
and reused across the design. Arguments make one declaration serve many latencies
or widths.

> **Design intent.** A sequence captures the *shape over time* of an intended
> behavior: request then grant, four-cycle stall, the third acknowledge. Cycle
> delays and repetition let you draw that shape exactly — fixed depth with `##n`,
> a latency window with `##[m:n]`, a hold time with `[*n]`, a counted event with
> `[->n]`. The sequence is the designer's timing diagram, written so a tool can
> check it.

## Common pitfalls

- **Reading `##2` as "within 2 cycles."** It means *exactly* two cycles later.
  For a window, use `##[1:2]`.
- **Confusing `[*n]` with `[->n]`.** `[*n]` requires `n` *consecutive* cycles;
  `[->n]` counts `n` *occurrences* that may be spread out.
- **Confusing `[->n]` with `[=n]`.** Goto pins the match to the last occurrence;
  non-consecutive allows trailing idle cycles before the next term.
- **Unbounded delays in pure simulation.** `##[+]` may never complete within a
  finite test. Use a bounded window or a strong property when a deadline is
  required.
- **Inlining a complex sequence everywhere.** Name it with `sequence` so the
  intent is documented once and reused, and so a fix lands in one place.

## Summary

- A sequence is a pattern of booleans over clock cycles, built on the boolean
  layer.
- `##n` is an exact delay, `##[m:n]` a window, `##[*]`/`##[+]` unbounded waits.
- `[*n]` repeats consecutively; `[->n]` counts occurrences and pins the match to
  the last; `[=n]` counts occurrences but allows trailing idle cycles.
- Name reusable or complex sequences with `sequence`, optionally parameterized.

---

[← The Boolean Layer](04-boolean-layer.md) · [Table of contents](../README.md) · [Next: Sequence Operations →](06-sequence-operations.md)
