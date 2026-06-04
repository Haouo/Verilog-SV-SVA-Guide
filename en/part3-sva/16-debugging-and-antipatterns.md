# Part III · 16. Debugging and Anti-Patterns

[← Checkers and Libraries](15-checkers-and-libraries.md) · [Table of contents](../README.md) · [Next: Appendix A — Verilog vs SystemVerilog →](../appendices/A-verilog-vs-sv.md)

## Learning objectives

- Read a failing assertion: find the attempt's start, not just its failure cycle.
- Trace a failure back through the antecedent to the responsible cycle.
- Recognize the common SVA mistakes and the anti-patterns behind them.
- Apply good-practice guidelines that keep assertions trustworthy.

This is the closing chapter of Part III. It assumes everything before it — sampling
(Chapter 2), implication and vacuity (Chapters 7, 13), clocking and reset (Chapter 8),
and the patterns of Chapter 10 — and turns to what goes wrong and how to fix it.

## Designer's mental model

A failed assertion is a debugging instrument. It should tell you which intent was
violated, when the violating attempt started, and what evidence made the
consequent fail. If a property is too large, clocked on the wrong edge, or allowed
to pass vacuously, it stops being an instrument and becomes noise.

Debugging SVA is therefore partly debugging the design and partly debugging the
specification. When an assertion fails, check both: the RTL may be wrong, or the
property may have encoded the wrong rule. A good anti-pattern list trains you to
recognize the second case quickly.

## Reading a failing assertion

When a concurrent assertion fails, the tool reports the cycle the obligation was
violated. That cycle is the *end* of the story, not the start. A property begins a new
**attempt** each time its antecedent could match; the failure you see belongs to one
specific attempt that started some cycles earlier. Debugging means finding *that*
attempt's start.

```systemverilog
// Reported failure is at the cycle gnt should be high but isn't;
// the attempt started 1..N cycles earlier, when req rose
assert property ($rose(req) |-> ##[1:N] gnt);
```

The procedure:

1. **Note the failure cycle** the tool reports — the consequent's deadline.
2. **Walk back to the antecedent match** that opened this attempt. For `$rose(req)
   |-> ##[1:N] gnt`, that is the `$rose(req)` cycle within the last *N* cycles.
3. **Inspect the window between them.** The bug is whatever made the consequent miss
   its obligation across that span — a missing `gnt`, a dropped request, a state that
   went wrong mid-window.

Most assertion debuggers draw this attempt span on the waveform, highlighting the
start, the steps, and the failing cycle. Read the span, not the single red marker:
the cause is almost always upstream of where the failure is flagged.

## Tracing through the antecedent

A subtle failure is one where the *antecedent* is the real bug. If an assertion fails
"unexpectedly," check whether the antecedent matched when it should not have:

```systemverilog
// If this fails, ask first: did 'start' really rise here,
// or is the antecedent firing on a glitch the design didn't intend?
assert property ($rose(start) |=> busy);
```

A failure can mean the consequent is wrong *or* that the antecedent fired in a
situation the designer never meant to constrain. Reading the antecedent's sampled
value at the attempt start distinguishes the two: a real trigger with a broken
response is a design bug; a spurious trigger is an assertion that is too broad.

## Common mistakes and anti-patterns

### Wrong clock or wrong edge

Sampling on a clock or edge that does not match the logic produces failures that look
random because the assertion sees values half a cycle off (Chapter 8).

```systemverilog
// ANTI-PATTERN: design captures on posedge, assertion samples negedge
assert property (@(negedge clk) load |=> q == $past(d));
// FIX: match the capture edge
assert property (@(posedge clk) load |=> q == $past(d));
```

### Missing disable iff

An assertion with no reset guard fires during the unknown start-up window and reports
failures that are really just reset behavior.

```systemverilog
// ANTI-PATTERN: no reset guard — fires during reset
assert property (@(posedge clk) req |=> gnt);
// FIX: disable during reset
assert property (@(posedge clk) disable iff (!rst_n) req |=> gnt);
```

### Vacuity hiding a bug

An implication whose antecedent never fires passes vacuously and verifies nothing
(Chapter 13). A green report then hides an untested path.

```systemverilog
// ANTI-PATTERN: trusting this pass without checking the trigger ever occurred
assert property (mode_x && start |=> done);
// FIX: cover the antecedent so a zero count exposes the vacuity
cover property (mode_x && start);
```

### Operators too strong or too weak

