# Verilog、SystemVerilog 與 SVA：數位設計工程師指南 — 繁體中文版

[← 回到首頁](../README.md) · [English Edition](../en/README.md)

本指南寫給 RTL 設計工程師。內容涵蓋撰寫可合成（synthesizable）硬體所需的 Verilog
與 SystemVerilog，並深入介紹 **SystemVerilog Assertions（SVA）**，因為斷言
（assertion）正是設計者用來記錄設計意圖（design intent）的工具。

若你剛接觸這些語言，建議依序閱讀。若你已能撰寫 RTL，可直接跳到 **第三部**。

## 目錄

### 第 0 部 — 導論
- [導論](00-introduction.md) — 讀者對象、設計意圖、如何使用本指南。

### 第一部 — Verilog 設計
可合成 RTL，依據 IEEE 1364-2005。

1. [模組與階層](part1-verilog/01-modules-and-hierarchy.md)
2. [資料型別與數值](part1-verilog/02-data-types-and-values.md)
3. [運算子與運算式](part1-verilog/03-operators-and-expressions.md)
4. [組合邏輯](part1-verilog/04-combinational-logic.md)
5. [循序邏輯](part1-verilog/05-sequential-logic.md)
6. [有限狀態機](part1-verilog/06-finite-state-machines.md)
7. [面向合成的撰寫](part1-verilog/07-synthesis-aware-coding.md)
8. [測試平台基礎（僅提及）](part1-verilog/08-testbench-essentials.md)

### 第二部 — SystemVerilog 設計
SystemVerilog 設計子集，依據 IEEE 1800-2023。

1. [為何用 SystemVerilog 做設計](part2-systemverilog/01-why-sv-for-design.md)
2. [強化的資料型別](part2-systemverilog/02-enhanced-data-types.md)
3. [套件與範圍](part2-systemverilog/03-packages-and-scope.md)
4. [介面與 modport](part2-systemverilog/04-interfaces-and-modports.md)
5. [程序區塊與運算子](part2-systemverilog/05-procedural-and-operators.md)
6. [參數化與 generate](part2-systemverilog/06-parameterization-and-generate.md)
7. [驗證功能概覽（僅提及）](part2-systemverilog/07-verification-features-overview.md)

### 第三部 — SystemVerilog Assertions（核心重點）
實務上的設計意圖斷言，並涵蓋進階與形式化（formal）主題。

1. [為何需要斷言](part3-sva/01-why-assertions.md)
2. [模擬語意](part3-sva/02-simulation-semantics.md)
3. [斷言種類](part3-sva/03-assertion-kinds.md)
4. [布林層](part3-sva/04-boolean-layer.md)
5. [序列：基礎](part3-sva/05-sequences-basics.md)
6. [序列運算](part3-sva/06-sequence-operations.md)
7. [性質（property）](part3-sva/07-properties.md)
8. [時脈與重置](part3-sva/08-clocking-and-reset.md)
9. [綁定與放置](part3-sva/09-binding-and-placement.md)
10. [RTL 斷言樣式](part3-sva/10-rtl-assertion-patterns.md)
11. [區域變數](part3-sva/11-local-variables.md)
12. [遞迴性質](part3-sva/12-recursive-properties.md)
13. [覆蓋率與空真（vacuity）](part3-sva/13-coverage-and-vacuity.md)
14. [形式化驗證入門](part3-sva/14-formal-verification-primer.md)
15. [checker 與函式庫](part3-sva/15-checkers-and-libraries.md)
16. [除錯與反樣式](part3-sva/16-debugging-and-antipatterns.md)

### 附錄
- [A — Verilog 與 SystemVerilog 對照](appendices/A-verilog-vs-sv.md)
- [B — SVA 速查表](appendices/B-sva-cheatsheet.md)
- [C — 詞彙表](appendices/C-glossary.md)
- [D — 參考文獻](appendices/D-references.md)

---

共用術語：[GLOSSARY.md](../GLOSSARY.md) ·
撰寫慣例：[CONTRIBUTING.md](../CONTRIBUTING.md)
