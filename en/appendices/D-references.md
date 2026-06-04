# Appendix D · References

[← Glossary](C-glossary.md) · [Back to table of contents](../README.md)

An annotated bibliography mapping the guide's three parts to their governing
sources and key supplementary literature.

## How to use this appendix

References are the backstop for the guide's technical claims. Use the standards
for normative language rules, and use books or papers for design practice,
examples, and interpretation. When a chapter grows more detailed, this appendix
is where the supporting source should become visible.

---

## Governing standards

**IEEE Std 1364-2005 — IEEE Standard for Verilog Hardware Description Language.**
Institute of Electrical and Electronics Engineers, 2006.
*The normative authority for Part I. All Verilog syntax, semantics, and simulation
behavior in this guide are defined against this standard.*

**IEEE Std 1800-2023 — IEEE Standard for SystemVerilog — Unified Hardware Design,
Specification, and Verification Language.**
Institute of Electrical and Electronics Engineers, 2023.
*The normative authority for Parts II and III. Supersedes IEEE 1800-2017.
Assertion semantics, sampled-value model, sequence and property algebra, clocking
blocks, and checkers are all specified here.*

---

## SVA in depth

**Cohen, Ben; Venkataramanan, Srinivasan; and Kumari, Ajeetha.**
*SystemVerilog Assertions Handbook.* 4th ed. Createspace, 2015.
*The most thorough practical treatment of SVA. Covers the full assertion language
with worked examples, methodology guidance, and simulation/formal tool usage.
Recommended for designers who want to go beyond this guide's scope.*

**Cohen, Ben; Venkataramanan, Srinivasan; Kumari, Ajeetha; and Piper, Lisa.**
*A Practical Guide to Adopting the Universal Verification Methodology (UVM).*
Covers SVA integration in a verification environment; complements the assertion
methodology in Part III.

**SystemVerilog Assertions 应用指南 [SystemVerilog Assertions Application Guide].**
*A Chinese-language practical reference for SVA patterns. Useful alongside Part III
for readers who prefer a Chinese primary source for assertion coding patterns.*

---

## Synthesizable SystemVerilog

**Sutherland, Stuart.**
"Synthesizable SystemVerilog: Taming the Beast."
*SNUG (Synopsys Users Group) conference paper, 2013.*
*A concise, tool-focused guide to which SystemVerilog constructs are synthesizable
and which are not — essential reading before using Part II features in production.*

**Sutherland, Stuart; and Mills, Don.**
"Verilog and SystemVerilog Gotchas: 101 Common Coding Errors and How to Avoid Them."
*SNUG conference paper.*
*Covers the most frequent mistakes designers make when moving from Verilog to
SystemVerilog. Pairs directly with Part II's pitfall sections.*

---

## Design-intent and ABV methodology

**Bening, Lionel; and Foster, Harry D.**
*Principles of Verifiable RTL Design: A Functional Coding Style Supporting
Verification Processes in Verilog.* 2nd ed. Kluwer Academic, 2001.
*The foundational text on writing RTL with verification in mind. Introduces the
design-intent principle that motivates assertion-based verification (ABV) as used
throughout Part III.*

---

## Verification context (out of scope for this guide)

**Spear, Chris; and Tumbush, Greg.**
*SystemVerilog for Verification: A Guide to Learning the Testbench Language Features.*
3rd ed. Springer, 2012.
*Covers constrained-random verification, coverage-driven verification, and the
class-based OOP features of SystemVerilog. This guide deliberately leaves out the
verification side of the language; Spear & Tumbush is the recommended next step
for designers who need to write testbenches.*

---

## Further reading

- The **Accellera** website (accellera.org) archives earlier SystemVerilog
  language reference manuals and the original donation documents, useful for
  understanding how the language evolved.
- **SNUG** (snug-universal.org) and **DVCon** proceedings contain a large body
  of practitioner papers on SVA methodology, formal verification flows, and
  synthesizable coding styles — most are freely available after registration.
- Tool vendors (Synopsys, Cadence, Siemens EDA, Aldec) publish application notes
  for their specific simulators and formal engines; consult these when the
  standard's semantics interact with tool-specific behavior.

---

[← Glossary](C-glossary.md) · [Back to table of contents](../README.md)
