# Glossary · 術語對照表

Shared bilingual terminology for this guide. Technical terms stay in English in
both editions; this table fixes the Traditional Chinese gloss so translations
stay consistent. Add a term here before using a new translation in a chapter.

本指南共用的雙語術語。技術名詞在兩個版本中皆保留英文；本表固定其繁體中文譯名，
以維持翻譯一致。在章節使用新譯名前，請先於此處登錄。

| English | 繁體中文 | Note |
|---|---|---|
| design intent | 設計意圖 | What the hardware is *supposed* to do. |
| RTL (Register-Transfer Level) | 暫存器轉移層級 | Abstraction level for synthesizable design. |
| synthesizable | 可合成 | Code a synthesis tool can map to gates. |
| synthesis | 合成 | Mapping RTL to a gate-level netlist. |
| elaboration | 闡述 / 展開 | Resolving parameters and hierarchy before simulation. |
| net | 線網 | A connection driven by something (e.g. `wire`). |
| variable | 變數 | Holds a value until next assigned (e.g. `reg`, `logic`). |
| combinational logic | 組合邏輯 | Output depends only on present inputs. |
| sequential logic | 循序邏輯 | Output depends on state; clocked. |
| flip-flop | 正反器 | Edge-triggered storage element. |
| latch | 閂鎖器 | Level-sensitive storage element (usually unintended in RTL). |
| blocking assignment | 阻塞式指定 | `=` in procedural code. |
| non-blocking assignment | 非阻塞式指定 | `<=` in procedural code. |
| sensitivity list | 敏感度列表 | Signals that trigger an `always` block. |
| finite state machine (FSM) | 有限狀態機 | Control logic modeled as states + transitions. |
| testbench | 測試平台 | Non-synthesizable code that stimulates a design. |
| assertion | 斷言 | A checkable statement of intended behavior. |
| immediate assertion | 即時斷言 | Procedural, evaluated like a statement. |
| concurrent assertion | 並行斷言 | Clocked, evaluated over time. |
| deferred assertion | 延遲斷言 | Immediate assertion reported in a later region. |
| property | 性質 | A temporal statement that can hold or fail. |
| sequence | 序列 | A description of events over clock cycles. |
| implication | 蘊涵 | `\|->` / `\|=>` antecedent-then-consequent. |
| antecedent | 前提 | Left side of an implication. |
| consequent | 後件 | Right side of an implication. |
| sampled value | 取樣值 | Signal value in the Preponed region. |
| clocking block | 時脈區塊 | Groups signals under a clock for sampling/driving. |
| vacuity / vacuous | 空真 / 空泛成立 | Pass with the antecedent never satisfied. |
| cover | 覆蓋 | Check that a behavior actually occurred. |
| Assertion-Based Verification (ABV) | 基於斷言的驗證 | Methodology centered on assertions. |
| formal verification | 形式化驗證 | Mathematical proof over all legal inputs. |
| safety property | 安全性性質 | "Something bad never happens." |
| liveness property | 活性性質 | "Something good eventually happens." |
| bind | 綁定 | Attach assertions/modules to a design without editing it. |
| checker | checker | Reusable container for assertions (SV `checker`). |
