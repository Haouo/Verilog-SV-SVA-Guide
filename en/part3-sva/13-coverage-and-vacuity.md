# Part III · 13. Coverage and Vacuity

[← Recursive Properties](12-recursive-properties.md) · [Table of contents](../README.md) · [Next: Formal Verification Primer →](14-formal-verification-primer.md)

## Learning objectives

- Use `cover property` and `cover sequence` to measure that a behavior occurred.
- Turn design intent into functional coverage from assertions.
- Understand **vacuity** (空真) and why a vacuous pass can hide a bug.
- Confirm that an implication's antecedent actually fires.
- Frame assertion verification closure: every check exercised, every trigger seen.

## Designer's mental model

A passing assertion answers only one question: no observed attempt violated this
rule. It does not prove that the interesting attempt ever happened. Coverage and
vacuity checks answer the missing question: did the trigger occur, did the window
open, and did the design exercise the behavior the assertion was meant to guard?

For every important implication, ask what evidence would convince you the check
was meaningful. Often that evidence is a `cover property` on the antecedent or a
related scenario. Assertion closure is not just green checks; it is green checks
plus confidence that the checks were actually exercised.

## Cover: did it actually happen?

An `assert` proves a behavior is *correct*. A `cover` (覆蓋) proves a behavior
*occurred* at all. They are complementary: an assertion that never fails tells you
nothing if the situation it guards never arose. `cover` closes that gap by reporting
how many times a sequence or property matched.

```systemverilog
// Count how often a back-to-back write burst occurs
cover property (@(posedge clk) wr_en ##1 wr_en ##1 wr_en);
```

When this runs, the tool reports the match count. Zero matches is a warning sign: the
stimulus never produced the scenario, so any assertion about it was never truly
tested.

## cover property versus cover sequence

Both forms measure occurrence; they differ in what they accept and report.

- **`cover sequence`** takes a sequence and reports each match, including every match
  of overlapping or multiple threads. It is the precise tool for "count occurrences
  of this temporal pattern."
- **`cover property`** takes a property. For a plain sequence it behaves like
  sequence coverage; for an implication it reports coverage of the implication
  *being evaluated*, which is usually not what you want for measuring a scenario.

```systemverilog
// Sequence coverage: every occurrence of the three-cycle pattern
cover sequence (@(posedge clk) req ##1 stall ##1 ack);

// Property coverage of a simple scenario
cover property (@(posedge clk) $rose(start) ##[1:4] done);
```

For functional-scenario coverage, write the scenario as a sequence and cover that
sequence (or a non-implication property). Reserve implication-shaped covers for
deliberate analysis of the implication itself.

## Functional coverage from intent

The same design intent that drives assertions drives coverage. For every "this must
hold" assertion, ask "did the triggering situation occur?" — and cover it. A small
set of covers documents which corners the test actually exercised:

```systemverilog
// Intent: the FIFO is exercised at both extremes
cover property (@(posedge clk) full);    // did we ever fill it?
cover property (@(posedge clk) empty);   // did we ever drain it?

// Intent: a write and read collide on the same cycle
cover property (@(posedge clk) wr_en && rd_en);
```

Covers written from intent answer the question an assertion alone cannot: *was the
intent ever put to the test?* They turn "no failures" into "no failures, and here is
what we exercised."

## Vacuity

Recall from Chapter 7 that an implication passes **vacuously** when its antecedent
never matches: there was no obligation, so the property is trivially satisfied. A
vacuous pass is logically correct, but it is also *empty* — it proves nothing about
the consequent.

```systemverilog
// If 'req' never rises, this passes every cycle without ever checking 'gnt'
assert property (@(posedge clk) $rose(req) |=> gnt);
```

The danger is silent: the report shows a passing assertion, the engineer reads
"passing" as "verified," and the consequent was never exercised. A real bug in the
grant logic would never be caught, because the grant logic was never reached. Vacuity
is how a green report can hide an untested path.

## Confirming the antecedent fires

The remedy is to verify the antecedent actually occurs, with a `cover` on it. Pairing
each implication with a cover of its trigger is a standard discipline:

```systemverilog
assert property (@(posedge clk) $rose(req) |=> gnt);
cover  property (@(posedge clk) $rose(req));   // proves the trigger was real
```

Now the report carries two facts: the grant rule held (assert), *and* a request
actually happened to test it (cover). If the cover count is zero, the passing assert
is vacuous and must not be trusted. Many tools also flag vacuous passes directly;
treat such a flag as "not yet verified," not "verified."

> **Design intent.** Assertions and coverage state the two halves of "verified."
> An assertion captures *what must be true*; a cover captures *that the situation
> was actually reached*. Vacuity is the gap between them — a check can pass simply
> because its trigger never fired. Covering the antecedent closes that gap, so a
> passing report means "correct *and* exercised," which is what a designer actually
> wants to know.

## Assertion verification closure

Closure on an assertion set means two conditions hold together:

1. **No assertion failed.** Every stated obligation was met on every attempt.
2. **No assertion passed only vacuously.** Every antecedent was covered — every
   triggering scenario was reached at least once.

A passing suite that fails the second condition is not closed; it is untested in
disguise. Practical closure therefore tracks cover counts alongside assertion
results, and treats an uncovered antecedent the same as a missing test. Formal tools
make this explicit with vacuity analysis; in simulation, the cover-the-antecedent
discipline supplies it.

## Common pitfalls

- **Reading "pass" as "verified."** A pass can be vacuous. Without a cover on the
  antecedent, a green assertion may have checked nothing.
- **Never checking cover counts.** A cover that matched zero times means the scenario
  never occurred; the related assertion was not exercised.
- **Covering an implication for scenario counts.** Cover the *sequence* (or a
  non-implication property) when you mean "count occurrences"; implication coverage
  measures something else.
- **Ignoring tool vacuity flags.** A vacuity warning marks an untested obligation.
  Treat it as unfinished, not as noise.
- **Stopping at "all assertions pass."** Closure also requires every antecedent
  covered. Track both.

## Summary

- `cover` measures that a behavior occurred; `assert` proves it was correct — the two
  are complementary.
- Use `cover sequence` (or a non-implication `cover property`) to count occurrences of
  a temporal scenario.
- A vacuous pass happens when the antecedent never matches; it proves nothing and can
  hide a bug behind a green report.
- Cover every implication's antecedent to confirm the trigger was real; a zero count
  means the assertion was never truly tested.
- Verification closure requires no failures *and* no purely vacuous passes — every
  obligation met and every trigger exercised.

---

[← Recursive Properties](12-recursive-properties.md) · [Table of contents](../README.md) · [Next: Formal Verification Primer →](14-formal-verification-primer.md)