A strong operator where the event is not guaranteed turns a legal case into a
failure; a weak operator where the event *is* guaranteed lets a real miss pass
silently (Chapter 7).

```systemverilog
// Too strong: forces ack to occur even when the protocol allows abort
assert property ($rose(req) |-> req s_until ack);
// Right strength when ack may legitimately never come:
assert property ($rose(req) |-> req until ack);
```

Choose the weak form for best-effort conditions and the strong form only when the
release event is contractually guaranteed.

### An antecedent that never fires

An over-specific antecedent — too many conjuncts, an impossible combination — never
matches, so the assertion is permanently vacuous. The cover count of zero is the tell
(Chapter 13). Simplify the antecedent until it captures the real trigger.

### One assertion doing too much

A single property packing many obligations, local-variable bookkeeping, and nested
operators is hard to read, hard to debug, and reports a failure without saying *which*
part broke.

```systemverilog
// ANTI-PATTERN: one giant property, opaque on failure
assert property (
    $rose(req) |-> (gnt && !err) ##1 (data_ok throughout (busy[*1:$] ##1 done))
                   and ##[1:8] resp
);
// BETTER: split into focused, independently reported checks
a_gnt:  assert property ($rose(req) |-> gnt && !err);
a_data: assert property ($rose(req) ##1 busy |-> data_ok throughout (busy[*1:$] ##1 done));
a_resp: assert property ($rose(req) |-> ##[1:8] resp);
```

Several small, named assertions each pinpoint their own failure and document one
intent apiece. Prefer them over a single monolith.

## Good-practice guidelines

- **One intent per assertion.** Small, named checks isolate failures and read as
  documentation. Name them so the report points at the intent.
- **Set the clock and reset once.** Use `default clocking` and `default disable iff`
  so no assertion drifts to the wrong edge or fires during reset (Chapter 8).
- **Cover every antecedent.** Pair each implication with a cover of its trigger so
  vacuity cannot hide behind a green report (Chapter 13).
- **Match operator strength to the contract.** Strong forms only when the event is
  guaranteed; weak forms for best-effort.
- **Capture data with local variables, not ad-hoc logic.** For pipelined checks, a
  local variable binds the response to its specific trigger cleanly (Chapter 11).
- **Bind separate assertions; keep the RTL clean.** Reusable checks live in checkers
  and bound modules, not edited into the design (Chapters 9, 15).
- **Read the attempt span, not the marker.** On a failure, walk back to the antecedent
  start and inspect the whole window.

> **Design intent.** An assertion is only as trustworthy as it is debuggable and
> honest. A failure should point clearly at one broken intent; a pass should mean the
> intent was actually exercised. The anti-patterns all blur one of those: a wrong
> clock makes failures lie, vacuity makes passes lie, and an overloaded property makes
> failures unreadable. Good practice keeps each assertion a small, clocked,
> covered, single statement of intent — so when it speaks, a designer can believe it.

## Common pitfalls

- **Debugging from the failure cycle alone.** The cause is in the attempt window that
  started earlier. Walk back to the antecedent.
- **Wrong clock or edge.** Produces failures that look random. Match the design's
  capture edge.
- **Missing `disable iff`.** Reset-time activity reported as failures. Guard with
  `disable iff` or `default disable iff`.
- **Trusting a vacuous pass.** A never-firing antecedent verifies nothing. Cover the
  antecedent and watch for a zero count.
- **Mismatched operator strength.** Too strong fails legal cases; too weak hides real
  misses. Match the contract.
- **Monolithic assertions.** Hard to debug and opaque on failure. Split into small,
  named checks.

## Summary

- A failing assertion reports the violation cycle; the cause lies in the attempt that
  started earlier — walk back to the antecedent and read the whole window.
- The recurring anti-patterns are wrong clock or edge, missing `disable iff`, vacuity
  hiding a bug, mismatched operator strength, a never-firing antecedent, and one
  assertion doing too much.
- Good practice: one intent per named assertion, clock and reset set once, every
  antecedent covered, operator strength matched to the contract, data captured with
  local variables, and reusable checks bound rather than edited in.
- An assertion is trustworthy only when its failures are readable and its passes are
  non-vacuous.

This closes Part III. The appendices that follow collect quick references — starting
with a Verilog-versus-SystemVerilog comparison.

---

[← Checkers and Libraries](15-checkers-and-libraries.md) · [Table of contents](../README.md) · [Next: Appendix A — Verilog vs SystemVerilog →](../appendices/A-verilog-vs-sv.md)
