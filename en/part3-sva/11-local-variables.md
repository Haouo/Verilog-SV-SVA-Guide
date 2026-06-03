# Part III · 11. Local Variables

[← RTL Assertion Patterns](10-rtl-assertion-patterns.md) · [Table of contents](../README.md) · [Next: Recursive Properties →](12-recursive-properties.md)

## Learning objectives

- Declare a **local variable** (區域變數) inside a sequence or property.
- Assign to it during a sequence match and read it later.
- Use a local variable to check pipelined data across cycles.
- Understand per-attempt scoping and the flow of local-variable values.
- Avoid the sampling and flow pitfalls that make local variables surprising.

## Why local variables exist

Implication relates a trigger to a response, but often the response must be checked
*against a value captured at the trigger.* A read returns the data that was written;
a response carries the tag of its request. A plain boolean property cannot remember
the captured value across cycles. A **local variable** can: it is storage private to
one evaluation attempt of an assertion, written when a sequence element matches and
read in a later element.

```systemverilog
// Capture the address at request, check the response uses the same one
property addr_matches;
    logic [7:0] a;
    (req, a = addr) |=> ##[1:3] (resp && rsp_addr == a);
endproperty
assert property (addr_matches);
```

The declaration `logic [7:0] a;` introduces the local variable. The action block
`(req, a = addr)` says: when `req` matches, assign `addr` into `a`. The later term
reads `a`, comparing it to the response's address. Each attempt gets its own `a`, so
overlapping requests do not clobber each other.

## Assignment in sequences

A local-variable assignment rides along with a boolean match using the comma form
inside parentheses:

```systemverilog
// On the matching cycle, also perform the assignment
(boolean_expr, var = expr)
```

The assignment happens *when that boolean matches*, using the sampled values at that
cycle. Several assignments can be chained:

```systemverilog
(start, cnt = 0, base = addr)
```

Assignments may also update a local variable as a sequence advances — for example,
incrementing a counter on each iteration of a repetition. The value carried forward
is always the most recent assignment along the matching thread.

## Sampling: local variables use sampled values

A local-variable assignment captures the **sampled value** of its right-hand side —
the value in the Preponed region, the same value the rest of the assertion sees
(Chapter 2). It does not capture a mid-cycle or glitchy value. This is what makes the
captured data line up cycle-for-cycle with the design's own sampling.

```systemverilog
// 'a' holds the value of addr as sampled on the req cycle,
// not whatever addr becomes later
(req, a = addr) |=> ... (rsp_addr == a)
```

Because the capture is a sampled value, comparing it later against another sampled
value is an apples-to-apples comparison — exactly the semantics a pipelined check
needs.

## Pipelined data checking

The headline use of local variables is verifying a pipeline: data entering at one
stage must emerge, transformed as specified, some fixed number of cycles later.

```systemverilog
// A 3-stage pipe: output equals input + 1, three cycles later
property pipe_add1;
    logic [15:0] d;
    (in_valid, d = in_data) |-> ##3 (out_valid && out_data == d + 1);
endproperty
assert property (pipe_add1);
```

The local variable `d` snapshots the input, the assertion waits the pipeline depth,
and then checks the output against the captured, transformed value. With overlapping
data flowing every cycle, each attempt carries its *own* `d`, so the check correctly
tracks each datum through the pipe even when many are in flight at once.

> **Design intent.** A local variable lets an assertion say "*this* output must
> match *that* input" — binding a response to the specific value that triggered it,
> not merely to "some response happened." It is how a designer states a data-path
> contract: the number that went in is the number (suitably transformed) that comes
> out, every time, through every stage.

## Per-attempt scope and flow

Two properties of local variables follow from "private to one attempt":

- **Independent copies.** Every start of the assertion gets a fresh set of local
  variables. Concurrent, overlapping attempts never share storage, so simultaneous
  in-flight transactions are tracked separately.
- **Flow along the match.** A local variable's value flows forward only along a
  *matching* thread. If a sequence forks (for example through `or` or a bounded
  repetition), each branch carries its own copy, and a value assigned on one branch
  is not visible on another.

This flow model is why local variables compose cleanly with sequence operators: the
value travels with the thread that actually matched, and disappears when that thread
fails.

```systemverilog
// Count consecutive 'beat's and require exactly LEN of them before 'last'
property burst_len;
    int n;
    ($rose(start), n = 0)
    ##1 (beat, n = n + 1)[*1:$] ##0 last
    |-> (n == LEN);
endproperty
assert property (burst_len);
```

Here `n` accumulates across the repetition along the matching thread, and the final
check reads the accumulated count. Each burst tracked by a separate attempt has its
own `n`.

## Reading a local variable before it is assigned

A local variable read on a thread where it was never assigned has an undefined value
for that thread, which makes the check meaningless. Always assign a local variable on
every path that later reads it — usually at the antecedent's trigger, so every
surviving thread carries a defined value.

## Common pitfalls

- **Reading before assigning.** A local variable not assigned on the current thread
  has no meaningful value. Assign it at the trigger so every live thread has it.
- **Expecting one shared variable.** Each attempt has its own copy; you cannot use a
  local variable to pass state *between* separate attempts. Use design state or a
  separate mechanism for that.
- **Forgetting the value is sampled.** The captured value is the Preponed sample, not
  a live or glitchy value. This is correct for cycle-aligned checks but surprises
  anyone expecting blocking-assignment timing.
- **Assigning on a non-matching branch.** A value assigned on a branch that fails
  does not flow forward. Put the assignment on the thread that must carry it.
- **Overcomplicating the antecedent.** Deep local-variable bookkeeping in one
  assertion is hard to read and debug. Prefer the simplest capture that expresses the
  data binding.

## Summary

- A local variable is storage private to one assertion attempt, written on a match
  and read later.
- Assign with the `(boolean, var = expr)` form; the captured value is the sampled
  (Preponed) value.
- Local variables are the tool for pipelined data checking: snapshot the input, wait
  the pipeline depth, compare the output to the captured value.
- Each attempt has independent copies, and values flow only along the matching
  thread, so overlapping transactions are tracked separately.
- Always assign before reading on a given thread, or the value is undefined.

---

[← RTL Assertion Patterns](10-rtl-assertion-patterns.md) · [Table of contents](../README.md) · [Next: Recursive Properties →](12-recursive-properties.md)
