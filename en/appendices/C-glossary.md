# Appendix C · Glossary

[← SVA Cheat-Sheet](B-sva-cheatsheet.md) · [Table of contents](../README.md) · [Next: References →](D-references.md)

The full bilingual glossary lives at the repository root:
**[../../GLOSSARY.md](../../GLOSSARY.md)**

That file is the single source of truth for term translations used throughout
both the English and Traditional Chinese editions. Add a term there before
introducing a new translation in any chapter.

---

## Quick reference — eight core terms

The eight terms below appear in nearly every chapter. The gloss here is a
convenience; the canonical entry is in GLOSSARY.md.

| Term | Traditional Chinese | Brief definition |
|---|---|---|
| design intent | 設計意圖 | What the hardware is *supposed* to do — the designer's mental model, stated explicitly. |
| RTL (Register-Transfer Level) | 暫存器轉移層級 | The abstraction level at which synthesizable hardware is described: operations on registers, transferred each clock cycle. |
| assertion | 斷言 | A checkable statement of intended behavior. Violations are reported by simulators and formal tools. |
| property | 性質 | A temporal statement — ranging over one or more clock cycles — that can hold or fail at a given point in time. |
| sequence | 序列 | A description of a pattern of signal events across one or more clock cycles, used as a building block for properties. |
| implication | 蘊涵 | The `\|->` (overlapping) or `\|=>` (non-overlapping) operator: "if the antecedent matches, the consequent must hold." |
| vacuity / vacuous pass | 空真 / 空泛成立 | An assertion passes vacuously when its antecedent is never true — no real checking occurred. Cover properties diagnose this. |
| formal verification | 形式化驗證 | Mathematical proof that a property holds for all legal inputs and all reachable states, without simulation. |

---

[← SVA Cheat-Sheet](B-sva-cheatsheet.md) · [Table of contents](../README.md) · [Next: References →](D-references.md)
