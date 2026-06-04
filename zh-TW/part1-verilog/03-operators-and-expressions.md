# 第一部 · 3. 運算子與運算式

[← 資料型別與數值](02-data-types-and-values.md) · [目錄](../README.md) · [下一章：組合邏輯 →](04-combinational-logic.md)

## 學習目標

- 正確使用各主要運算子群組。
- 理解 Verilog 如何決定運算元的寬度與延伸方式。
- 知道位元運算與邏輯運算的差異，以及 `==` 與 `===` 的不同。
- 避免常見的寬度與有號數陷阱。

## 設計者 mental model

expression 是一小段 hardware network。operator 選擇 gate，reduction 把 vector 壓成較少的
bit，concatenation 負責 bit routing，comparison 則決定 unknown 如何參與。讀 expression 時
先當 hardware 看，再看 syntax：哪些 bit 進來、幾個 bit 出去、`x` 或 signedness 會不會改變結果。

這也是 simulation 與 synthesis 容易悄悄偏離 intent 的地方。simulator 會忠實套用 language 的
sizing 與 four-state rule，但那不一定是 designer 腦中想的 rule。好的 RTL 會把 width 與
signedness 寫得足夠明確，讓 expression 看起來就像你真的要建的 hardware。

## 運算子群組

Verilog 運算子分為幾個群組。在 RTL 中最常用的如下：

| 群組 | 運算子 |
|---|---|
| 算術 | `+ - * / %` |
| 位元 | `~ & \| ^ ^~` |
| 縮減 | `& ~& \| ~\| ^ ~^`（一元） |
| 邏輯 | `! && \|\|` |
| 關係 | `< <= > >=` |
| 相等 | `== != === !==` |
| 移位 | `<< >> <<< >>>` |
| 串接 | `{ }` 與複製 `{N{ }}` |
| 條件 | `? :` |

### 位元運算與邏輯運算

這點常使初學者混淆。位元運算子逐位元運算，回傳向量；邏輯運算子將整個運算元視為真/假，回傳單一位元。

```verilog
4'b1100 & 4'b1010   // bitwise AND -> 4'b1000
4'b1100 && 4'b1010  // logical AND -> 1'b1 (both are nonzero, so true)
```

合併位元時使用 `&`/`|`；合併條件時使用 `&&`/`||`。

### 縮減運算子

一元縮減（reduction）運算子對向量的所有位元套用該運算，將其折疊為一個位元：

```verilog
&data   // 1 if every bit of data is 1
|data   // 1 if any bit is 1 (data is nonzero)
^data   // parity: 1 if an odd number of bits are 1
```

這些寫法精簡且合成效果佳——`&data` 是全一檢查，無需字面值比較。

## 串接與複製

大括號用於串接訊號；`{N{x}}` 將 `x` 重複 N 次。

```verilog
{a, b}           // a in the high bits, b in the low bits
{4{1'b1}}        // 4'b1111
{byte_a[7], byte_a}  // sign-extend an 8-bit value to 9 bits
```

串接（concatenation）是建構與切割匯流排的標準工具。

## 寬度、延伸與上下文規則

Verilog 運算式具有寬度，且由上下文決定。這是錯誤的常見來源。要記住兩條規則：

1. 在指定（assignment）中，運算元會延伸（或截斷）至最寬運算元*與*左側目標的寬度。這稱為「由上下文決定」的寬度。
2. 無號運算元以零延伸；有號運算元以符號延伸。

```verilog
reg [7:0]  a;
reg [3:0]  b;
reg [7:0]  c;
c = a + b;   // b is zero-extended to 8 bits before the add
```

常見錯誤是中間結果溢位，原因是運算式寬度由較窄的運算元決定。有疑慮時，請明確指定寬度。

## 相等比較：`==` 與 `===`

- `==` 與 `!=` 是*邏輯*相等。若任一運算元含有 `x` 或 `z` 位元，結果為 `x`（未知），而非 0 或 1。
- `===` 與 `!==` 是*case* 相等。它們逐位元比較 `x` 與 `z`，並且總是回傳確定的 0 或 1。

```verilog
4'b1x10 == 4'b1x10   // x  (unknown, because of the x bit)
4'b1x10 === 4'b1x10  // 1  (exact match including the x)
```

在可合成 RTL 中請使用 `==`——`===` 不可合成，因為真實硬體沒有 `x`。`===` 適用於測試平台（testbench）與斷言中，用於對 `x`/`z` 進行檢查。

## 有號算術

線網與 `reg` 預設為無號。當需要二補數（two's-complement）算術與符號延伸時，請宣告 `signed`：

```verilog
reg signed [7:0] s;
wire signed [7:0] diff = s - 8'sd1;   // signed literal: 8'sd1
```

混用有號與無號運算元遵循嚴格規則，且常出乎意料：若*任何*運算元為無號，則整個運算視為無號。在運算式中保持有號性一致，並在表示有號常數時使用 `'s` 字面值形式。

> **設計意圖。** 運算式的寬度與有號性是意圖的一部分：
> 「這個加法器是 8 位元無號」、「這個差值是有號的。」
> Verilog 從上下文推斷兩者，因此當推斷不明顯時，請以帶寬度的有號字面值
> 與中間訊號明確陳述。讀者——以及合成工具——不應猜測。

## 常見陷阱

- **用位元運算取代邏輯運算，或反之。** `&` 不等於 `&&`。
- **靜默截斷。** 將寬運算式指定給窄目標時，高位元會被丟棄且不發出警告。請刻意指定中間訊號的寬度。
- **對 `x`/`z` 使用 `==`。** 會回傳 `x` 並向外傳播。僅在非可合成程式碼中，確實需要比較 `x`/`z` 時才使用 `===`。
- **意外的無號算術。** 一個無號運算元使整個運算式成為無號。留意減法時的符號延伸。

## 小結

- 熟悉各運算子群組；不要混淆位元運算與邏輯運算。
- 縮減運算子將向量折疊為一個位元，且合成乾淨。
- 運算式寬度由上下文決定；截斷與延伸是靜默發生的。
- RTL 中使用 `==`；僅在測試平台/斷言中進行 `x`/`z` 檢查時使用 `===`。

---

[← 資料型別與數值](02-data-types-and-values.md) · [目錄](../README.md) · [下一章：組合邏輯 →](04-combinational-logic.md)
