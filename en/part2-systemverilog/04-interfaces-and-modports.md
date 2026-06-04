# Part II · 4. Interfaces and Modports

[← Packages and Scope](03-packages-and-scope.md) · [Table of contents](../README.md) · [Next: Procedural Constructs and Operators →](05-procedural-and-operators.md)

## Learning objectives

- Declare an `interface` to bundle related signals under one name.
- Use `modport` to assign port directions for each role that connects to the
  interface.
- Instantiate and connect modules through an interface.
- Understand the design benefits of interfaces independent of verification use.

## Designer's mental model

An interface is a protocol bundle, not just a shortcut for many ports. It gives a
name to signals that are meant to travel together and can place protocol-specific
helpers or assertions near those signals. A `modport` then states which role a
module plays in that protocol.

Use interfaces when the bundle has meaning beyond convenience: ready/valid,
request/grant, address/data/control, or another recurring relationship. If the
signals are unrelated, an interface can hide clarity. If they form a protocol,
the interface makes that protocol visible at the module boundary.

## The problem interfaces solve

A typical bus or handshake protocol involves several signals that always travel
together: data, address, valid, ready, write-enable, byte-enable, and so on.
In plain Verilog, each signal is a separate port on every module that participates
in the protocol. Connecting two modules means wiring each signal individually.
Adding a signal to the protocol means editing every module and every instantiation
— a tedious and error-prone process.

SystemVerilog interfaces collect those signals into a named bundle. The bundle is
declared once, connected once, and extended in one place.

## Declaring an interface

```systemverilog
interface simple_bus #(
    parameter int DATA_W = 32,
    parameter int ADDR_W = 16
);
    logic [DATA_W-1:0] data;
    logic [ADDR_W-1:0] addr;
    logic              valid;
    logic              ready;
    logic              write;

endinterface
```

An interface looks like a module but contains only signal declarations (and
optionally modports, functions, and tasks). It has parameters like a module.
It is not a module — it has no ports and it cannot be synthesized on its own.

## `modport` — directions per role

An interface by itself has no direction information. The same `data` signal is
driven by the master and read by the slave. `modport` attaches a name and a
direction set for each logical role:

```systemverilog
interface simple_bus #(
    parameter int DATA_W = 32,
    parameter int ADDR_W = 16
);
    logic [DATA_W-1:0] data;
    logic [ADDR_W-1:0] addr;
    logic              valid;
    logic              ready;
    logic              write;

    modport master (
        output data, addr, valid, write,
        input  ready
    );

    modport slave (
        input  data, addr, valid, write,
        output ready
    );

endinterface
```

Now `master` and `slave` each name a subset and direction of the interface
signals. A module declares which modport it uses.

## Using an interface as a port

A module declares an interface port by naming the interface type and the modport:

```systemverilog
module bus_master (
    input  logic      clk,
    input  logic      rst_n,
    simple_bus.master bus      // interface type, modport
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bus.valid <= 1'b0;
            bus.write <= 1'b0;
        end else begin
            bus.valid <= 1'b1;
            bus.addr  <= next_addr;
            bus.data  <= next_data;
            bus.write <= do_write;
        end
    end

    logic [15:0] next_addr;
    logic [31:0] next_data;
    logic        do_write;
    // ... internal logic not shown
endmodule
```

```systemverilog
module bus_slave (
    input  logic     clk,
    input  logic     rst_n,
    simple_bus.slave bus
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            bus.ready <= 1'b0;
        else
            bus.ready <= 1'b1;   // simplified accept-all
    end
    // ... memory access not shown
endmodule
```

Both modules refer to the fields by name (`bus.valid`, `bus.data`, etc.). There
is no list of individual wires to manage.

## Instantiation and connection

At the top level, instantiate the interface once, then pass it to each module:

```systemverilog
module top;
    logic clk, rst_n;

    // One interface instance
    simple_bus #(.DATA_W(32), .ADDR_W(16)) bus_if ();

    bus_master u_master (
        .clk   (clk),
        .rst_n (rst_n),
        .bus   (bus_if)   // interface port
    );

    bus_slave u_slave (
        .clk   (clk),
        .rst_n (rst_n),
        .bus   (bus_if)
    );

    // ... clock generation not shown
endmodule
```

The interface is a single connection point. Adding a signal to `simple_bus` means
editing the interface declaration and the one or two modules that use the new
signal — not every port list and every instantiation.

## Arrays of interfaces

An array of interfaces is useful for multi-channel or multi-port designs:

```systemverilog
simple_bus #(.DATA_W(32), .ADDR_W(16)) port_if [4] ();  // 4 instances

// Connect to an array of masters
for (genvar i = 0; i < 4; i++) begin : gen_masters
    bus_master u_master (
        .clk  (clk),
        .rst_n(rst_n),
        .bus  (port_if[i])
    );
end
```

Synthesis tool support for interface arrays varies; check your tool's
documentation before using them in production RTL.

## Interfaces and testbenches

Interfaces are heavily used in verification, where a testbench driver and a
monitor both connect to the same interface. That use is out of scope for this
guide (see Appendix D). The point here is that interfaces provide clean, typed
connectivity that benefits the design itself: reduced port list size, type-checked
connections, and a single point of protocol definition.

> **Design intent.** An interface is a protocol stated in code. When you look at
> a module's port list and see `simple_bus.master bus`, you know at a glance that
> this module is the initiator of the simple_bus protocol. The modport enforces
> the direction contract so that a synthesis or lint tool can flag an accidental
> driver/receiver mismatch.

## Interfaces with parameters

Interface parameters work exactly like module parameters and allow the same
interface to serve multiple bus widths:

```systemverilog
simple_bus #(.DATA_W(64), .ADDR_W(32)) wide_bus ();
simple_bus #(.DATA_W(8),  .ADDR_W(8))  narrow_bus ();
```

Each instance has its own independently sized field widths. The modport directions
remain the same; only the widths change.

## Common pitfalls

- **Missing `modport` on a port declaration.** Without a modport, a module accepts
  the whole interface with no direction checking. Any signal can be driven from
  either side, and tools cannot verify correctness. Always specify the modport.
- **Driving an `input` modport signal.** If `bus.data` is declared `input` in the
  modport, assigning to it is a modport violation. Lint tools report this; some
  simulators only warn at elaboration. Treat modport violations as errors.
- **Instantiating the interface without `()`.**  `simple_bus bus_if;` is a
  declaration of type `simple_bus`, but it does not create an instance with actual
  storage. Write `simple_bus bus_if ();` to instantiate.
- **Putting logic in an interface for synthesis.** Interfaces can contain
  `function` and `task` definitions, but synthesizable logic should live in
  modules. Keep interfaces as pure connectivity descriptors.
- **Tool support gaps.** Not all synthesis tools support every interface feature
  equally. Parameterized interfaces and interface arrays may need workarounds.
  Verify tool support early.

## Summary

- An `interface` bundles related signals under one name and one declaration.
- `modport` assigns a name and port directions for each logical role; use it
  on every interface port.
- Modules connect to interfaces through a single port, reducing port list size
  and making protocol changes a one-place edit.
- Interfaces serve design connectivity first; verification benefits are a bonus.

---

[← Packages and Scope](03-packages-and-scope.md) · [Table of contents](../README.md) · [Next: Procedural Constructs and Operators →](05-procedural-and-operators.md)
