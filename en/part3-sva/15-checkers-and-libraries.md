# Part III · 15. Checkers and Libraries

[← Formal Verification Primer](14-formal-verification-primer.md) · [Table of contents](../README.md) · [Next: Debugging and Anti-Patterns →](16-debugging-and-antipatterns.md)

## Learning objectives

- Use the `checker` construct as a reusable container for assertions.
- Pass signals and parameters into a checker and bind it like a module.
- Compare a `checker` with a property and with an assertion module.
- Know the standard reusable assertion libraries: OVL and the Accellera SVA library.
- Package your own assertions for reuse across a project.

## Designer's mental model

A checker is a reusable assertion container with a named interface. It lets a
team package a protocol rule once and instantiate it wherever the same rule
appears. A library then becomes a vocabulary of design intent: no overflow,
stable until accept, one-hot, latency bounded, and so on.

The useful interface of a checker is small but precise. It should expose the
signals, parameters, clocking, and reset needed to state the rule, while hiding
the SVA details that callers should not rewrite. Reuse is valuable only if the
checker name and parameters make the intent unmistakable.

## Start from the problem

When the same handshake appears in ten modules, copying ten properties looks fast
until it becomes maintenance work: some copies forget the antecedent cover, some use
different latency parameters, and some miss the reset condition. What you really
want to reuse is not a few lines of syntax, but a complete protocol-checking unit.

Checkers and libraries package that unit: a clear port list, parameters,
clock/reset conventions, and the assert/cover pair together. The caller supplies
signals and protocol parameters without rewriting the property internals.

## The checker construct

A **checker** (checker) is a SystemVerilog container built specifically to hold
assertions, covers, and the modeling code that supports them. It is like a module in
that it has ports and can be instantiated or bound, but it is dedicated to
verification: it may contain `assert`, `assume`, `cover`, sequences, properties, and
limited procedural modeling, and it is meant to be reused.

```systemverilog
// A reusable request/acknowledge checker
checker req_ack_chk (logic clk, logic rst_n, logic req, logic ack, int unsigned n);
    default clocking cb @(posedge clk); endclocking
    default disable iff (!rst_n);

    a_ack: assert property ($rose(req) |-> ##[1:n] ack);
    c_req: cover  property ($rose(req));
endchecker
```

The checker packages a complete, self-documenting unit of intent — the assertion,
its matching cover, and the clock and reset convention — behind a named interface.
Anywhere this handshake shape recurs, one instantiation applies the whole bundle.

## Instantiating and binding a checker

A checker is instantiated like a module, by name with port connections. The natural
way to attach one to a design is `bind` (Chapter 9), so the design source stays
untouched:

```systemverilog
// Attach the checker to every fifo instance, forwarding its ports
bind fifo req_ack_chk u_chk (
    .clk   (clk),
    .rst_n (rst_n),
    .req   (rd_req),
    .ack   (rd_ack),
    .n     (4)
);
```

Because a checker takes ports and parameters, one definition adapts to many sites:
different signal names map through the ports, and a parameter like the latency bound
`n` tunes the check per instance. Binding the checker keeps the reusable verification
code entirely outside the RTL.

## Checker versus property versus assertion module

Three constructs can hold assertions; they sit at different scales.

- A **named property** is the smallest reusable unit: one temporal statement, with
  arguments. Use it for a single recurring shape (Chapter 7).
- A **`checker`** is a purpose-built bundle of several assertions, covers, and
  supporting modeling, with its own ports and parameters. Use it when a *set* of
  related checks travels together — a protocol's whole contract, say.
- A **plain assertion module** (Chapter 9) also bundles assertions, but it is a
  general module repurposed for verification. A `checker` is the construct the
  language provides *for this job*: it permits verification modeling that a module
  may restrict, and it signals intent clearly.

Choose the smallest that fits: a property for one rule, a checker for a related set,
and reserve a full module when you need module-level features a checker does not
offer.

## Reusable assertion libraries

You rarely need to write the common checks from scratch. Two bodies of reusable
assertions are widely available.

### OVL (Open Verification Library)

OVL is an Accellera library of pre-packaged checker components — overflow,
one-hot, handshake, FIFO, and many more — usable from Verilog and SystemVerilog. Each
checker is instantiated with parameters describing the specific case. OVL predates
broad SVA support and remains useful where a tool or flow favors instantiable
checkers over inline SVA.

### Accellera SVA standard checker library

The SVA standard checker library is a set of `checker`-based components written in
native SVA, covering the same recurring intents — data stability, handshake, gray
code, parity, and so on — as parameterized checkers. Being native SVA, it composes
cleanly with your own assertions and binds the same way.

```systemverilog
// Conceptual: instantiate a library checker rather than hand-writing it
// (exact name and ports depend on the library version)
bind dma assert_handshake #(.MIN(1), .MAX(8))
    u_hs (.clk(clk), .reset_n(rst_n), .req(req), .ack(ack));
```

> **Design intent.** A library turns recurring design intent into a vocabulary. "No
> overflow," "single-bit gray change," "request answered within N" are intents that
> appear in block after block; a checker library names each once, verified and
> parameterized, so a designer instantiates intent rather than re-deriving the SVA.
> Reuse here is not just convenience — a library check is battle-tested, which makes
> it more trustworthy than a fresh hand-written property.

## Packaging your own assertions

Project-specific intent deserves the same treatment. Collect the checks a team writes
repeatedly into checkers, parameterize the variable parts, and place them in a shared
package or file. The discipline mirrors any reusable code:

- One checker per coherent unit of intent (a protocol, a structure type).
- Parameterize widths, depths, and latency bounds rather than hardcoding them.
- Pair each assertion with the cover that proves its antecedent (Chapter 13), so a
  reused check carries its own vacuity guard.
- Bind, never hand-instantiate, so the RTL stays clean.

A house library of bound checkers means a new block inherits the team's accumulated
verification intent by instantiation, with the corner cases already encoded.

## Common pitfalls

- **Reinventing standard checks.** Overflow, one-hot, and handshake checkers already
  exist in OVL and the SVA library. Prefer the verified component.
- **Hardcoding parameters in a checker.** A checker with a fixed width or bound is
  not reusable. Parameterize the variable parts.
- **Hand-instantiating a checker in the RTL.** That edits the design source; bind the
  checker instead.
- **Shipping a checker without its covers.** A reused assertion can pass vacuously at
  a new site. Include the antecedent cover so the check guards its own vacuity.
- **Using a module where a checker fits.** A `checker` is the language's purpose-built
  container and permits verification modeling a module may restrict. Prefer it for
  bundled checks.

## Summary

- A `checker` is a reusable container for assertions, covers, and supporting modeling,
  with ports and parameters, instantiated or bound like a module.
- Bind a checker to attach a bundle of related checks to a design without editing it,
  forwarding signals and parameters per site.
- Pick the smallest fit: a named property for one rule, a checker for a related set, a
  full module only when you need module-level features.
- OVL and the Accellera SVA checker library provide verified, parameterized checks for
  the common intents; prefer them over hand-rolled equivalents.
- Package project-specific intent into bound, parameterized checkers that carry their
  own antecedent covers.

---

[← Formal Verification Primer](14-formal-verification-primer.md) · [Table of contents](../README.md) · [Next: Debugging and Anti-Patterns →](16-debugging-and-antipatterns.md)
