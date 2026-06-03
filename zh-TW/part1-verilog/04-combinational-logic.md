# 第一部 · 4. 組合邏輯

[← 運算子與運算式](03-operators-and-expressions.md) · [目錄](../README.md) · [下一章：循序邏輯 →](05-sequential-logic.md)

## 學習目標

- 以 `assign` 與 `always` 描述組合邏輯（combinational logic）。
- 以 `always @*` 撰寫正確的敏感度列表（sensitivity list）。
- 在不推斷閂鎖器（latch）的前提下使用 `if` 與 `case`。
- 理解 `full_case` / `parallel_case` 並知道為何應避免使用。

## 組合邏輯的兩種寫法

組合邏輯的輸出僅取決於當前輸入，不含任何狀態。Verilog 提供兩種風格。

### 連續指定

`assign` 從一個運算式持續驅動線網，是簡單邏輯的自然選擇。

```verilog
assign y     = a & b;
assign sum   = a + b;
assign mux_o = sel ? in1 : in0;
```

### 程序式組合邏輯

對於含有 `if`/`case` 結構的邏輯，請使用 `always` 區塊。在純 Verilog 中，這是以 `always @*` 驅動 `reg` 變數。

```verilog
reg [3:0] result;
always @* begin
    if (op == 2'b00)      result = a + b;
    else if (op == 2'b01) result = a - b;
    else                  result = a & b;
end
```

目標雖是 `reg`（見第 2 章），但這仍是組合邏輯，而非暫存器——這裡沒有時脈。

## 敏感度列表

`always @*`（等同於 `always @(*)`）告訴工具：當該區塊所讀取的*任何*訊號變化時，觸發此區塊。組合邏輯應一律使用它。舊式的手動列舉訊號方式——`always @(a or b or sel)`——容易出錯：遺漏一個訊號，模擬結果便不再與合成（synthesis）結果一致，因為合成工具無論如何都會建構組合邏輯，不受你的列表影響。

```verilog
// Good: complete sensitivity, by construction
always @* begin ... end

// Bad: hand-listed, easy to get wrong
always @(a or b) begin
    result = a + b + c;   // c is missing -> simulation mismatch
end
```

## 避免閂鎖器

這是組合 `always` 區塊最核心的危險。若某變數在區塊的*某條路徑上未被指定*，工具就必須保持其先前的值——這意味著它推斷出一個閂鎖器（latch）。RTL 中的閂鎖器幾乎都是錯誤：它們製造時序問題，通常也意味著描述不完整。

```verilog
// Latch inferred: result is not assigned when en is 0
always @* begin
    if (en) result = a + b;
end
```

兩種可靠的修正方式：

1. **先指定預設值**，再覆寫：

   ```verilog
   always @* begin
       result = 4'b0000;        // default covers every path
       if (en) result = a + b;
   end
   ```

2. **讓每個分支都指定每個輸出**，包括最終的 `else` 與 `case` 中的 `default`。

無論哪種方式，規則都很簡單：組合區塊的每個輸出，在每條路徑上都必須獲得一個值。

## `case` 語句

`case` 是表達多路選擇的清晰方式，例如多工器（multiplexer）或解碼器（decoder）。務必包含 `default`。

```verilog
always @* begin
    case (sel)
        2'b00: y = in0;
        2'b01: y = in1;
        2'b10: y = in2;
        2'b11: y = in3;
        default: y = 1'bx;   // unreachable here, but defends against x on sel
    endcase
end
```

當 `sel` 可能為 `x`（例如在重置傳播期間），將 `y` 送到已知值——或送到 `x` 以暴露問題——的 `default` 分支既能防止閂鎖器，也讓意圖明確。

`casez` 將 `z`/`?` 位元視為 don't-care，適用於優先解碼器（priority decoder）。`casex` 也將 `x` 視為 don't-care，可能遮蔽錯誤——請優先使用 `casez`。

## `full_case` 與 `parallel_case`

這些是你會在舊有程式碼中看到的合成 pragma：

- `full_case` 宣稱所有可能的 `case` 值都已涵蓋。
- `parallel_case` 宣稱各項目是互斥的。

兩者都應避免。它們告訴合成工具假設某些模擬器不假設的事，導致模擬與合成產生分歧——這正是斷言（assertion）存在所要捕捉的不一致。請改為撰寫帶有明確 `default` 的完整 `case`，讓工具看到真實情況。

> **設計意圖。** 組合區塊的本意是成為輸入的純函數。
> 閂鎖器透過引入隱藏狀態打破了這個意圖。
> `always @*`、預設指定、每個 `case` 中的 `default`——這套紀律
> 就是你表達「這是純組合邏輯」的方式，讓工具確實建構出你所想要的。

## 常見陷阱

- **指定不完整 → 推斷出閂鎖器。** 在每條路徑上指定每個輸出。
- **手動撰寫敏感度列表。** 請使用 `always @*`。
- **缺少 `case` 的 `default`。** 可能推斷出閂鎖器，並隱藏選擇器上的 `x`。
- **`full_case`/`parallel_case` pragma。** 它們導致模擬/合成不一致。請改寫完整的 `case` 語句。
- **`casex`。** 它將 `x` 視為 don't-care，可能隱藏真實錯誤；請使用 `casez`。

## 小結

- 簡單邏輯使用 `assign`；含 `if`/`case` 邏輯使用 `always @*`。
- `always @*` 自動提供完整的敏感度列表。
- 在每條路徑上指定每個輸出，以避免推斷出閂鎖器。
- 撰寫帶有 `default` 的完整 `case` 語句；避免使用 case pragma。

---

[← 運算子與運算式](03-operators-and-expressions.md) · [目錄](../README.md) · [下一章：循序邏輯 →](05-sequential-logic.md)
