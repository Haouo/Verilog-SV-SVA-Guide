# Part II · 5. Procedural Constructs and Operators

[← Interfaces and Modports](04-interfaces-and-modports.md) · [Table of contents](../README.md) · [Next: Parameterization and Generate →](06-parameterization-and-generate.md)

## Learning objectives

- Use `do-while`, `foreach`, `break`, and `continue` in synthesizable contexts.
- Apply `++`, `--`, `+=`, `-=` and other shorthand assignment operators.
- Write `case inside` for wildcard pattern matching.
- Cast values correctly with the static cast `'` and with `$cast`.
- Know which constructs are synthesizable and which are simulation-only.

## Designer's mental model

SystemVerilog procedural features are useful when they reduce accidental detail.
Inline loop variables, `foreach`, casts, shorthand assignments, and `case inside`
can make the intended operation clearer than older Verilog forms. The best use is
not shorter code alone, but code whose structure matches the decision or data
movement being described.

Because these constructs are more expressive, they also deserve more deliberate
review. Ask whether a cast is documenting a real conversion or silencing a type
warning, whether a shorthand assignment is safe for the block's timing, and
whether `case inside` is expressing a real pattern or hiding don't-care behavior
that should be checked.

## Enhanced loop constructs

### `do-while`

`do-while` executes the body at least once before testing the condition.
In synthesizable code, loops must have a statically determinable bound — the
synthesis tool unrolls them. `do-while` is synthesizable when its bound is
statically known.

```systemverilog
// Synthesizable: bound is known at elaboration
int i;
always_comb begin
    i = 0;
    do begin
        result[i] = in_data[i] ^ key[i];
        i++;
    end while (i < 8);
end
```

In practice, `for` is more common in RTL because its bound is immediately visible
at the top of the construct. Use `do-while` when the first iteration must always
execute regardless of the condition.

### `foreach`

`foreach` iterates over every element of an array. It automatically handles
the index range and is the clearest way to process arrays:

```systemverilog
logic [7:0] data [16];
logic [7:0] xor_all;

always_comb begin
    xor_all = '0;
    foreach (data[i])
        xor_all ^= data[i];
end
```

`foreach` on a multi-dimensional array iterates all dimensions:

```systemverilog
logic [3:0][7:0] matrix [4];   // 4 unpacked elements, each 4×8 packed

always_comb begin
    foreach (matrix[i, j, k])
        // i: unpacked index, j: outer packed, k: inner packed
        processed[i][j][k] = matrix[i][j][k];
end
```

### `break` and `continue`

`break` exits the innermost loop immediately. `continue` skips to the next
iteration. Both are synthesizable in `for` and `foreach` loops when the loop
has a static bound, because the tool unrolls the loop and then evaluates the
condition as combinational logic.

```systemverilog
// Find first set bit — synthesizable because the loop bound is static
logic [7:0]  in;
logic [2:0]  first_bit;
logic        found;

always_comb begin
    first_bit = '0;
    found     = 1'b0;
    for (int i = 0; i < 8; i++) begin
        if (!found && in[i]) begin
            first_bit = i[2:0];
            found     = 1'b1;
        end
    end
end
```

Note: a `break` in a synthesized loop does not shorten the loop at run time; the
tool unrolls every iteration and inserts conditional logic for the early exit.
The hardware executes all iterations; it just ignores the results after the break
condition is met. This is correct behavior, but be aware that a "break" does not
save area compared to a fully unrolled loop — it just clarifies intent.

## Shorthand assignment operators

SystemVerilog adds the C-style shorthand assignments. All are synthesizable.

| Operator | Meaning |
|----------|---------|
| `a++`    | `a = a + 1` (post-increment) |
| `++a`    | `a = a + 1` (pre-increment) |
| `a--`    | `a = a - 1` (post-decrement) |
| `--a`    | `a = a - 1` (pre-decrement) |
| `a += b` | `a = a + b` |
| `a -= b` | `a = a - b` |
| `a *= b` | `a = a * b` |
| `a /= b` | `a = a / b` |
| `a &= b` | `a = a & b` |
| `a \|= b`| `a = a \| b` |
| `a ^= b` | `a = a ^ b` |
| `a <<= b`| `a = a << b` |
| `a >>= b`| `a = a >> b` |

```systemverilog
always_comb begin
    sum   = '0;
    carry = '0;
    for (int i = 0; i < 8; i++) begin
        sum += data[i];   // accumulate
    end
end
```

In clocked blocks, use `<=` for the non-blocking version: `count <= count + 1`
rather than `count++`. The `++` operator always performs a blocking update — it
has no non-blocking form — so in `always_ff` write the explicit assignment. Keep
increment notation for combinational loop variables where the blocking context
is clear.

## `case inside`

Plain `case` matches only exact values. `case inside` extends this with wildcard
patterns, using `?` for don't-care bits. This is synthesizable.

