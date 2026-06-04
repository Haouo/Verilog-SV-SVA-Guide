# 第二部 · 1. 為何用 SystemVerilog 做設計

[← 測試平台基礎](../part1-verilog/08-testbench-essentials.md) · [目錄](../README.md) · [下一章：強化的資料型別 →](02-enhanced-data-types.md)

## 學習目標

- 理解為何 `logic` 在可合成（synthesizable）RTL 中能同時取代 `wire` 與 `reg`。
- 以 `always_comb`、`always_ff`、`always_latch` 明確表達程序區塊的設計意圖。
- 了解這三種特化 `always` 區塊如何讓工具檢查設計規則。
- 使用 `unique` 與 `priority` 修飾 case 敘述，以記錄決策結構。

## 設計者 mental model

SystemVerilog 讓 RTL 可以更直接地表達 intent。`logic` 減少 `wire`/`reg` 的儀式感，specialized
`always_*` block 宣告 process 應該 infer 哪一種 hardware，`unique` 或 `priority` 則把 designer
對 decision tree 的假設交給 tool 檢查。

重點不是為了新語法而用新語法，而是把設計知識從 comment 和 coding folklore 移到 simulator、
linter、synthesis tool 可以 check 的 construct 裡。當一個 SystemVerilog construct 能降低 hardware
描述的 ambiguity，它就值得使用。

## Verilog 型別的問題

Verilog 要求將訊號宣告為 `wire` 或 `reg`。這個區別源自歷史，而非邏輯：`wire` 是線網（net），由持續性 `assign` 或模組埠驅動；`reg` 是變數（variable），在程序性指定之間保持其值。這兩個名稱都無法告訴你硬體是組合邏輯（combinational logic）還是循序邏輯（sequential logic）。

這個混淆很深。`reg` 並不代表暫存器（register）。在 `always @(*)` 組合邏輯區塊內，你完全可以也應該使用 `reg`。工具是從區塊的結構推斷閂鎖器（latch）或組合閘，而非從訊號的宣告型別。閱讀程式碼的設計者，光靠 `reg` 無法判斷設計者是否意圖使用正反器（flip-flop）。

SystemVerilog 引入了 `logic`，這是一種單一的 4-state 型別，可以在所有過去使用 `wire` 或 `reg` 的地方使用。它簡化了宣告、消除了混淆，是 RTL 訊號的正確預設型別。

```systemverilog
// Verilog — 兩種型別，一個概念
wire [7:0] bus;
reg  [7:0] count;

// SystemVerilog — 兩者皆用一種型別
logic [7:0] bus;
logic [7:0] count;
```

4-state 值（0、1、X、Z）被完整保留。合成（synthesis）工具忽略 X 與 Z；它們存在於 simulation 中，用於建模未初始化的狀態和高阻抗（high-impedance）。

### 何時保留 `wire`

`logic` 無法被多個持續性來源驅動（多個 `assign` 敘述或多個模組輸出接到同一線網）。那種情況下，三態（tri-state）匯流排仍需使用 `wire`。在實際情況中，可合成 RTL 幾乎不在內部使用三態；只有在確實需要多驅動連接時才使用 `wire`。

## 特化的 always 區塊

Verilog 的 `always @(*)` 能用，但它是泛用的：它不記錄你意圖使用正反器、閂鎖器還是組合邏輯，編譯器和 simulator 也無法檢查程式碼是否符合你的意圖。SystemVerilog 提供三種具有明確目的的形式。

### `always_comb`

使用 `always_comb` 表示組合邏輯。simulator 自動從區塊中讀取的所有變數推導敏感度列表（sensitivity list）——你完全不需要寫 `@(*)`。更重要的是，工具會檢查此區塊確實是組合邏輯：每個輸出必須在區塊的每條執行路徑上都被指定，且不允許有回授。

```systemverilog
always_comb begin
    // Combinational mux: no inferred latch
    if (sel)
        y = a;
    else
        y = b;
end
```

若你不小心在某條路徑上漏掉某個變數的指定，lint 工具或 simulator 會報告違規。使用普通的 `always @(*)`，你會悄悄地推斷出一個閂鎖器。

`always_comb` 也在時間零之後的一個 delta 時間點啟動，確保此區塊在任何邊緣觸發區塊讀取其輸出之前先完成求值。這與組合邏輯在時脈緣之前穩定的行為一致。

### `always_ff`

使用 `always_ff` 表示帶時脈的循序邏輯。你仍然需要寫出敏感度列表（時脈和任何非同步重置）。工具會檢查列表中只出現邊緣敏感訊號，且區塊使用非阻塞式指定（non-blocking assignment）`<=`。

```systemverilog
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        count <= '0;
    else if (en)
        count <= count + 1;
end
```

違規——例如使用 `=` 而非 `<=`——會被標記為 lint 錯誤，而不是悄悄產生錯誤行為。這個關鍵字對每位閱讀者和每個工具都清楚地說明了設計意圖。

