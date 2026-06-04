# Part III · 14. Formal Verification Primer

[← Coverage and Vacuity](13-coverage-and-vacuity.md) · [Table of contents](../README.md) · [Next: Checkers and Libraries →](15-checkers-and-libraries.md)

## Learning objectives

- Distinguish the roles of `assert`, `assume`, and `cover` in formal verification.
- Adopt the formal mindset: a proof over *all* legal inputs, not a sampled trace.
- Constrain the input space with `assume`.
- Separate **safety** (安全性性質) from **liveness** (活性性質) properties.
- Tell bounded from unbounded proofs and read their results.
- Judge when a designer should reach for formal instead of simulation.

## Designer's mental model

Formal verification changes the question from "did this happen in the tests I
ran?" to "can this happen under all allowed behaviors?" Assertions become proof
obligations, assumptions define the legal environment, and covers ask whether a
scenario is reachable at all.

This makes assumptions as important as assertions. A too-weak assumption may let
the tool explore impossible environments; a too-strong assumption may hide the
bug. Good formal setup is therefore a model of the design's world, not just a bag
of properties.

## Start from the problem

Simulation can only say "the stimulus I ran did not break this rule." Some
questions are hard to exhaust with stimulus: can a FIFO underflow under any read
and write interleaving, can an arbiter ever grant two ports at once, or does a
deadlock appear only after a very deep state sequence?

Formal rewrites the question as "under all allowed environment behavior, must this
rule hold?" That means you write not only `assert` properties, but also `assume`
properties to define the legal environment and `cover` properties to show scenarios
are reachable. This chapter establishes those roles before introducing bounded
proof, induction, and counterexamples.

## What formal does

**Formal verification** (形式化驗證) proves a property over *every* legal input
sequence, mathematically, rather than checking the finite traces a simulation happens
to produce. Where simulation answers "the property held on the stimulus I ran,"
formal answers "the property holds on *all* stimulus, or here is a counterexample."

The same SVA properties drive both. Nothing about the assertion changes; the tool
changes. This is the practical payoff of writing intent as assertions: one property
serves both the simulation and the proof.

## assert, assume, cover in formal

In a formal setting, the three statements take on sharp, distinct roles.

- **`assert`** — an obligation the tool must *prove*. The proof either holds for all
  legal inputs or yields a counterexample trace that violates it.
- **`assume`** — a constraint the tool may *rely on*. It restricts the input space to
  the legal stimulus, so the proof considers only inputs that satisfy it.
- **`cover`** — a reachability goal the tool tries to *reach*. It asks the engine to
  produce a trace where the behavior occurs, proving the scenario is possible.

```systemverilog
// assume: the environment never writes a full FIFO (input constraint)
assume property (@(posedge clk) full |-> !wr_en);

// assert: prove the count never exceeds depth (obligation)
assert property (@(posedge clk) count <= DEPTH);

// cover: show the FIFO can actually fill (reachability)
cover  property (@(posedge clk) full);
```

The division is the heart of formal: `assume` says what the environment promises,
`assert` says what the design must guarantee given those promises, and `cover`
confirms the proof space is non-empty.

## The formal mindset

Simulation is existential about bugs: it finds a bug if your stimulus happens to hit
it. Formal is universal: it considers every input the constraints allow, so it finds
the bug *if one exists within those constraints*, no stimulus authoring required.

This shifts the engineering effort. You no longer write tests to provoke the design;
you write `assert`s for what must be true and `assume`s for what the environment may
do, and the tool searches. The risk moves accordingly: an over-tight `assume` can
silently exclude the very inputs that would expose a bug. In formal, the constraints
are as important as the assertions.

## Constraining with assume

Without constraints, formal explores *all* input combinations, including ones the
real environment never produces — illegal protocol sequences, impossible resets,
reserved opcodes. Those produce false counterexamples. `assume` carves the legal
input space:

```systemverilog
// The protocol guarantees req stays high until ack — tell the prover
assume property (@(posedge clk) $rose(req) |-> req s_until ack);

// Reset is asserted for at least the first cycle
assume property (@(posedge clk) $initstate |-> !rst_n);
```

