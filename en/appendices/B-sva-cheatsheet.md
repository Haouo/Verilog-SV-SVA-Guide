# Appendix B · SVA Cheat-Sheet

[← Verilog vs SystemVerilog](A-verilog-vs-sv.md) · [Table of contents](../README.md) · [Next: Glossary →](C-glossary.md)

A dense reference card for the SVA constructs covered in Part III. Each section
links to the chapter where the construct is explained in depth.

## How to use this appendix

Use this cheat-sheet after you already understand the intent behind a construct.
It is optimized for recall, not first learning. If a row feels surprising, follow
the chapter link and rebuild the timing model before using the syntax in real RTL
or a formal environment.

The safest workflow is sentence first, operator second: state the protocol rule
in words, choose the sampled facts or sequence shape, then use this appendix to
confirm the exact spelling. SVA syntax is compact; the design sentence keeps it
honest.

---

## Sampled-value functions

Used inside concurrent assertions. All values are taken from the **Preponed**
region of the assertion clock. → [Part III · Ch 4](../part3-sva/04-boolean-layer.md)

| Function | Meaning | Tiny example |
|---|---|---|
| `$rose(e)` | LSB of `e` went 0→1 this cycle | `$rose(req)` — req just asserted |
| `$fell(e)` | LSB of `e` went 1→0 this cycle | `$fell(ack)` — ack just de-asserted |
| `$stable(e)` | `e` unchanged from previous cycle | `busy \|-> $stable(cfg)` |
| `$changed(e)` | `e` differs from previous cycle (negation of `$stable`) | `!$changed(addr)` |
| `$past(e)` | Sampled value of `e` one cycle ago | `q == $past(d)` |
| `$past(e, n)` | Sampled value of `e` exactly `n` cycles ago | `out == $past(in, 3)` |
| `$onehot(e)` | Exactly one bit of `e` is 1 | `$onehot(state)` |
| `$onehot0(e)` | At most one bit of `e` is 1 | `$onehot0(grant)` |
| `$countones(e)` | Number of bits set to 1 in `e` | `$countones(active) == 2` |
| `$isunknown(e)` | Any bit of `e` is `x` or `z` | `!$isunknown(ctrl)` |

---

## Sequence operators

Sequences describe patterns of events across clock cycles.
→ [Part III · Ch 5](../part3-sva/05-sequences-basics.md) and
[Ch 6](../part3-sva/06-sequence-operations.md)

### Delay operators

| Syntax | Meaning | Example |
|---|---|---|
| `s1 ##n s2` | `s1` then exactly `n` cycles later `s2` | `req ##1 gnt` |
| `s1 ##[m:n] s2` | `s1` then between `m` and `n` cycles later `s2` | `req ##[1:4] gnt` |
| `s1 ##[*] s2` | `s1` then 0 or more cycles later `s2` (alias `##[0:$]`) | `start ##[*] done` |
| `s1 ##[+] s2` | `s1` then 1 or more cycles later `s2` (alias `##[1:$]`) | `req ##[+] ack` |

### Repetition operators

| Syntax | Meaning | Example |
|---|---|---|
| `e [*n]` | `e` is true for exactly `n` consecutive cycles | `valid [*3]` |
| `e [*m:n]` | `e` is true for `m` to `n` consecutive cycles | `busy [*1:8]` |
| `e [*]` | `e` is true for 0 or more consecutive cycles | `stall [*]` |
| `e [+]` | `e` is true for 1 or more consecutive cycles | `hold [+]` |
| `e [->n]` | `e` is true for exactly `n` non-consecutive occurrences (goto repetition) | `ack [->1]` |
| `e [=n]` | `e` is true for exactly `n` occurrences, no consecutive requirement (non-consecutive repetition) | `err [=2]` |

### Composition operators

| Syntax | Meaning | Example |
|---|---|---|
| `s1 and s2` | Both sequences start at the same point; both must complete | `req_a and req_b` |
| `s1 or s2` | Either sequence holds | `(a ##1 b) or (c ##2 d)` |
| `s1 intersect s2` | Both sequences hold and end at the same cycle | `s1 intersect s2` |
| `e throughout s` | `e` is true throughout every cycle `s` spans | `valid throughout (a ##1 b)` |
| `s1 within s2` | `s1` is contained (matched) within `s2` | `pulse within window` |
| `first_match(s)` | Only the earliest match of `s` is taken | `first_match(a ##[1:5] b)` |