### `always_latch`

當確實需要電平敏感閂鎖器（level-sensitive latch）時（在 RTL 中極為罕見），使用 `always_latch`。工具會檢查此區塊具有閂鎖器特性：不完整的指定是機制，而非錯誤。

```systemverilog
always_latch begin
    // Intentional latch: hold q when en is low
    if (en)
        q <= d;
end
```

在大多數設計中，`always_latch` 區塊是一個警示，提示設計意圖應該重新考量。優先使用暫存器邏輯。但當閂鎖器是刻意的——例如在時脈閘控（clock-gate）使能路徑中——使用 `always_latch` 讓意圖明確，並能抑制虛假的 lint 警告。

> **設計意圖。** `always_comb`、`always_ff`、`always_latch` 將每個程序區塊對應到一種硬體類別。閱讀者從關鍵字就能看出意圖，而無需解讀敏感度列表和指定風格。工具接著可以檢查程式碼是否符合關鍵字的聲明——將編碼慣例轉化為可強制執行的規則。

## `unique` 與 `priority` case 修飾詞

Verilog 的普通 `case` 敘述不保證覆蓋完整性。若沒有分支匹配，輸出保持當前值（在組合邏輯區塊中暗示閂鎖器），或者單純不更新。SystemVerilog 新增兩個修飾詞，用於記錄和檢查決策結構。

### `unique case`

`unique case` 聲明兩件事：

1. 各分支互斥（不可能有兩個分支同時匹配）。
2. 此 case 是完整的（任何合法輸入至少匹配一個分支）。

```systemverilog
always_comb begin
    unique case (op)
        2'b00: result = a + b;
        2'b01: result = a - b;
        2'b10: result = a & b;
        2'b11: result = a | b;
    endcase
end
```

使用 `unique`，合成工具可以在假設各分支互斥的前提下進行最佳化。若 case 表達式同時匹配多個分支或完全不匹配，simulator 會在執行時發出警告。這消除了那些本應完整解碼的 case 中的優先級編碼和推斷的閂鎖器。

### `priority case`

`priority case` 聲明各分支按順序求值，第一個匹配的分支獲勝——如同一連串的 `if / else if`。它也聲明 case 是完整的：至少有一個分支永遠會匹配。

```systemverilog
always_comb begin
    priority case (1'b1)          // one-hot check
        req[0]: grant = 4'b0001;
        req[1]: grant = 4'b0010;
        req[2]: grant = 4'b0100;
        req[3]: grant = 4'b1000;
    endcase
end
```

`priority case` 適用於優先級編碼器或第一匹配仲裁確實是設計意圖的情況。若各分支確實互斥，應使用 `unique`。

### `unique if` 與 `priority if`

相同的修飾詞也適用於 `if / else if` 鏈：

```systemverilog
// All conditions mutually exclusive and complete
unique if (state == IDLE)   next = FETCH;
else if (state == FETCH)    next = DECODE;
else if (state == DECODE)   next = EXECUTE;
else if (state == EXECUTE)  next = IDLE;
```

在完整解碼的有限狀態機（FSM）狀態轉換上使用 `unique if`，告訴工具每個合法狀態都已覆蓋且無兩個條件重疊。工具在 simulation 時進行兩者的檢查，並在合成時可進行最佳化。

## 常見陷阱

- **使用 `reg` 卻意圖是 `logic`。** 名稱容易誤導；將所有非真正多驅動線網的 RTL 訊號都改為 `logic`。
- **對循序邏輯寫 `always @(*)`。** 一個讀取時脈緣的 `always @(*)` 區塊具有非直覺的敏感度列表。請使用 `always_ff` 並明確地將時脈加入列表。
- **忘記 `always_comb` 會檢查完整性。** 它不會悄悄允許不完整的分支——這正是它的目的。請加入 `default` 或涵蓋所有情況。
- **對不完整的集合使用 `unique`。** 若輸入合法上可能落在列出的分支之外，請勿使用 `unique`；你會得到虛假的 simulation 警告。
- **在 `always_ff` 中混用阻塞式指定 `=`。** Lint 工具會將此標記為違反 `always_ff` 合約。請使用 `<=`。

## 小結

- `logic` 統一了 RTL 訊號的 `wire` 與 `reg`；除真正的多驅動線網外，一律使用它。
- `always_comb`、`always_ff`、`always_latch` 使程序區塊的意圖明確，並讓工具能夠檢查設計規則。
- `unique case` 聲明互斥且完整的決策；`priority case` 聲明按優先級排序且完整的決策；兩者在 simulation 時都被檢查。
- 這些特性在合成時零成本——它們增加資訊，不增加硬體。

---

[← 測試平台基礎](../part1-verilog/08-testbench-essentials.md) · [目錄](../README.md) · [下一章：強化的資料型別 →](02-enhanced-data-types.md)
