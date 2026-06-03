# Part III · 9. Binding and Placement

[← Clocking and Reset](08-clocking-and-reset.md) · [Table of contents](../README.md) · [Next: RTL Assertion Patterns →](10-rtl-assertion-patterns.md)

## Learning objectives

- Decide where assertions live: inline in the RTL versus a separate module.
- Use `bind` to attach assertions to a design without editing it.
- Bind to a module type or to a specific instance.
- Pass design signals into a bound checker through its ports.
- Choose a placement style that fits both design and verification ownership.

## Where assertions go

A concurrent assertion can sit almost anywhere a continuous statement can: in the
design module itself, in a separate module, in an `interface`, or in a `checker`.
The choice is mostly about ownership and intrusion.

- **Inline** assertions live next to the RTL they check. They are easy to read in
  context and travel with the code, but they add lines to the design file and
  require edit access to it.
- **Separate** assertions live in their own module, kept apart from the RTL and
  connected to it later. The design file stays untouched, which matters when the
  RTL is shared, generated, or owned by another team.

Both compile and run identically. The question is whether the check belongs *in*
the design source or *beside* it.

## Inline assertions

When the designer owns the RTL and the check expresses that designer's own intent,
inline is the simplest placement. The assertion reads as part of the module's
contract:

```systemverilog
module fifo_ctrl (input logic clk, rst_n, wr_en, rd_en, full, empty /* ... */);

    default clocking cb @(posedge clk); endclocking
    default disable iff (!rst_n);

    // Intent stated right where the signals are declared
    assert property (wr_en |-> !full);
    assert property (rd_en |-> !empty);

    // ... rest of the controller ...
endmodule
```

Keeping the assertion beside the logic it constrains makes the intent obvious to
the next reader and keeps check and code in sync through every edit.

## Separate assertion modules

When the assertions are written by a verification engineer, or the RTL must not be
touched, collect them in their own module. That module declares the same signals as
ports and contains nothing but the checks:

```systemverilog
// A pure-assertion module: no logic, only checks
module fifo_assertions (
    input logic clk, rst_n,
    input logic wr_en, rd_en, full, empty
);
    default clocking cb @(posedge clk); endclocking
    default disable iff (!rst_n);

    assert property (wr_en |-> !full);
    assert property (rd_en |-> !empty);
endmodule
```

This module must now be connected to the design. Instantiating it by hand inside
the RTL would defeat the purpose — it would edit the design file. The `bind`
construct connects it without that edit.

## bind: attaching without editing

`bind` (綁定) instantiates a module (or `checker`, or `interface`) *into* another
module from the outside. The design source is never modified; the connection is
declared separately, typically in a verification file:

```systemverilog
// Attach fifo_assertions to every instance of module fifo
bind fifo fifo_assertions u_fifo_sva (
    .clk    (clk),
    .rst_n  (rst_n),
    .wr_en  (wr_en),
    .rd_en  (rd_en),
    .full   (full),
    .empty  (empty)
);
```

Read this as: "inside module `fifo`, create an instance `u_fifo_sva` of
`fifo_assertions`, wiring its ports to these names." The names on the right are
resolved *in the scope of `fifo`*, so they reference that module's internal signals
directly — including ones that are not ports of `fifo`. This is the key power of
`bind`: an assertion module can observe a design's internal state without that
state being exposed on any boundary.

## Binding to a type or an instance

The first identifier after `bind` chooses the target. There are two forms.

### Bind by module type

Naming a module type attaches the checker to *every* instance of that module:

```systemverilog
// Every fifo in the whole design gets these assertions
bind fifo fifo_assertions u_sva (.clk(clk), .rst_n(rst_n) /* ... */);
```

This is the usual choice for a reusable block: write the checks once, and they
follow the block everywhere it is instantiated.

### Bind by instance

Naming a specific instance path attaches the checker to only that instance:

```systemverilog
// Only this one fifo instance is checked
bind dut.u_rx_fifo fifo_assertions u_sva (.clk(clk), .rst_n(rst_n) /* ... */);
```

Per-instance binding suits a check that applies to one location only — for example,
a fifo whose depth or protocol differs from its siblings, or a single instance under
focused debug.

## Passing ports and parameters

A bound module connects through ordinary ports, with all the usual rules. Two
points matter in practice.

- **Port expressions are evaluated in the target's scope.** The right-hand side of
  each connection refers to signals visible inside the bound-into module, so you can
  reach internal nets, not just the target's ports.
- **Parameters can be forwarded.** A parameterized checker can receive the target's
  own parameters so its checks scale with the instance:

```systemverilog
// Forward the design's WIDTH into the parameterized checker
bind alu #(.WIDTH(WIDTH)) alu_assertions u_sva (
    .clk (clk),
    .a   (a),
    .b   (b),
    .y   (result)
);
```

Forwarding parameters keeps one checker correct across instances of different
widths, depths, or modes, instead of forcing a separate checker per configuration.

> **Design intent.** Placement is about *whose* intent the assertion captures and
> *where* that intent can live. Inline assertions are the designer's own contract,
> stated in the RTL. A bound assertion module lets a verification engineer attach
> intent to a design they should not edit, while still reaching its internal state.
> `bind` decouples the check from the source: the design stays clean, the checks
> stay separate, and both describe the same hardware.

## Common pitfalls

- **Editing the RTL to instantiate a checker.** That reintroduces the intrusion
  `bind` exists to avoid. Declare the connection with `bind` in a separate file.
- **Binding by type when only one instance is meant.** Type binding hits every
  instance; use an instance path when the check is local to one of them.
- **Mismatched port directions or widths.** A bound module follows normal port
  rules; a width or direction mismatch is an error or a silent truncation, just as
  for any instantiation.
- **Forgetting to forward parameters.** A checker with a hardcoded width will be
  wrong on a differently sized instance. Forward the target's parameters.
- **Relying on the bind file's scope for names.** Port expressions resolve in the
  *target* module's scope, not the bind statement's; reference the design's internal
  names accordingly.

## Summary

- Assertions can be placed inline in the RTL or in a separate module; both run
  identically.
- Inline placement suits the designer's own intent; a separate module suits checks
  on RTL that must not be edited.
- `bind` instantiates an assertion module into a design from the outside, with no
  change to the design source.
- Bind by module type to cover every instance, or by instance path to cover one.
- Port expressions resolve in the target's scope, so a bound module can observe
  internal signals; forward parameters to keep a checker correct across instances.

---

[← Clocking and Reset](08-clocking-and-reset.md) · [Table of contents](../README.md) · [Next: RTL Assertion Patterns →](10-rtl-assertion-patterns.md)
