# Verilog, SystemVerilog & SVA for Digital Designers — English Edition

[← Back to top](../README.md) · [繁體中文版](../zh-TW/README.md)

A guide for RTL designers. It covers the parts of Verilog and SystemVerilog you
need to write synthesizable hardware, and then treats **SystemVerilog Assertions
(SVA)** in depth, because assertions are how a designer records intent.

Read the parts in order if you are new to the languages. If you already write
RTL, jump straight to **Part III**.

## Reading style

This guide is meant to be read as a designer's working reference, not only as a
syntax list. Each chapter starts by naming the mental model behind the
construct before moving into examples and pitfalls. If you are skimming, read
that mental-model section first; it tells you what the syntax is trying to make
explicit.

## Table of contents

### Part 0 — Orientation
- [Introduction](00-introduction.md) — audience, design intent, how to read this guide.

### Part I — Verilog for Design
Synthesizable RTL, based on IEEE 1364-2005.

1. [Modules and Hierarchy](part1-verilog/01-modules-and-hierarchy.md)
2. [Data Types and Values](part1-verilog/02-data-types-and-values.md)
3. [Operators and Expressions](part1-verilog/03-operators-and-expressions.md)
4. [Combinational Logic](part1-verilog/04-combinational-logic.md)
5. [Sequential Logic](part1-verilog/05-sequential-logic.md)
6. [Finite State Machines](part1-verilog/06-finite-state-machines.md)
7. [Synthesis-Aware Coding](part1-verilog/07-synthesis-aware-coding.md)
8. [Testbench Essentials (mention only)](part1-verilog/08-testbench-essentials.md)

### Part II — SystemVerilog for Design
The SystemVerilog design subset, based on IEEE 1800-2023.

1. [Why SystemVerilog for Design](part2-systemverilog/01-why-sv-for-design.md)
2. [Enhanced Data Types](part2-systemverilog/02-enhanced-data-types.md)
3. [Packages and Scope](part2-systemverilog/03-packages-and-scope.md)
4. [Interfaces and Modports](part2-systemverilog/04-interfaces-and-modports.md)
5. [Procedural Blocks and Operators](part2-systemverilog/05-procedural-and-operators.md)
6. [Parameterization and Generate](part2-systemverilog/06-parameterization-and-generate.md)
7. [Verification Features Overview (mention only)](part2-systemverilog/07-verification-features-overview.md)

### Part III — SystemVerilog Assertions (core focus)
Practical design-intent assertions, plus advanced and formal topics.

1. [Why Assertions](part3-sva/01-why-assertions.md)
2. [Simulation Semantics](part3-sva/02-simulation-semantics.md)
3. [Assertion Kinds](part3-sva/03-assertion-kinds.md)
4. [The Boolean Layer](part3-sva/04-boolean-layer.md)
5. [Sequences: Basics](part3-sva/05-sequences-basics.md)
6. [Sequence Operations](part3-sva/06-sequence-operations.md)
7. [Properties](part3-sva/07-properties.md)
8. [Clocking and Reset](part3-sva/08-clocking-and-reset.md)
9. [Binding and Placement](part3-sva/09-binding-and-placement.md)
10. [RTL Assertion Patterns](part3-sva/10-rtl-assertion-patterns.md)
11. [Local Variables](part3-sva/11-local-variables.md)
12. [Recursive Properties](part3-sva/12-recursive-properties.md)
13. [Coverage and Vacuity](part3-sva/13-coverage-and-vacuity.md)
14. [Formal Verification Primer](part3-sva/14-formal-verification-primer.md)
15. [Checkers and Libraries](part3-sva/15-checkers-and-libraries.md)
16. [Debugging and Anti-Patterns](part3-sva/16-debugging-and-antipatterns.md)

### Appendices
- [A — Verilog vs SystemVerilog](appendices/A-verilog-vs-sv.md)
- [B — SVA Cheat-Sheet](appendices/B-sva-cheatsheet.md)
- [C — Glossary](appendices/C-glossary.md)
- [D — References](appendices/D-references.md)

---

Shared terminology: [GLOSSARY.md](../GLOSSARY.md) ·
Conventions: [CONTRIBUTING.md](../CONTRIBUTING.md)
