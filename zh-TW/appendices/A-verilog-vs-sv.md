# 附錄 A · Verilog 與 SystemVerilog 對照

[← 除錯與反樣式](../part3-sva/16-debugging-and-antipatterns.md) · [目錄](../README.md) · [下一篇：SVA 速查表 →](B-sva-cheatsheet.md)

本附錄快速對照 Verilog（IEEE 1364-2005）與第二部所涵蓋的 SystemVerilog 設計改進。
每項功能附一句說明，解釋它對撰寫可合成（synthesizable）RTL 的設計者有何助益。

## 如何使用這個 appendix

請把這個 appendix 當成 decision aid，用來把 Verilog habit 轉成 SystemVerilog design habit。表格
不是說每個舊 construct 都錯，而是在指出 SystemVerilog 哪些地方能把同一個 intent 寫得更 explicit，
也更容易被 tool check。

採用某個 feature 前，建議先沿著 link 回到對應 chapter。短表格提供 motivation，但 chapter 會說明
constraint、pitfall，以及 synthesis-aware context。

---

## 資料型別

| 功能 | Verilog (1364-2005) | SystemVerilog (1800-2023) | 助益說明 |
|---|---|---|---|
| 線網與變數 | `wire`（線網）、`reg`（變數）— 語意不同 | `logic` 統一代替兩者 — 同為四態，單一關鍵字 | 消除 `wire` 與 `reg` 的混淆；`logic` 只有一個驅動源，可用於 `reg` 的所有場合。見[第二部 · 第 2 章](../part2-systemverilog/02-enhanced-data-types.md)。 |
| 二態型別 | 無 | `bit`、`byte`、`shortint`、`int`、`longint` | 二態 simulation 速度更快，更直接地對應設計意圖；適合 testbench 算術。 |
| 列舉型別 | 以 `parameter` 或 `localparam` 編碼 | `enum logic [1:0] { IDLE, BUSY, DONE }` | 具名狀態；合成工具與偵錯工具顯示狀態名稱，而非數字。見[第二部 · 第 2 章](../part2-systemverilog/02-enhanced-data-types.md)。 |
| 結構 | 無 | `typedef struct packed { ... }` | 將相關欄位分組；packed struct 可合成。 |
| 聯集 | 無 | `typedef union packed { ... }` | 在同一組位元上重疊多種編碼；packed 時可合成。 |
| void 型別 | 無 | `void`（用於無回傳值的 task） | 讓函式/task 簽名更清晰。 |
| string 型別 | 無 | `string`（動態） | 適用於非合成的 testbench 與 assertion message。 |
| 整數字面值 | `8'b0`，必須指定位元寬 | `'0`、`'1`、`'x`、`'z`（位元寬自動推斷） | `q <= '0` 無論位元寬為何皆能將所有位元 reset，不需寫魔術數字。 |

---

## 程序區塊

| 功能 | Verilog (1364-2005) | SystemVerilog (1800-2023) | 助益說明 |
|---|---|---|---|
| 組合邏輯區塊 | `always @(*)` | `always_comb` | 無敏感度列表錯誤；工具自動推斷完整列表。Verilog 中 `@(*)` 漏寫訊號是常見的閂鎖器錯誤。見[第二部 · 第 5 章](../part2-systemverilog/05-procedural-and-operators.md)。 |
| clock 邏輯區塊 | `always @(posedge clk)` | `always_ff @(posedge clk)` | 宣告意圖；lint 與合成工具可對 `always_ff` 內的非正反器內容發出警告。 |
| 閂鎖器區塊 | 由 `always @(*)` 中不完整的 `if` 推斷 | `always_latch` | 明確宣告；閂鎖器是刻意的，而非意外。 |
| 迴圈變數 | 必須在 `begin` 前宣告 | `for (int i = 0; ...)` — 內嵌宣告 | 迴圈寫法更簡短，較不易出錯。 |
| `unique`/`priority` | 無 | `unique case`、`priority case` | 表達設計者對 case 完整性與優先序的知識；工具可加以驗證。 |
| `case inside` | 無 | `case (expr) inside`，支援萬用字元範圍 | 無需 `casex`/`casez` 的副作用即可匹配範圍與萬用字元。見[第二部 · 第 5 章](../part2-systemverilog/05-procedural-and-operators.md)。 |

---

## 運算子與運算式

| 功能 | Verilog (1364-2005) | SystemVerilog (1800-2023) | 助益說明 |
|---|---|---|---|
| 遞增/遞減 | 無 | `i++`、`i--`、`i += n` | 簡潔的計數器與迴圈書寫。 |
| 萬用字元相等 | 無 | `==?`、`!=?` | 以 `x`/`z` 作為 don't-care 進行比較；適用於遮罩。 |
| 串流運算子 | 無 | `{>>{}}`、`{<<{}}` | 無需手動索引即可反轉或重新切割位元串流。 |

---

## 套件與範圍

| 功能 | Verilog (1364-2005) | SystemVerilog (1800-2023) | 助益說明 |
|---|---|---|---|
| 共用定義 | 以 `` `include `` 引入標頭檔，或在每個模組各自宣告 `parameter` | `package` 加 `import` | enum、struct、parameter 只需定義一次；消除複製貼上的不一致。見[第二部 · 第 3 章](../part2-systemverilog/03-packages-and-scope.md)。 |
| 範圍限定詞 | 無 | `pkg_name::item` | 明確的命名空間，避免跨套件名稱衝突。 |
| 編譯單元 | 以檔案為單位 | `$unit` 範圍 | 常數在整個編譯單元內可見，不需額外建立套件。 |

---

## 介面

| 功能 | Verilog (1364-2005) | SystemVerilog (1800-2023) | 助益說明 |
|---|---|---|---|
| 埠組合 | 每個模組各自重複列出個別埠 | `interface` + `modport` | 匯流排訊號只宣告一次；modport 依角色強制規定方向。見[第二部 · 第 4 章](../part2-systemverilog/04-interfaces-and-modports.md)。 |
| 埠內協定 | 無 | 介面內可內嵌 assertion 與 task | 將協定規則 bind 於匯流排，而非散落在各模組中。 |

---

## 參數化

| 功能 | Verilog (1364-2005) | SystemVerilog (1800-2023) | 助益說明 |
|---|---|---|---|
| 參數型別 | `parameter`（無型別或 `integer`） | 帶型別的參數：`parameter int`、`parameter type T` | 在闡述（elaboration）階段即可捕捉位元寬不符的錯誤。見[第二部 · 第 6 章](../part2-systemverilog/06-parameterization-and-generate.md)。 |
| `localparam` | 可用，但功能有限 | 支援完整運算式 | 可從其他參數推導衍生常數。 |

---

## 快速對照摘要

```text
Verilog                    SystemVerilog 等效寫法
──────────────────────────────────────────────────
wire / reg                 logic（或 wire logic）
always @(*)                always_comb
always @(posedge clk)      always_ff @(posedge clk)
8'b0 reset                 '0
casez / casex              case inside
各模組各自的 parameter      package + import
重複列出的埠                interface + modport
```

---

[← 除錯與反樣式](../part3-sva/16-debugging-and-antipatterns.md) · [目錄](../README.md) · [下一篇：SVA 速查表 →](B-sva-cheatsheet.md)
