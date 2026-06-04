# 第一部 · 5. 循序邏輯

[← 組合邏輯](04-combinational-logic.md) · [目錄](../README.md) · [下一章：有限狀態機 →](06-finite-state-machines.md)

## 學習目標

- 以帶時脈的 `always` 區塊推斷正反器（flip-flop）。
- 在循序邏輯中使用非阻塞式指定（non-blocking assignment），並理解原因。
- 在同步重置與非同步重置之間做出選擇。
- 避免阻塞式/非阻塞式指定的經典競態（race）問題。

## 設計者 mental model

sequential logic 是 time 變成 state 的地方。clock edge sample input value，並 commit 新的
register value；edge 之間 register 維持不變。code form 應該讓這個 sampling story 很清楚，
所以 clocked logic 預設使用 non-blocking assignment。

reset 也是同一個 story 的一部分。它定義 design 在 initialization 或 recovery 之後承諾進入哪個
state。reset branch 不是裝飾，而是在回答：「normal traffic 開始前，哪些 value 必須是 safe 的？」
如果這個答案不清楚，後面的 assertion 和 testbench 也會不清楚。

## 推斷正反器

循序邏輯（sequential logic）具有在時脈緣更新的狀態。透過由時脈緣觸發的 `always` 區塊，可推斷出正反器：

```verilog
always @(posedge clk) begin
    q <= d;
end
```

這表示：在 `clk` 的每個上升緣，`q` 取得 `d` 的值。這就是一個 D 型正反器。敏感度列表中的 `posedge`（或 `negedge`）使邏輯成為循序，而非組合。

## 循序邏輯使用非阻塞式指定

在帶時脈的區塊內，請使用非阻塞式指定 `<=`，而非阻塞式指定 `=`。這是 Verilog 中最重要的規則之一。

- **阻塞式（`=`）** 立即按順序執行，如同軟體語句。
- **非阻塞式（`<=`）** 先取樣所有右側值，再在時間步結束時統一更新所有左側目標。

非阻塞式指定模擬了真實正反器的行為：所有正反器在時脈緣同時取樣輸入，再統一更新。考慮一個移位暫存器（shift register）：

```verilog
// Correct: all three FFs sample, then all update
always @(posedge clk) begin
    q1 <= d;
    q2 <= q1;
    q3 <= q2;
end
```

使用 `<=` 時，`q2` 取得的是*舊*的 `q1`，與硬體行為完全一致，形成三級移位暫存器。若改用 `=`，`q1` 會先更新，`q2` 讀到的就是*新*的 `q1`，使移位暫存器退化為單一級。關鍵字的選擇直接改變了硬體。

第 4 章的配對規則與此完整呼應：

- **循序（帶時脈）邏輯 → 非阻塞式 `<=`。**
- **組合邏輯 → 阻塞式 `=`。**

遵循這個規則，可避免絕大多數指定相關的錯誤。

## 重置

正反器通常需要重置以達到已知狀態。有兩種風格。

### 同步重置

重置在時脈緣取樣，與其他輸入相同：

```verilog
always @(posedge clk) begin
    if (rst)
        q <= 1'b0;
    else
        q <= d;
end
```

同步重置使所有邏輯保持在帶時脈的域內，對時序分析以及大多數 FPGA 架構友好。其缺點是需要運作中的時脈才能生效。

### 非同步重置

重置立即生效，不受時脈影響，透過出現在敏感度列表中來實現：

```verilog
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        q <= 1'b0;
    else
        q <= d;
end
```

非同步重置（此處為低電位有效的 `rst_n`）在重置訊號拉低的瞬間強制進入狀態，即使沒有時脈也有效。其缺點在於重置的*釋放*：若重置在靠近時脈緣的時刻取消，正反器可能進入亞穩態（metastable），因此釋放訊號必須同步化。

在一個時脈域（clock domain）內選定一種風格並一致地套用。在同一個域內混用重置風格會造成問題。

> **設計意圖。** 重置是一個承諾：「重置之後，每個狀態元素持有已知的值。」
> 為每個正反器撰寫重置分支，並保持風格一致，就是陳述這個承諾。
> 「重置後 `q == 0`」這類斷言（第三部）能將承諾轉化為工具可驗證的條件。

## 阻塞式/非阻塞式指定的競態

若在同一個時間步內，一個區塊以 `=` 指定某變數，另一個區塊讀取它，結果就取決於 simulator 執行各區塊的順序——這就是競態。遵循上述兩條規則（帶時脈用 `<=`，組合邏輯用 `=`，且同一訊號絕不混用）可消除這類競態。不要從兩個 `always` 區塊指定同一個變數，也不要對同一個變數混用 `=` 與 `<=`。

## 完整的暫存器範例

```verilog
module counter #(
    parameter WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             en,
    output reg  [WIDTH-1:0] count
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= {WIDTH{1'b0}};
        else if (en)
            count <= count + 1'b1;
    end
endmodule
```

注意結構：非同步重置在前，再接同步行為。`count` 在 `en` 為低時保持——這是帶時脈區塊中刻意的狀態保持，而非閂鎖器。

## 常見陷阱

- **在帶時脈邏輯中使用阻塞式指定。** 會破壞移位暫存器並產生競態。請使用 `<=`。
- **對同一個變數混用 `=` 與 `<=`。** 依規則每個區塊只選用其中一種。
- **兩個區塊驅動同一個暫存器。** 每個狀態元素只有一個驅動者。
- **在同一個時脈域內混用重置風格。** 選定同步或非同步並堅持到底。
- **忘記重置需要已知初始值的狀態。** 未重置的正反器以 `x` 啟動。

## 小結

- 帶時脈的 `always @(posedge clk)` 區塊推斷正反器。
- 帶時脈邏輯使用 `<=`；組合邏輯使用 `=`。
- 同步重置保持在時脈域內；非同步重置立即生效，但釋放訊號需要同步化。
- 每個暫存器只有一個驅動者，且在同一個域內保持一致的重置風格。

---

[← 組合邏輯](04-combinational-logic.md) · [目錄](../README.md) · [下一章：有限狀態機 →](06-finite-state-machines.md)
