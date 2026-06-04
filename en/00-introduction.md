# Introduction

[← Table of contents](README.md) · [Next: Modules and Hierarchy →](part1-verilog/01-modules-and-hierarchy.md)

## Learning objectives

- Understand who this guide is for and what it assumes you already know.
- See why assertions are a designer's job, not only a verifier's.
- Learn how the three parts fit together and how to read them.

## Designer's mental model

Read this guide as a bridge between three things you already do as a designer:
describe hardware structure, choose coding forms that tools can interpret, and
write down the promises the hardware must keep. Verilog and SystemVerilog cover
the first two; SVA covers the third. The important habit is to ask, at every
construct, "What hardware fact am I making explicit?"

The chapters are intentionally not a language-lawyer tour. They are a path from
RTL syntax to design intent. When a detail seems small, such as a width rule or a
sampled-value rule, treat it as a future debug boundary: if the mental model is
clear now, the waveform later becomes much easier to read.

## Who this guide is for

This guide is for digital designers: engineers who write Register-Transfer Level
(RTL) code that a synthesis tool turns into gates. It assumes you already
understand digital logic — combinational and sequential circuits, clocking,
reset, and the basic synthesis flow. It does not teach logic design from scratch.
Instead, it teaches the languages a designer uses to describe that logic, and the
assertion language a designer uses to state what the logic must do.

The guide has three parts:

1. **Verilog for Design** — the synthesizable core of Verilog.
2. **SystemVerilog for Design** — the SystemVerilog features that make RTL
   clearer and safer.
3. **SystemVerilog Assertions (SVA)** — the main focus, covered in depth.

## Why a designer writes assertions

A designer holds knowledge that the RTL alone does not show. You know that a
request must always receive an acknowledge, that a state register is one-hot,
that a FIFO must never overflow. These facts are *design intent*. They live in
your head, in a specification, or in a comment — places a tool cannot check.

An assertion moves that intent into the code, in a form a simulator or a formal
tool can check on every cycle. When the design later violates the intent — during
your own simulation, a colleague's, or a block-level regression — the assertion
fires at the exact point of failure, not three modules downstream where the
symptom finally appears.

This is why SVA belongs to the designer. You are the one who knows the intent.
Writing it down as you write the RTL captures it while it is fresh, and turns it
into a permanent, machine-checked contract.

> **Design intent.** RTL describes *how* the hardware behaves. An assertion
> describes *what must be true* about that behavior. The two together are far
> stronger than either alone: the RTL can be wrong, but the assertion says so.

## What this guide does not cover

This is a design guide, not a verification course. Building testbenches, UVM,
class-based randomization, and coverage methodology are large topics with their
own literature. We mention them only where a designer needs to recognize them —
for example, to know where an assertion's `assume` belongs in a formal flow. The
one verification-adjacent topic we do treat fully is SVA, because it is design
intent.

## How to read this guide

If the languages are new to you, read the parts in order. Part I builds the
Verilog foundation, Part II adds the SystemVerilog design features, and Part III
uses both to express intent with assertions.

If you already write RTL, skim Parts I and II for the specific constructs you
use, then spend your time in Part III.

Each chapter follows the same shape: objectives, concepts, short illustrative
snippets, a design-intent callout, common pitfalls, and a summary. Code is
illustrative — it shows the point rather than forming a runnable project.

## Conventions

- Verilog code is fenced as `verilog`; SystemVerilog as `systemverilog`.
- Technical terms stay in English. The first use links to the
  [glossary](../GLOSSARY.md).
- Reference standards are listed in
  [Appendix D](appendices/D-references.md): IEEE 1364-2005 for Verilog and IEEE
  1800-2023 for SystemVerilog and SVA.

## Summary

- The guide is for RTL designers who already know digital logic.
- It teaches Verilog, the SystemVerilog design subset, and SVA in depth.
- Assertions are a designer's tool because the designer owns the intent.
- Testbench and verification methodology are out of scope, by design.

---

[← Table of contents](README.md) · [Next: Modules and Hierarchy →](part1-verilog/01-modules-and-hierarchy.md)