---

## Property operators

Properties compose sequences into checkable temporal statements.
→ [Part III · Ch 7](../part3-sva/07-properties.md)

### Implication

| Syntax | Meaning | Notes |
|---|---|---|
| `s \|-> p` | Overlapping implication: if `s` matches ending now, check `p` starting now | Same endpoint |
| `s \|=> p` | Non-overlapping implication: if `s` matches, check `p` starting next cycle | `\|=>` ≡ `\|-> ##1` |

### Boolean and temporal connectives

| Syntax | Meaning | Example |
|---|---|---|
| `not p` | Negation of property `p` | `not ($rose(err))` |
| `p and q` | Both properties must hold | `p1 and p2` |
| `p or q` | At least one must hold | `p1 or p2` |
| `if (e) p` | If `e` holds, `p` must hold (vacuously true otherwise) | `if (mode) p` |
| `if (e) p else q` | `p` when `e`; `q` otherwise | |
| `nexttime p` | `p` must hold starting one cycle from now | `nexttime (q == 0)` |
| `nexttime [n] p` | `p` must hold starting `n` cycles from now | `nexttime [3] p` |
| `s_nexttime p` | Strong form: endpoint must be reached | |
| `always p` | `p` holds at every future point | `always $onehot(state)` |
| `s_always [m:n] p` | Strong always over a finite window | |
| `eventually [m:n] p` | `p` holds within the window (weak form must be bounded) | `eventually [1:8] done` |
| `s_eventually p` | Strong eventually — `p` must eventually hold (may be unbounded) | |
| `p until q` | `p` holds until `q` holds (weak — `q` need not occur) | `busy until idle` |
| `p s_until q` | Strong until — `q` must eventually hold | `busy s_until idle` |
| `p until_with q` | `p` holds through the cycle `q` first holds | |
| `p implies q` | If `p` holds at this point, `q` must too | |
| `p iff q` | Bi-directional implication | |

---

## Assertion statements

→ [Part III · Ch 3](../part3-sva/03-assertion-kinds.md)

### Concurrent assertion statements

Evaluated at each clock tick; result reported by a simulator or formal tool.

| Statement | Purpose | Typical placement |
|---|---|---|
| `assert property (p)` | Verify `p` holds; failure is an error | RTL module, checker, bind |
| `assume property (p)` | Constrain inputs; treated as axiom by formal tools | Formal environment |
| `cover property (p)` | Record that `p` was witnessed at least once | RTL module, checker |
| `restrict property (p)` | Formal only: hard constraint (no simulation effect) | Formal environment |

Syntax pattern:
```systemverilog
label: assert property (@(posedge clk) disable iff (!rst_n) antecedent |-> consequent)
    else $error("message");
```

### Immediate assertion statements

Procedural; evaluated the moment they execute, like a statement.

| Statement | Timing | Use |
|---|---|---|
| `assert (expr)` | Active region (inline, when reached) | Inside `always`, `initial`, tasks |
| `assert final (expr)` | Reactive region | End-of-step checks |
| `assert #0 (expr)` | Observed region | Deferred: avoids glitch reads |

---

## Clocking and disable

→ [Part III · Ch 8](../part3-sva/08-clocking-and-reset.md)

| Construct | Meaning | Example |
|---|---|---|
| `@(posedge clk)` inline | Per-assertion clock | `assert property (@(posedge clk) p)` |
| `default clocking cb @(posedge clk); endclocking` | Module-wide default clock | Omit clock on each assertion |
| `disable iff (expr)` | Suppress assertion while `expr` is true (typically reset) | `disable iff (!rst_n)` |
| `$inferred_clock` | Clock inferred from the assertion's context (e.g. `default clocking` or an enclosing procedure) | Rarely written explicitly |

---

## Bind

→ [Part III · Ch 9](../part3-sva/09-binding-and-placement.md)

```systemverilog
bind target_module assertion_module inst_name (
    .clk   (clk),
    .sig_a (sig_a)
);
```

Attaches an assertion module to `target_module` without modifying its source.

---

[← Verilog vs SystemVerilog](A-verilog-vs-sv.md) · [Table of contents](../README.md) · [Next: Glossary →](C-glossary.md)