```systemverilog
logic [3:0] opcode;
logic       is_branch;

always_comb begin
    unique case (opcode) inside
        4'b0???: is_branch = 1'b0;   // opcodes 0xxx: not a branch
        4'b10??: is_branch = 1'b1;   // opcodes 10xx: branch
        4'b1100: is_branch = 1'b0;   // specific non-branch
        4'b1101: is_branch = 1'b1;   // specific branch
        default: is_branch = 1'b0;
    endcase
end
```

`case inside` also accepts ranges with `[lo:hi]` syntax:

```systemverilog
unique case (count) inside
    [0:7]:   group = 2'd0;
    [8:15]:  group = 2'd1;
    [16:23]: group = 2'd2;
    default: group = 2'd3;
endcase
```

`unique` and `priority` work with `case inside` exactly as they do with plain
`case`. Use `unique case inside` when the patterns are non-overlapping and
complete.

## Casting

### Static cast `'`

The static cast operator `'` converts a value to a target type at compile time.
It is the primary casting mechanism in synthesizable code.

```systemverilog
typedef enum logic [1:0] {IDLE=2'd0, RUN=2'd1, DONE=2'd2} state_t;
state_t state;
logic [1:0] raw;

// Cast a logic value to an enum type
state = state_t'(raw);

// Cast a wider value to a narrower type (truncation)
logic [7:0]  byte_val;
logic [3:0]  nibble;
nibble = 4'(byte_val);        // static width cast, takes low 4 bits

// Sign extension
logic signed [15:0] s16;
logic        [7:0]  u8;
s16 = 16'(signed'(u8));      // sign-extend 8-bit unsigned to 16-bit signed
```

Static casts are evaluated at elaboration time when applied to constants, or at
the point of assignment for run-time values. Synthesis maps them to wiring
(truncation, extension, reinterpretation — no logic gates).

### `$cast`

`$cast` is a dynamic cast used primarily in simulation and verification. For
enum types, it assigns the source to the target and returns 1 if the value is
a legal enum member, 0 otherwise.

```systemverilog
state_t next;
logic [1:0] encoded;
bit ok;

// ok == 0 if encoded is not a valid state_t member
ok = $cast(next, encoded);
```

`$cast` is not synthesizable. In design code, use the static cast `state_t'(v)`
and rely on `unique case` plus assertions to detect illegal values. Reserve
`$cast` for testbenches.

## Signed arithmetic

SystemVerilog operands are unsigned by default. Use `signed` keyword or the
`$signed` / `$unsigned` system functions to control sign extension in arithmetic:

```systemverilog
logic [7:0]  a, b;
logic [8:0]  sum_u;  // unsigned
logic signed [8:0] sum_s; // signed

sum_u = {1'b0, a} + {1'b0, b};           // unsigned addition
sum_s = $signed({1'b0, a}) + $signed({1'b0, b}); // treat as signed
```

In synthesis, signed and unsigned arithmetic map to the same adder; only the
interpretation of the carry/overflow bit differs. Mismatched signedness in
expressions is a common source of subtle bugs — be explicit.

> **Design intent.** `case inside` with wildcard patterns documents that certain
> bits are genuinely irrelevant to the decision — a hardware encoding decision,
> not a simulation convenience. The `unique` modifier checks that the remaining
> bits are fully determined. Together they express a precise, tool-verifiable
> specification of a decoder.

## Common pitfalls

- **Using `break` expecting it to save power or area.** In synthesis, loop
  unrolling means all iterations execute as combinational logic. `break` does not
  short-circuit hardware. It clarifies intent and may help synthesis recognize
  the intended structure, but do not rely on it for area reduction.
- **Applying `++` in a clocked block.** Use `count <= count + 1` in `always_ff`,
  not `count++` on the left side. The non-blocking assignment is the explicit
  and portable form.
- **Using `$cast` in synthesizable RTL.** It is simulation-only. Use the static
  cast `type'(value)` in design code.
- **Overlapping patterns in `case inside` with `unique`.** If two patterns can
  match the same input, `unique` is violated and the simulator will warn. Check
  all patterns for overlap before declaring `unique`.
- **Neglecting signedness in comparisons.** Comparing `logic signed [7:0] a` with
  `logic [7:0] b` (unsigned) applies unsigned comparison rules. Both operands
  must be the same sign type for correct signed comparison.

## Summary

- `do-while` and `foreach` extend loop expressiveness; both synthesize when the
  bound is static.
- `break` and `continue` are synthesizable in static-bound loops; they become
  conditional logic, not short-circuit hardware.
- Shorthand operators (`++`, `+=`, etc.) are synthesizable and improve readability;
  use `<=` form in clocked blocks.
- `case inside` adds wildcard (`?`) and range (`[lo:hi]`) patterns; combine with
  `unique` for complete, non-overlapping decoders.
- Use static cast `type'(v)` in synthesizable code; reserve `$cast` for
  testbenches.

---

[← Interfaces and Modports](04-interfaces-and-modports.md) · [Table of contents](../README.md) · [Next: Parameterization and Generate →](06-parameterization-and-generate.md)
