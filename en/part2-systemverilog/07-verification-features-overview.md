# Part II · 7. Verification Features Overview (mention only)

[← Parameterization and Generate](06-parameterization-and-generate.md) · [Table of contents](../README.md) · [Next: Why Assertions →](../part3-sva/01-why-assertions.md)

> **Scope note.** This chapter is deliberately brief. SystemVerilog's
> verification subset — classes, constrained randomization, coverage, mailboxes,
> semaphores, and UVM — is a large discipline with its own literature and is
> **not** the focus of this guide. Part II covers only the synthesizable design
> subset. The goal here is to name the major verification features so that a
> designer can recognize them when reading mixed design-and-verification code and
> know where to look for further information. For real verification methodology,
> see the references in [Appendix D](../appendices/D-references.md).

## Learning objectives

- Recognize the major SystemVerilog verification constructs by name.
- Understand that these features are simulation-only and not synthesizable.
- Know where the boundary between the design subset (this guide) and the
  verification subset lies.

## Designer's mental model

SystemVerilog contains both design features and verification features. A designer
does not need to master every class-based or UVM detail to write good RTL, but
should be able to recognize when code has moved out of the synthesizable design
subset. That recognition prevents accidental dependence on testbench-only
constructs.

This chapter is a map, not a methodology course. Its purpose is to show where
classes, constrained randomization, functional coverage, and UVM sit relative to
RTL and assertions. SVA is the bridge a designer uses most directly: it stays
close to the design while still giving verification tools something precise to
check.

## The two faces of SystemVerilog

IEEE 1800 is a single standard that serves two communities. The **design subset**
(Parts I and II of this guide) targets synthesizable RTL: modules, always blocks,
interfaces, packages, and the type system. The **verification subset** extends
the language with object-oriented programming, randomization, and coverage — none
of which synthesizes to hardware.

A file can mix both subsets. Synthesis tools accept only the design subset; they
reject or ignore verification constructs. Simulators accept both. When reading
a SystemVerilog codebase, you will encounter both halves.

## Object-oriented programming: classes

SystemVerilog adds a `class` construct with inheritance, polymorphism, and virtual
methods. Classes are used in verification to model transactions, sequences, and
environments. A class instance is allocated with `new` and lives on the heap.

None of this is synthesizable. If you see `class`, `extends`, `virtual function`,
or `new` in a file, that file is verification code.

```systemverilog
// Verification only — not synthesizable
class bus_transaction;
    rand logic [31:0] addr;
    rand logic [31:0] data;
    rand logic        write;

    function new();
        addr  = '0;
        data  = '0;
        write = 1'b0;
    endfunction
endclass
```

## Constrained randomization

The `rand` and `randc` modifiers on class fields mark them as randomly generated.
`constraint` blocks express relationships and limits on those values. The
`randomize()` method generates a legal set of values satisfying all constraints.

```systemverilog
// Verification only
class aligned_transaction extends bus_transaction;
    constraint c_aligned {
        addr[1:0] == 2'b00;   // word-aligned addresses only
        data inside {[0:255]}; // small data values
    }
endclass
```

Constrained randomization is the foundation of modern verification methodology.
It is entirely simulation-only.

## Interprocess communication: mailboxes and semaphores

`mailbox` is a parameterized FIFO used to pass objects between concurrent
simulation threads (`fork / join`). `semaphore` provides mutual exclusion.
Both are simulation constructs.

```systemverilog
// Verification only
mailbox #(bus_transaction) gen2drv;   // generator to driver channel
semaphore bus_lock;                   // prevent concurrent bus access
```

These have no synthesis equivalent. Hardware synchronization uses clocked logic
and handshake protocols — the topics of Parts I and II.

## Functional coverage

`covergroup` and `coverpoint` measure which values and value combinations a
simulation has exercised. Coverage reports drive the verification process: when
coverage reaches 100%, the plan is complete.

```systemverilog
// Verification only
covergroup bus_cg @(posedge clk);
    cp_cmd: coverpoint bus.cmd {
        bins read  = {READ};
        bins write = {WRITE};
    }
    cp_len: coverpoint bus.len { bins short = {[1:4]}; bins long = {[5:16]}; }
    cx_cmd_len: cross cp_cmd, cp_len;
endgroup
```

Functional coverage complements code coverage and assertion coverage. None of
it affects synthesis.

## Universal Verification Methodology (UVM)

UVM is a library built on top of SystemVerilog's class system. It standardizes
the structure of a verification environment: agents, drivers, monitors,
scoreboards, and sequences. Most industrial verification is done in UVM.

UVM is out of scope for this guide. It is an extensive topic; dedicated books and
courses exist for it. The reference list in Appendix D points to the standard
starting materials.

## Assertions as a bridge

SystemVerilog Assertions (SVA) occupy a middle ground: they are written in
verification style but many can be synthesized or consumed by formal tools. They
are the subject of Part III of this guide. SVA is the one verification-adjacent
feature that every RTL designer should know.

> **Design intent.** Knowing that verification features exist — and recognizing
> them in code — helps a designer understand the full SystemVerilog ecosystem
> without being overwhelmed by it. The design subset in Parts I and II is already
> sufficient to describe any synthesizable RTL. Part III adds the assertion layer
> that connects design intent to automated checking.

## Common pitfalls

- **Using `class` or `rand` in synthesizable design files.** Synthesis tools will
  reject these constructs. Keep verification code in separate files or directories,
  and keep design files free of class definitions and random modifiers.
- **Confusing `mailbox` with a hardware FIFO.** A `mailbox` is a simulation
  object. A hardware FIFO is a module with clocked push and pop logic, as shown in
  Chapter 6.
- **Treating coverage as part of synthesis.** Coverage directives are simulation
  instrumentation. They add no logic to the synthesized design.

## Summary

- SystemVerilog has a design subset (synthesizable) and a verification subset
  (simulation-only); this guide covers the design subset.
- Classes, constrained randomization, mailboxes, semaphores, and covergroups are
  verification constructs; none synthesize to hardware.
- UVM is the standard verification methodology built on the SV class system; it
  is a separate discipline.
- SVA (Part III) is the bridge: assertion language usable in both design and
  formal verification contexts.
- For verification, see the references in [Appendix D](../appendices/D-references.md).

---

[← Parameterization and Generate](06-parameterization-and-generate.md) · [Table of contents](../README.md) · [Next: Why Assertions →](../part3-sva/01-why-assertions.md)
