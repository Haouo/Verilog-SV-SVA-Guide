# 附錄 A · Verilog 與 SystemVerilog 對照

[← 除錯與反樣式](../part3-sva/16-debugging-and-antipatterns.md) · [目錄](../README.md) · [下一篇：SVA 速查表 →](B-sva-cheatsheet.md)

本附錄快速對照 Verilog（IEEE 1364-2005）與第二部所涵蓋的 SystemVerilog 設計改進。
每項功能附一句說明，講清楚它對撰寫可合成（synthesizable）RTL 的設計者有何助益。

## 如何使用本附錄

把本附錄當成一份決策參考，用來把 Verilog 的習慣轉成 SystemVerilog 的設計習慣。表格並不是說每個舊有的構件都錯，而是指出 SystemVerilog 在哪些地方能把同一個意圖寫得更明確，也更容易被工具檢查。

要採用某項功能之前，建議先順著連結回到對應的章節。短短的表格只給你動機，章節才會說明各種約束、陷阱，以及考量合成時的脈絡。

---

## 資料型別

| 功能 | Verilog (1364-2005) | SystemVerilog (1800-2023) | 助益說明 |
|---|---|---|---|
| 線網與變數 | `wire`（線網）、`reg`（變數），語意不同 | `logic` 一個關鍵字統一兩者，同為四態 | 消除 `wire` 與 `reg` 的混淆；`logic` 只有一個驅動源，凡是 `reg` 能用的場合都能用。見[第二部 · 第 2 章](../part2-systemverilog/02-enhanced-data-types.md)。 |
| 二態型別 | 無 | `bit`、`byte`、`shortint`、`int`、`longint` | 二態 simulation 速度更快，也更直接對應設計意圖；適合 testbench 算術。 |
| 列舉型別 | 以 `parameter` 或 `localparam` 編碼 | `enum logic [1:0] { IDLE, BUSY, DONE }` | 具名狀態；合成工具與偵錯工具顯示狀態名稱，而非數字。見[第二部 · 第 2 章](../part2-systemverilog/02-enhanced-data-types.md)。 |
| 結構 | 無 | `typedef struct packed { ... }` | 把相關欄位歸為一組；packed struct 可合成。 |
| 聯集 | 無 | `typedef union packed { ... }` | 在同一組位元上重疊多種編碼；packed 時可合成。 |
| void 型別 | 無 | `void`（用於無回傳值的 task） | 讓函式/task 的簽名更清晰。 |
| string 型別 | 無 | `string`（動態） | 適用於不可合成的 testbench 與 assertion 訊息。 |
| 整數字面值 | `8'b0`，必須指定位元寬 | `'0`、`'1`、`'x`、`'z`（位元寬自動推斷） | `q <= '0` 不論位元寬多少都能把所有位元 reset，不必再寫魔術數字。 |

---

## 程序區塊

| 功能 | Verilog (1364-2005) | SystemVerilog (1800-2023) | 助益說明 |
|---|---|---|---|
| 組合邏輯區塊 | `always @(*)` | `always_comb` | 不會有敏感度列表錯誤，工具會自動推斷出完整的列表。Verilog 裡 `@(*)` 漏寫訊號是常見的閂鎖器錯誤。見[第二部 · 第 5 章](../part2-systemverilog/05-procedural-and-operators.md)。 |
| clock 邏輯區塊 | `always @(posedge clk)` | `always_ff @(posedge clk)` | 宣告意圖；lint 與合成工具會對 `always_ff` 裡非正反器的內容發出警告。 |
| 閂鎖器區塊 | 由 `always @(*)` 中不完整的 `if` 推斷 | `always_latch` | 明確宣告；閂鎖器是刻意設計，而非意外產生。 |
| 迴圈變數 | 必須在 `begin` 之前宣告 | `for (int i = 0; ...)`，內嵌宣告 | 迴圈寫得更短，也更不易出錯。 |
| `unique`/`priority` | 無 | `unique case`、`priority case` | 表達設計者對 case 完整性與優先序的判斷，並交由工具驗證。 |
| `case inside` | 無 | `case (expr) inside`，支援萬用字元範圍 | 比對範圍與萬用字元，又不會有 `casex`/`casez` 的副作用。見[第二部 · 第 5 章](../part2-systemverilog/05-procedural-and-operators.md)。 |

---

## 運算子與運算式

| 功能 | Verilog (1364-2005) | SystemVerilog (1800-2023) | 助益說明 |
|---|---|---|---|
| 遞增/遞減 | 無 | `i++`、`i--`、`i += n` | 計數器與迴圈記帳寫得更簡潔。 |
| 萬用字元相等 | 無 | `==?`、`!=?` | 把 `x`/`z` 當 don't-care 來比較；適合用於遮罩。 |
| 串流運算子 | 無 | `{>>{}}`、`{<<{}}` | 反轉或重新切割位元串流，不必手動索引。 |

---

## 套件與範圍

| 功能 | Verilog (1364-2005) | SystemVerilog (1800-2023) | 助益說明 |
|---|---|---|---|
| 共用定義 | 以 `` `include `` 引入標頭檔，或在每個模組各自宣告 `parameter` | `package` 搭配 `import` | enum、struct、parameter 只定義一次，消除複製貼上造成的不一致。見[第二部 · 第 3 章](../part2-systemverilog/03-packages-and-scope.md)。 |
| 範圍限定詞 | 無 | `pkg_name::item` | 提供明確的命名空間，避免跨套件的名稱衝突。 |
| 編譯單元 | 以檔案為單位 | `$unit` 範圍 | 常數在整個編譯單元內可見，不必另外建套件。 |

---

## 介面

| 功能 | Verilog (1364-2005) | SystemVerilog (1800-2023) | 助益說明 |
|---|---|---|---|
| 埠組合 | 每個模組各自重複列出個別的埠 | `interface` + `modport` | 匯流排訊號只宣告一次；modport 依角色強制規定方向。見[第二部 · 第 4 章](../part2-systemverilog/04-interfaces-and-modports.md)。 |
| 埠內協定 | 無 | 介面內可內嵌 assertion 與 task | 把協定規則 bind 在匯流排上，而不是散落在各個模組裡。 |

---

## 參數化

| 功能 | Verilog (1364-2005) | SystemVerilog (1800-2023) | 助益說明 |
|---|---|---|---|
| 參數型別 | `parameter`（無型別或 `integer`） | 帶型別的參數：`parameter int`、`parameter type T` | 在闡述（elaboration）階段就能抓出位元寬不符的錯誤。見[第二部 · 第 6 章](../part2-systemverilog/06-parameterization-and-generate.md)。 |
| `localparam` | 可用，但功能有限 | 支援完整運算式 | 能從其他參數推導出衍生常數。 |

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
