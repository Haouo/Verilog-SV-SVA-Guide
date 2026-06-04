# Part II · 2. Enhanced Data Types

[← Why SystemVerilog for Design](01-why-sv-for-design.md) · [Table of contents](../README.md) · [Next: Packages and Scope →](03-packages-and-scope.md)

## Learning objectives

- Define named types with `typedef` to make code self-documenting.
- Use `enum` for FSM states and other named-constant sets.
- Group related signals into `struct` and `packed struct`.
- Understand the difference between packed and unpacked arrays.
- Know when 2-state types (`bit`, `int`) are safe and when 4-state (`logic`) is
  required in synthesizable design.

## Designer's mental model

SystemVerilog types let you name design concepts instead of only bit ranges. An
`enum` says these encodings are states or commands; a `struct` says these fields
travel together; a `typedef` lets that meaning be reused without rewriting the
shape every time. Types become lightweight documentation that tools can also
check.

The tradeoff is that the designer must still remember the hardware underneath.
A packed struct is bits in a fixed layout, an unpacked array is a collection of
elements, and a 2-state type can hide `x` information. Use stronger types to
state intent, but always ask what bits will be synthesized or simulated.

## `typedef` — naming a type

`typedef` gives a name to any type expression. This is the same idea as in C,
and it serves the same purpose: replacing a structural description with a
meaningful name.

```systemverilog
typedef logic [7:0]  byte_t;
typedef logic [31:0] word_t;
typedef logic [15:0] addr_t;

module alu (
    input  word_t a,
    input  word_t b,
    output word_t result
);
```

The suffix `_t` is a common convention for type aliases; it is not required by
the language. Using named types makes port lists and signal declarations shorter
and easier to read, and it makes width changes a one-place edit.

## `enum` — named symbolic values

An `enum` defines a type whose values are drawn from a named set. It is
the right tool for FSM state variables, opcode fields, and any other signal
where the meaning of a value should be apparent from its name.

```systemverilog
typedef enum logic [1:0] {
    IDLE    = 2'b00,
    FETCH   = 2'b01,
    DECODE  = 2'b10,
    EXECUTE = 2'b11
} state_t;

state_t state, next_state;
```

The base type (`logic [1:0]` here) sets the encoding and bit width. If you omit
an explicit encoding, the tool assigns sequential integer values starting from 0.
Explicit encodings give you control over the bit pattern, which matters when
synthesis optimizes for a particular encoding or when the state register is
observed in waveforms.

### Enum in a case statement

Enums pair naturally with `unique case`:

```systemverilog
always_comb begin
    unique case (state)
        IDLE:    next_state = FETCH;
        FETCH:   next_state = DECODE;
        DECODE:  next_state = EXECUTE;
        EXECUTE: next_state = IDLE;
    endcase
end
```

The case expression uses the symbolic names. The tool checks that every enum
member is covered (or that a `default` is present). This makes FSM transitions
readable and verifiable.

### `enum` methods

SystemVerilog provides built-in methods on enum variables for use in simulation
and testbenches. In synthesizable code, keep enum operations to assignment and
comparison; the methods (`first()`, `last()`, `next()`, `prev()`, `name()`) are
not reliably synthesizable and belong in verification code.

## `struct` — grouping related signals

A `struct` groups multiple fields under one name. Use it when several signals
belong together conceptually — for example, the fields of a bus transaction or
the control word of a pipeline stage.

```systemverilog
typedef struct {
    logic [31:0] data;
    logic [3:0]  byte_en;
    logic        valid;
    logic        write;
} bus_req_t;

bus_req_t req;

// Field access
assign req.valid = 1'b1;
assign req.data  = payload;
```

Struct fields are accessed with dot notation. A struct can be passed as a single
port, assigned as a whole, or compared field by field.

### `packed struct`

A `packed struct` stores its fields as a contiguous bit vector. The fields are
ordered from the most-significant bit down, in declaration order. This lets the
struct be treated as both a named collection of fields and as a plain bit vector.

```systemverilog
typedef struct packed {
    logic [7:0]  opcode;   // bits [15:8]
    logic [7:0]  operand;  // bits [7:0]
} instr_t;

instr_t instr;
logic [15:0] raw;

// Both are valid:
assign instr.opcode = 8'hAB;
assign raw = instr;          // treat as 16-bit vector
```

Packed structs are the standard choice for synthesizable design because the bit
layout is deterministic and matches how hardware sees the signal. Unpacked structs
may have implementation-defined padding and are less predictable in synthesis.

### `union` and `packed union`

A `union` allows different interpretations of the same bits. A `packed union`
makes this a contiguous bit field, which is synthesizable.

```systemverilog
typedef union packed {
    logic [31:0]  raw;
    struct packed {
        logic [15:0] high;
        logic [15:0] low;
    } halves;
} word_u;

word_u w;
assign w.raw = 32'hDEADBEEF;
// w.halves.high == 16'hDEAD, w.halves.low == 16'hBEEF
```