A good constraint set is the minimum needed to exclude *illegal* inputs and nothing
more. Too few constraints flood you with false counterexamples; too many hide real
bugs. Note the duality: the same property is an `assume` on the input side of one
block and an `assert` on the output side of the block that drives it — this is how
assume/assert pairs verify an interface across a boundary.

## Safety versus liveness

Formal handles two property classes differently.

- A **safety property** says "something bad never happens." Its violation has a
  *finite* counterexample — a trace of bounded length ending at the bad cycle. FIFO
  overflow, two simultaneous grants, an `X` on a valid payload: all safety.
- A **liveness property** says "something good eventually happens." Its violation is
  an *infinite* trace in which the good event never arrives. "Every request is
  eventually granted" is liveness.

```systemverilog
// Safety: a bad state is unreachable
assert property (@(posedge clk) !(grant_a && grant_b));

// Liveness: a request is eventually served (needs unbounded reasoning)
assert property (@(posedge clk) req |-> s_eventually gnt);
```

Most RTL sign-off is safety: invariants and bounded responses. Liveness needs
unbounded proof methods and a fairness assumption (the granting mechanism is not
starved forever), so it is heavier and used more selectively.

## Bounded versus unbounded proofs

Formal engines come in two flavors of guarantee.

- A **bounded** proof (bounded model checking) verifies the property for all inputs
  up to a fixed number of cycles *N* from reset. It finds any bug reachable within
  *N* steps and is fast, but says nothing beyond the bound. A clean bounded run is
  strong evidence, not a complete proof.
- An **unbounded** proof verifies the property for *all* time, with no cycle limit.
  It gives a full guarantee but is harder to converge and may not complete on a large
  state space.

In practice a designer often starts with a bounded run to catch shallow bugs quickly,
then pursues an unbounded proof on the critical safety properties. A bounded pass to
depth *N* means "no counterexample within *N* cycles"; read it as coverage of a
window, not as a theorem.

> **Design intent.** Formal turns an assertion from a check on the traces you ran
> into a proof over every trace the environment allows. The designer states intent as
> `assert`, states the environment's promises as `assume`, and confirms reachability
> with `cover`; the tool does the searching. The mindset is universal, not
> existential — and the constraints carry as much intent as the assertions, because a
> wrong `assume` can hide the very bug you are hunting.

## When to reach for formal

Formal pays off in specific situations:

- **Control logic with deep corner cases** — arbiters, FSMs, handshake protocols —
  where the failing sequence is rare and hard to stimulate.
- **Invariants that must hold absolutely** — one-hot state, no-overflow, mutual
  exclusion — where "we never saw it fail" is not strong enough.
- **Bug hunting** on a localized block, letting the engine find the counterexample
  you could not write a test for.
- **Connectivity and configuration** checks across a large structure.

Simulation remains the right tool for data-path throughput, system-level scenarios,
and anything needing realistic stimulus over long runs. The two are complementary:
formal proves the corners, simulation exercises the whole.

## Common pitfalls

- **Over-constraining with `assume`.** A too-tight assumption excludes legal inputs
  and hides real bugs. Constrain only what is genuinely illegal.
- **Under-constraining.** Too few assumptions flood the run with false
  counterexamples from impossible inputs. Add the protocol's real guarantees.
- **Treating a bounded pass as a full proof.** Depth *N* covers only *N* cycles.
  Pursue unbounded proofs for critical safety properties.
- **Expecting liveness for free.** Liveness needs unbounded methods and fairness
  assumptions. Use bounded safety forms where a real deadline exists.
- **Forgetting `cover` in formal.** Without reachability covers, a proof may hold
  vacuously over an empty or unreachable space. Cover the key scenarios.

## Summary

- Formal proves a property over all legal inputs; simulation checks the traces you
  run.
- `assert` is an obligation to prove, `assume` constrains the input space, `cover`
  checks reachability.
- The mindset is universal: write intent and constraints, and let the tool search;
  constraints carry as much intent as assertions.
- Safety properties have finite counterexamples and dominate sign-off; liveness needs
  unbounded reasoning and fairness.
- Bounded proofs cover a fixed window quickly; unbounded proofs give a full guarantee
  but converge harder. Reach for formal on deep control logic and absolute
  invariants.

---

[← Coverage and Vacuity](13-coverage-and-vacuity.md) · [Table of contents](../README.md) · [Next: Checkers and Libraries →](15-checkers-and-libraries.md)
