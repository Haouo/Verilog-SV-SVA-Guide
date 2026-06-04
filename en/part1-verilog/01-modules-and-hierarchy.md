# Part I · 1. Modules and Hierarchy

[← Introduction](../00-introduction.md) · [Table of contents](../README.md) · [Next: Data Types and Values →](02-data-types-and-values.md)

## Learning objectives

- Declare a module with a clean port list.
- Instantiate modules and connect them by name.
- Build a hierarchy and understand how it elaborates.
- Pass parameters to make a module reusable.

## Designer's mental model

A `module` is not just a text container. It is the unit at which a design names a
piece of hardware, declares what crosses its boundary, and lets elaboration build
a hierarchy of instances. When you read a module, first read its port list and
parameters as a contract before looking at the implementation below it.

Good hierarchy reduces how much context you need at once. A caller should not
need to know every internal register of a child block; it should need to know the
ports, parameter meanings, and timing expectations. That is why this chapter
spends time on naming, instantiation, and parameterization rather than only the
`module ... endmodule` syntax.

## The module is the unit of design

A `module` is the basic building block in Verilog. It has a name, a list of
ports, and a body that describes behavior or structure. Hardware is built by
instantiating modules inside other modules, forming a tree. The top module is
the root; the leaves are primitive logic.

```verilog
module adder (
    input  wire [7:0] a,
    input  wire [7:0] b,
    output wire [8:0] sum
);
    assign sum = a + b;
endmodule
```

This guide uses the **ANSI port style** shown above, where direction, type, and
width appear in the port list. The older non-ANSI style declares ports and their
directions separately in the body. Prefer ANSI style: it is shorter and keeps
each port's full description in one place.

## Ports and direction

Every port has a direction:

- `input` — driven from outside, read inside.
- `output` — driven inside, read outside.
- `inout` — bidirectional, used for buses with tri-state drivers.

For synthesizable RTL, most ports are `input` or `output`. A port's width is
written as `[msb:lsb]`, almost always `[N-1:0]`.

## Instantiation and connection

You create an instance by naming the module, giving the instance a name, and
connecting its ports. Always connect **by name**, not by position. Named
connection survives port-list changes and makes intent obvious.

```verilog
module datapath (
    input  wire [7:0] x,
    input  wire [7:0] y,
    output wire [8:0] total
);
    // Named connection: .port(signal)
    adder u_adder (
        .a   (x),
        .b   (y),
        .sum (total)
    );
endmodule
```

Positional connection — `adder u_adder (x, y, total)` — works but is fragile. One
reordered or inserted port silently miswires the design. Named connection is the
rule in production RTL.

## Hierarchy and elaboration

When a tool reads your design, it performs *elaboration*: it picks the top
module, creates its instances, then creates their instances, and so on, until the
whole tree exists. Parameters are resolved during this step, before simulation or
synthesis begins. The result is a fully expanded hierarchy of concrete modules.

A signal in one module is not visible in another except through ports. This is
deliberate. Ports are the contract between a module and its parent; keeping that
contract explicit is what makes a design composable.

## Parameters make modules reusable

A `parameter` is a compile-time constant that a parent can override at
instantiation. Use parameters for widths, depths, and other sizes so one module
serves many cases.

```verilog
module adder #(
    parameter int WIDTH = 8
) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output wire [WIDTH:0]   sum
);
    assign sum = a + b;
endmodule

// Override the width at instantiation.
adder #(.WIDTH(16)) u_adder16 (.a(a16), .b(b16), .sum(sum17));
```

Override parameters by name, just like ports. A module that hardcodes its widths
works once; a parameterized module works everywhere.

> **Design intent.** The port list is the intent of a block stated as an
> interface: these are the signals that cross the boundary, and these are their
> directions and widths. A clean, named, parameterized port list tells the next
> engineer exactly how the block is meant to connect.

## Common pitfalls

- **Positional port connection.** It miswires silently when ports change. Always
  connect by name.
- **Mixing ANSI and non-ANSI styles** in one module. Pick ANSI and stay
  consistent.
- **Wide implicit nets.** An undeclared signal becomes a 1-bit `wire`. A typo in
  a port name can create a stray 1-bit net and a hard-to-find bug. (See Chapter 2
  on declaring nets; consider \`\`default_nettype none\` to disable implicit nets.)
- **Hardcoded widths.** They block reuse. Parameterize sizes from the start.

## Summary

- A module has a name, ports, and a body; designs are trees of module instances.
- Use ANSI port style and connect instances by name.
- Elaboration expands the hierarchy and resolves parameters before run.
- Parameters turn a single module into a reusable, sized component.

---

[← Introduction](../00-introduction.md) · [Table of contents](../README.md) · [Next: Data Types and Values →](02-data-types-and-values.md)
