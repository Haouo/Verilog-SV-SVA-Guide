# Part I · 2. Data Types and Values

[← Modules and Hierarchy](01-modules-and-hierarchy.md) · [Table of contents](../README.md) · [Next: Operators and Expressions →](03-operators-and-expressions.md)

## Learning objectives

- Distinguish nets from variables and know when to use each.
- Write vectors, literals, and constants correctly.
- Understand the four-state value system and what `x` and `z` mean.
- Use `parameter` and `localparam` for sized, named constants.

## Designer's mental model

Types and values in Verilog are mostly about what kind of object can drive or
store a bit pattern. A `wire` is a connection resolved from drivers; a `reg` is a
procedural variable that holds its last assigned value. Neither word by itself
means "a physical wire" or "a flip-flop" in every context, so always connect the
type back to how the object is assigned.

The second mental model is width. Hardware does not have abstract integers; it
has a fixed number of bits. Every literal, vector, concatenation, and extension
rule is a way of deciding how many bits exist and what happens to `x` and `z`.
Most surprising Verilog bugs are not caused by exotic syntax, but by a value
being one bit wider, narrower, signed, or unknown when the designer assumed
otherwise.

## Nets versus variables

Verilog has two families of data objects, and the split confuses newcomers
because it does not match software intuition.

- A **net** (the common type is `wire`) models a physical connection. It does not
  store a value; it reflects whatever drives it. A net must be driven
  continuously — by a module output, a primitive, or an `assign`.
- A **variable** (the type is `reg` in Verilog) holds its value until a procedural
  statement assigns a new one. Despite the name, a `reg` is *not* necessarily a
  hardware register. It is just a variable assigned inside an `always` or
  `initial` block.

The rule for synthesizable RTL:

- Drive a signal with `assign` or a module port → declare it `wire`.
- Assign a signal inside an `always` block → declare it `reg`.

```verilog
wire       enable;       // driven by assign or a port
wire [7:0] data_bus;     // an 8-bit net
reg  [7:0] count;        // assigned inside an always block
```

> In SystemVerilog this distinction is relaxed by the `logic` type, covered in
> Part II. In plain Verilog you must choose `wire` or `reg` correctly.

## Vectors and bit ordering

A vector is a multi-bit signal, written `[msb:lsb]`. By near-universal
convention the least significant bit is 0:

```verilog
wire [7:0] byte_a;       // bit 7 is MSB, bit 0 is LSB
wire [0:7] reversed;     // legal but unconventional; avoid
```

Select a single bit with `byte_a[3]`, and a range with `byte_a[3:0]`. A part
select must keep the same direction as the declaration.

## The four-state value system

Verilog signals carry one of four values per bit:

| Value | Meaning |
|---|---|
| `0` | logic zero |
| `1` | logic one |
| `x` | unknown |
| `z` | high impedance (undriven) |

`x` and `z` are essential for hardware modeling, not error markers by themselves.

- `z` means nothing drives the net — a tri-state bus, or a floating input.
- `x` means the value is unknown — an uninitialized register, a multi-driver
  conflict, or the result of reading something undefined.

In simulation, an `x` often signals a real bug: a register that was never reset,
or a race. Treat unexpected `x` as a problem to trace, not to mask. Assertions
(Part III) are an effective way to catch `x` where it must not occur.

## Literals

A sized literal is written `width'base value`:

```verilog
8'hFF        // 8 bits, hexadecimal, value 255
4'b1010      // 4 bits, binary
8'd200       // 8 bits, decimal
8'b0000_00xx // underscores for readability; low bits unknown
'0, '1       // fill all bits with 0 or 1 (SystemVerilog)
```

The base is `b`, `o`, `d`, or `h`. Underscores are ignored and improve
readability. An unsized literal like `42` defaults to a 32-bit integer; prefer
sized literals in RTL so widths are explicit.

## Constants: parameter and localparam

Use named constants instead of magic numbers.

- `parameter` — a constant that a parent can override at instantiation
  (see Chapter 1).
- `localparam` — a constant that cannot be overridden. Use it for values derived
  from parameters, or for fixed internal constants such as state encodings.

```verilog
module fifo #(
    parameter DEPTH = 16
) (/* ports */);
    localparam ADDR_W = $clog2(DEPTH);  // derived, not overridable
    reg [ADDR_W-1:0] rd_ptr, wr_ptr;
endmodule
```

Deriving `ADDR_W` with `localparam` keeps the address width consistent with
`DEPTH` automatically. If someone changes `DEPTH`, the pointers resize with it.

> **Design intent.** A width is a statement of range: "this value never needs
> more than `ADDR_W` bits." Naming it with `localparam` records that intent and
> keeps every dependent signal in agreement. Magic numbers scatter the same
> decision across the file, where the copies drift apart.

## Common pitfalls

- **Wrong net/variable choice.** Assigning a `wire` inside `always`, or an
  `assign` to a `reg`, is an error. Match the type to how the signal is driven.
- **Treating `reg` as a hardware register.** It is a variable; whether it becomes
  a flip-flop depends on *how* you assign it (Chapter 5), not on the keyword.
- **Unsized literals in RTL.** They default to 32 bits and can cause surprising
  widths in expressions. Use sized literals.
- **Ignoring `x`.** An unexpected `x` is usually a missing reset or a race, not a
  cosmetic issue. Trace it.

## Summary

- Nets (`wire`) carry driven values; variables (`reg`) hold assigned values.
- Vectors use `[msb:lsb]` with LSB 0 by convention.
- The four states `0 1 x z` model real hardware; unexpected `x` means trouble.
- Write sized literals, and name constants with `parameter` / `localparam`.

---

[← Modules and Hierarchy](01-modules-and-hierarchy.md) · [Table of contents](../README.md) · [Next: Operators and Expressions →](03-operators-and-expressions.md)
