# Part I · 3. Operators and Expressions

[← Data Types and Values](02-data-types-and-values.md) · [Table of contents](../README.md) · [Next: Combinational Logic →](04-combinational-logic.md)

## Learning objectives

- Use the main operator groups correctly.
- Understand how Verilog sizes and extends operands.
- Know the difference between logical and bitwise, and between `==` and `===`.
- Avoid the common width and signedness traps.

## Operator groups

Verilog operators fall into a few groups. The ones you use most in RTL:

| Group | Operators |
|---|---|
| Arithmetic | `+ - * / %` |
| Bitwise | `~ & \| ^ ^~` |
| Reduction | `& ~& \| ~\| ^ ~^` (unary) |
| Logical | `! && \|\|` |
| Relational | `< <= > >=` |
| Equality | `== != === !==` |
| Shift | `<< >> <<< >>>` |
| Concatenation | `{ }` and replication `{N{ }}` |
| Conditional | `? :` |

### Bitwise versus logical

This trips up newcomers. A bitwise operator works bit by bit and returns a
vector; a logical operator treats its whole operand as true/false and returns a
single bit.

```verilog
4'b1100 & 4'b1010   // bitwise AND -> 4'b1000
4'b1100 && 4'b1010  // logical AND -> 1'b1 (both are nonzero, so true)
```

Use `&`/`|` to combine bits, `&&`/`||` to combine conditions.

### Reduction operators

A unary reduction operator collapses a vector to one bit by applying the
operation across all bits:

```verilog
&data   // 1 if every bit of data is 1
|data   // 1 if any bit is 1 (data is nonzero)
^data   // parity: 1 if an odd number of bits are 1
```

These are compact and synthesize well — `&data` is an all-ones check without a
literal.

## Concatenation and replication

Braces join signals; `{N{x}}` repeats `x` N times.

```verilog
{a, b}           // a in the high bits, b in the low bits
{4{1'b1}}        // 4'b1111
{byte_a[7], byte_a}  // sign-extend an 8-bit value to 9 bits
```

Concatenation is the standard tool for building and slicing buses.

## Width, extension, and the context rule

Verilog expressions have a width, and it is computed from context. This is a
frequent source of bugs. Two rules to remember:

1. In an assignment, the operands are extended (or truncated) to the width of the
   widest operand *and* the left-hand side. This is "context-determined" width.
2. Unsigned operands are zero-extended; signed operands are sign-extended.

```verilog
reg [7:0]  a;
reg [3:0]  b;
reg [7:0]  c;
c = a + b;   // b is zero-extended to 8 bits before the add
```

A common mistake is an intermediate result that overflows because the expression
width was set by a narrow operand. When in doubt, make widths explicit.

## Equality: `==` versus `===`

- `==` and `!=` are *logical* equality. If either operand has an `x` or `z` bit,
  the result is `x` (unknown), not 0 or 1.
- `===` and `!==` are *case* equality. They compare `x` and `z` bits literally
  and always return a definite 0 or 1.

```verilog
4'b1x10 == 4'b1x10   // x  (unknown, because of the x bit)
4'b1x10 === 4'b1x10  // 1  (exact match including the x)
```

Use `==` in synthesizable RTL — `===` is not synthesizable, because real hardware
has no `x`. `===` is useful in testbenches and assertions for checking against
`x`/`z`.

## Signed arithmetic

By default, nets and `reg` are unsigned. Declare `signed` when you need
two's-complement arithmetic and sign extension:

```verilog
reg signed [7:0] s;
wire signed [7:0] diff = s - 8'sd1;   // signed literal: 8'sd1
```

Mixing signed and unsigned operands follows strict rules and often surprises
people: if *any* operand is unsigned, the operation is unsigned. Keep signedness
consistent within an expression, and use the `'s` literal form when you mean a
signed constant.

> **Design intent.** An expression's width and signedness are part of the intent:
> "this adder is 8-bit unsigned," "this difference is signed." Verilog infers
> both from context, so when the inference is not obvious, state it explicitly
> with sized, signed literals and intermediate signals. The reader — and the
> synthesis tool — should not have to guess.

## Common pitfalls

- **Bitwise where you meant logical**, or the reverse. `&` is not `&&`.
- **Silent truncation.** Assigning a wide expression to a narrow target drops the
  high bits with no warning. Size intermediates deliberately.
- **`==` with `x`/`z`.** Returns `x`, which then propagates. Use `===` only in
  non-synthesizable code when you truly want to compare against `x`/`z`.
- **Accidental unsigned math.** One unsigned operand makes the whole expression
  unsigned. Watch sign extension on subtraction.

## Summary

- Know the operator groups; do not confuse bitwise with logical.
- Reduction operators collapse a vector to one bit and synthesize cleanly.
- Expression width is context-determined; truncation and extension are silent.
- Use `==` in RTL and `===` only for `x`/`z` checks in testbenches/assertions.

---

[← Data Types and Values](02-data-types-and-values.md) · [Table of contents](../README.md) · [Next: Combinational Logic →](04-combinational-logic.md)
