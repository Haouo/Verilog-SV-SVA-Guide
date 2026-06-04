# The Ultimate Guide of Verilog, SystemVerilog & SVA for Digital Designers

> A from-the-designer's-chair guide to writing RTL in Verilog and SystemVerilog,
> and to expressing **design intent** with SystemVerilog Assertions (SVA).

This guide is written for **digital (RTL) designers** — the engineers who shape
combinational and sequential logic into synthesizable hardware. It treats
assertions as a *first-class designer responsibility*: SVA is how you state, in
machine-checkable form, what your design is *supposed* to do.

## Choose your language · 選擇語言

| | |
|---|---|
| 🇬🇧 **English** | **[Start reading →](en/README.md)** |
| 🇹🇼 **繁體中文** | **[開始閱讀 →](zh-TW/README.md)** |

## What you'll learn

1. **Part I — Verilog for Design.** Synthesizable RTL: modules, data types,
   combinational and sequential logic, FSMs, and synthesis-aware coding.
2. **Part II — SystemVerilog for Design.** The SystemVerilog *design* subset that
   makes RTL clearer and safer — `logic`, `always_comb/_ff`, enums, structs,
   packages, interfaces, and parameterization.
3. **Part III — SystemVerilog Assertions (the core focus).** From "why
   assertions = design intent" through sequences, properties, clocking, the
   `bind` workflow, a practical RTL assertion-pattern library, and the advanced
   and formal-verification topics (local variables, recursion, vacuity, liveness).

## What's *out of scope*

This is a **design** guide, not a verification-methodology course. Testbench
construction, UVM, class-based randomization, and functional-coverage
methodology are **mentioned only** where a designer needs to recognize them, with
pointers to dedicated verification literature. The one assertion topic that *is*
covered deeply — because it is design intent — is SVA.

## Editorial direction

The guide favors clear explanation over terse reference prose. Chapters build a
mental model first, then show syntax, examples, design-intent callouts, pitfalls,
and summaries. The Traditional Chinese edition intentionally keeps common RTL,
SystemVerilog, and SVA terms in English after the first gloss, so readers can map
the prose directly back to code and standards.

## How it's organized

The same chapter set exists in both languages, mirrored file-for-file. Code
examples are **illustrative snippets** (not a runnable project), chosen to make
each concept concrete. Each chapter follows a consistent shape: objectives →
concepts → snippets → a **design-intent callout** → common pitfalls → summary.

- Shared bilingual terminology: [GLOSSARY.md](GLOSSARY.md)
- Authoring conventions (for contributors): [CONTRIBUTING.md](CONTRIBUTING.md)
- Editorial status and review checklist: [docs/CONTENT_STATUS.md](docs/CONTENT_STATUS.md)

## License / status

Educational material in progress. Reference standards and books used while
authoring are listed in each language's `appendices/D-references.md`. Current
chapter status is tracked in [docs/CONTENT_STATUS.md](docs/CONTENT_STATUS.md).