Unions are useful for defining alternative views of a register or protocol field.
Keep union members all the same width; mismatched widths in a packed union require
explicit truncation or extension.

## Packed vs unpacked arrays

SystemVerilog distinguishes two array dimensions:

- **Packed dimensions** appear between the type keyword and the signal name. They
  form a contiguous bit vector. Indexing or slicing them yields logic bits.
- **Unpacked dimensions** appear after the signal name. They are an array of the
  declared type; the elements may not be contiguous in memory or hardware.

```systemverilog
// Packed: 4 × 8-bit vector = one 32-bit signal
logic [3:0][7:0] packed_array;   // [31:0] as a flat bit vector

// Unpacked: 4 separate 8-bit signals
logic [7:0] unpacked_array [4];

// Mixed: 4 elements, each a 32-bit vector
logic [31:0] mixed_array [8];    // 8 unpacked, each 32 packed bits
```

For synthesizable design, prefer packed dimensions when the whole structure
represents one hardware word. Use unpacked arrays for memories, register files,
and lookup tables where individual elements are accessed by index.

```systemverilog
// Synthesizable register file: 16 entries, 32 bits wide
logic [31:0] regfile [16];

always_ff @(posedge clk) begin
    if (we)
        regfile[waddr] <= wdata;
end

assign rdata = regfile[raddr];
```

## 2-state vs 4-state types

Verilog and SystemVerilog have two families of types:

| Family | Values | Examples |
|--------|--------|---------|
| 4-state | 0, 1, X, Z | `logic`, `reg`, `wire` |
| 2-state | 0, 1 only | `bit`, `byte`, `shortint`, `int`, `longint` |

### `bit` and `int`

`bit` is a 1-bit 2-state type. `int` is a 32-bit signed 2-state type (equivalent
to `integer` in Verilog but 2-state). `byte`, `shortint`, `longint` are 8-, 16-,
and 64-bit signed 2-state integers.

```systemverilog
bit        flag;       // 1-bit, 2-state
int        counter;    // 32-bit signed, 2-state
bit [7:0]  mask;       // 8-bit, 2-state
```

### When 2-state types are safe in design

2-state types are appropriate when:

- The signal is a loop variable, counter, or arithmetic quantity that will never
  legitimately hold X or Z.
- You are computing a parameter or localparam value at elaboration time.
- The signal is inside a testbench (where simulation-only arithmetic is common).

Use 4-state `logic` for all RTL ports and internal signals that are driven by
hardware. The reason: if a `logic` signal is unconnected or uninitialized, the
simulator propagates X, alerting you to the problem. A `bit` signal silently
initializes to 0, hiding the uninitialized state. In RTL, hiding X is dangerous.

```systemverilog
// GOOD: logic for hardware signals — X propagation catches mistakes
logic [7:0] data_in;
logic [7:0] result;

// OK: bit or int for synthesis-time constants and loop variables
localparam int DEPTH = 256;

// Generate loops use genvar — an elaboration-time index, not int/bit
for (genvar i = 0; i < DEPTH; i++) begin : gen_cells
    // ...
end
```

> **Design intent.** Choosing `logic` for hardware signals and `int`/`bit` for
> counters and parameters communicates which signals are part of the hardware
> fabric and which are elaboration-time quantities. The type choice is a form of
> documentation that tools can check.

## Common pitfalls

- **Using an unpacked struct for hardware ports.** Synthesis tools may not support
  unpacked struct ports. Use `packed struct` or `typedef` a packed struct for
  port types.
- **Omitting the base type in an enum.** The default base type is `int` (2-state,
  32 bits), which is usually wider than needed and may cause tool warnings. Always
  declare the base type explicitly.
- **Assigning an integer literal to an enum variable.** In SystemVerilog, this
  requires an explicit cast: `state = state_t'(2'b01)`. Assigning a raw literal
  directly is a type mismatch. Some tools accept it with a warning; rely on the
  cast for portability.
- **Using 2-state `bit` for module ports.** If a parent module drives a port with
  X (uninitialized), a `bit` port silently converts to 0. Use `logic` at module
  boundaries.
- **Packed array bit ordering.** In a packed array `[3:0][7:0]`, element `[3]`
  occupies the most-significant bits. Confirm ordering against your protocol
  specification before assigning the flat bit vector.

## Summary

- `typedef` names type expressions; use it to make port lists and declarations
  readable and maintainable.
- `enum` gives symbolic names to a set of values; it is ideal for FSM states and
  is checked by `unique case`.
- `packed struct` groups fields into a contiguous bit vector suitable for
  synthesis; prefer it over unpacked struct for hardware signals.
- `packed union` gives alternative views of the same bits — useful for registers
  with multiple interpretations.
- Use 4-state `logic` for hardware signals; reserve 2-state `int`/`bit` for
  elaboration-time constants and loop indices.

---

[← Why SystemVerilog for Design](01-why-sv-for-design.md) · [Table of contents](../README.md) · [Next: Packages and Scope →](03-packages-and-scope.md)
