# Part III · 6. Sequence Operations

[← Sequences: Basics](05-sequences-basics.md) · [Table of contents](../README.md) · [Next: Properties →](07-properties.md)

## Learning objectives

- Combine sequences with `and`, `or`, and `intersect`.
- Constrain a sequence's duration with `throughout` and `within`.
- Collapse multiple matches to the earliest with `first_match`.
- Use a sequence as a boolean event with `.triggered` and `.ended`.

## Combining sequences

Chapter 5 built single sequences. Real intent often combines several patterns —
two things that must both happen, or a condition that must hold for the whole span
of another. The sequence operations express these combinations.

### and

`seq1 and seq2` matches when *both* sequences match, each starting at the same
cycle. They need not end together; the combined match ends at the later of the two
endpoints:

```systemverilog
// From start, both a 2-cycle data path and a 3-cycle control path complete
sequence both_paths;
    (start ##2 data_ok) and (start ##3 ctrl_ok);
endsequence
```

Use `and` when two independent things must both happen from a common start, with no
requirement that they take the same number of cycles.

### or

`seq1 or seq2` matches when *either* sequence matches. It is the choice operator:

```systemverilog
// A response is either an ack next cycle or a nak two cycles later
sequence resp;
    (req ##1 ack) or (req ##2 nak);
endsequence
```

### intersect

`intersect` is like `and`, but stricter: both sequences must match *and* have the
**same length**. They start together and end together:

```systemverilog
// Two patterns that must both hold over exactly the same window
sequence locked_window;
    (busy[*1:$]) intersect (req ##[1:$] done);
endsequence
```

Use `intersect` when the two behaviors must occupy the identical span — same start,
same end. If you only care that both occur from a common start, use `and`.

## throughout: a condition over a span

`expr throughout seq` requires the boolean `expr` to hold true at *every* cycle of
the sequence `seq`. It is the way to say "this stays true for the whole duration of
that":

```systemverilog
// Enable must stay high for the entire 4-cycle burst
sequence held_burst;
    en throughout (start ##1 d1 ##1 d2 ##1 d3);
endsequence
```

If `en` drops at any cycle during the burst, the sequence fails. `throughout` is
the standard way to express a hold condition tied to another sequence's lifetime —
a chip-select that must stay asserted across a transfer, a flag that must remain
set for the length of an operation.

## within: containment

`seq1 within seq2` requires `seq1` to match somewhere *inside* the span of `seq2`:
`seq1` starts at or after `seq2` starts and ends at or before `seq2` ends:

```systemverilog
// A single ack pulse must occur somewhere within the busy window
sequence ack_in_busy;
    (ack[*1]) within (busy[*1:$]);
endsequence
```

`within` is containment: the inner pattern is bracketed by the outer one. Use it
when an event must occur during a known window but its exact position within the
window is not fixed.

## first_match: take the earliest

A sequence with a ranged or unbounded delay can match in several ways — `req
##[1:3] gnt` matches whenever `gnt` arrives at cycle +1, +2, or +3. `first_match`
keeps only the *earliest* match and discards the rest:

```systemverilog
// Once gnt arrives, stop looking; commit to the first match
sequence first_gnt;
    first_match(req ##[1:3] gnt);
endsequence
```

This matters when a later term depends on the match point, or when you want to
attach an action exactly once per request rather than once per possible match.
`first_match` is the usual way to make a windowed sequence behave like a single,
definite event.

## Sequences as events: .triggered and .ended

A sequence can be used as a boolean that is true at the cycle the sequence
*completes*. Two methods expose this, mainly for relating sequences on different
clocks or for using one sequence's completion as another's start condition.

- **`seq.triggered`** — true in the cycle in which `seq` reaches a match. It is
  evaluated as an endpoint test and is the form normally used to detect a
  sequence's completion from outside it, including across clock domains.
- **`seq.ended`** — also true when `seq` matches its end, with the match point
  defined at the end of the sequence.

```systemverilog
sequence s_req;
    $rose(req) ##1 hold;
endsequence

// When s_req completes, the grant logic must respond next cycle
assert property (@(posedge clk) s_req.triggered |=> gnt);
```

Both let a sequence's completion act as a single-cycle boolean event, so you can
chain or cross-reference sequences. For most single-clock intent you will write
implications directly (Chapter 7); `.triggered` and `.ended` come into their own
in multiclock and modular assertion structures.

> **Design intent.** The sequence operations let a designer state how separate
> timed behaviors relate: both must happen (`and`), either may (`or`), they must
> coincide exactly (`intersect`), one must hold throughout another (`throughout`),
> one must sit inside another (`within`). These mirror the words you already use
> for a protocol — "while busy, hold enable"; "ack within the window" — and turn
> them into checkable form.

## Common pitfalls

- **Using `and` when you mean `intersect`.** `and` lets the two sequences differ
  in length; `intersect` forces equal length. Pick the one that matches the
  intent.
- **Confusing `throughout` and `within`.** `throughout` holds a *boolean* across a
  sequence's whole span; `within` places a *sequence* inside another's span.
- **Forgetting `first_match` on a windowed sequence.** Without it, a `##[m:n]`
  delay can produce multiple matches, multiplying actions or confusing later
  terms.
- **Reaching for `.triggered` on a single clock unnecessarily.** Direct
  implication is clearer for same-clock intent; reserve `.triggered`/`.ended` for
  multiclock or for reusing a completion as an event.

## Summary

- `and` requires both sequences (any lengths); `or` requires either; `intersect`
  requires both with equal length.
- `throughout` holds a boolean across a sequence's whole duration; `within`
  contains one sequence inside another.
- `first_match` collapses a multi-match sequence to its earliest match.
- `.triggered` and `.ended` expose a sequence's completion as a single-cycle
  event, useful for chaining and multiclock assertions.

---

[← Sequences: Basics](05-sequences-basics.md) · [Table of contents](../README.md) · [Next: Properties →](07-properties.md)
