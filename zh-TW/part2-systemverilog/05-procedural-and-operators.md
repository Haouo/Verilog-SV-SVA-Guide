# 第二部 · 5. 程序區塊與運算子

[← 介面與 modport](04-interfaces-and-modports.md) · [目錄](../README.md) · [下一章：參數化與 generate →](06-parameterization-and-generate.md)

## 學習目標

- 在可合成的情境中使用 `do-while`、`foreach`、`break` 和 `continue`。
- 應用 `++`、`--`、`+=`、`-=` 及其他簡寫指定運算子。
- 使用 `case inside` 進行萬用字元樣式比對。
- 以靜態型別轉換 `'` 和 `$cast` 正確轉換型別。
- 了解哪些構造是可合成的，哪些僅用於模擬。

## 強化的迴圈構造

### `do-while`

`do-while` 在測試條件之前至少執行一次迴圈本體。在可合成程式碼中，迴圈必須有靜態可確定的邊界——合成工具會展開迴圈。當邊界在闡述（elaboration）時靜態已知，`do-while` 是可合成的。

```systemverilog
// Synthesizable: bound is known at elaboration
int i;
always_comb begin
    i = 0;
    do begin
        result[i] = in_data[i] ^ key[i];
        i++;
    end while (i < 8);
end
```

實際上，在 RTL 中 `for` 更為常見，因為它的邊界在構造頂端就一目瞭然。當第一次迭代必須無論條件如何都執行時，使用 `do-while`。

### `foreach`

`foreach` 迭代陣列的每個元素。它自動處理索引範圍，是處理陣列最清晰的方式：

```systemverilog
logic [7:0] data [16];
logic [7:0] xor_all;

always_comb begin
    xor_all = '0;
    foreach (data[i])
        xor_all ^= data[i];
end
```

`foreach` 用於多維陣列時，會迭代所有維度：

```systemverilog
logic [3:0][7:0] matrix [4];   // 4 unpacked elements, each 4×8 packed

always_comb begin
    foreach (matrix[i, j, k])
        // i: unpacked index, j: outer packed, k: inner packed
        processed[i][j][k] = matrix[i][j][k];
end
```

### `break` 與 `continue`

`break` 立即退出最內層迴圈。`continue` 跳至下一次迭代。當迴圈有靜態邊界時，兩者在 `for` 和 `foreach` 迴圈中都是可合成的，因為工具展開迴圈後會將條件求值為組合邏輯。

```systemverilog
// Find first set bit — synthesizable because the loop bound is static
logic [7:0]  in;
logic [2:0]  first_bit;
logic        found;

always_comb begin
    first_bit = '0;
    found     = 1'b0;
    for (int i = 0; i < 8; i++) begin
        if (!found && in[i]) begin
            first_bit = i[2:0];
            found     = 1'b1;
        end
    end
end
```

注意：合成迴圈中的 `break` 不會在執行時縮短迴圈；工具展開每次迭代，並為提前退出插入條件邏輯。硬體執行所有迭代，只是忽略 break 條件滿足後的結果。這是正確的行為，但需要知道：`break` 與完整展開的迴圈相比，並不節省面積——它只是讓意圖更清晰。

## 簡寫指定運算子

SystemVerilog 新增了 C 風格的簡寫指定。所有這些都是可合成的。

| 運算子 | 含義 |
|--------|------|
| `a++`    | `a = a + 1`（後置遞增） |
| `++a`    | `a = a + 1`（前置遞增） |
| `a--`    | `a = a - 1`（後置遞減） |
| `--a`    | `a = a - 1`（前置遞減） |
| `a += b` | `a = a + b` |
| `a -= b` | `a = a - b` |
| `a *= b` | `a = a * b` |
| `a /= b` | `a = a / b` |
| `a &= b` | `a = a & b` |
| `a \|= b`| `a = a \| b` |
| `a ^= b` | `a = a ^ b` |
| `a <<= b`| `a = a << b` |
| `a >>= b`| `a = a >> b` |

```systemverilog
always_comb begin
    sum   = '0;
    carry = '0;
    for (int i = 0; i < 8; i++) begin
        sum += data[i];   // accumulate
    end
end
```

在帶時脈的區塊中，使用非阻塞式指定 `<=` 的明確形式：`count <= count + 1`，而非 `count++`。在組合邏輯迴圈變數的阻塞式指定情境中，遞增記號是清晰的；在 `always_ff` 中請使用明確形式。

## `case inside`

普通的 `case` 敘述只匹配精確的值。`case inside` 以萬用字元樣式擴展了這一點，使用 `?` 表示不在意的位元（don't-care bit）。這是可合成的。

```systemverilog
logic [3:0] opcode;
logic       is_branch;

always_comb begin
    unique case (opcode) inside
        4'b0???: is_branch = 1'b0;   // opcodes 0xxx: not a branch
        4'b10??: is_branch = 1'b1;   // opcodes 10xx: branch
        4'b1100: is_branch = 1'b0;   // specific non-branch
        4'b1101: is_branch = 1'b1;   // specific branch
        default: is_branch = 1'b0;
    endcase
end
```

`case inside` 也接受帶有 `[lo:hi]` 語法的範圍：

```systemverilog
unique case (count) inside
    [0:7]:   group = 2'd0;
    [8:15]:  group = 2'd1;
    [16:23]: group = 2'd2;
    default: group = 2'd3;
endcase
```

`unique` 和 `priority` 與 `case inside` 的工作方式和與普通 `case` 完全相同。當樣式不重疊且完整時，使用 `unique case inside`。

## 型別轉換

### 靜態型別轉換 `'`

靜態型別轉換運算子 `'` 在編譯時將一個值轉換為目標型別。它是可合成程式碼中的主要轉換機制。

```systemverilog
typedef enum logic [1:0] {IDLE=2'd0, RUN=2'd1, DONE=2'd2} state_t;
state_t state;
logic [1:0] raw;

// Cast a logic value to an enum type
state = state_t'(raw);

// Cast a wider value to a narrower type (truncation)
logic [7:0]  byte_val;
logic [3:0]  nibble;
nibble = 4'(byte_val);        // static width cast, takes low 4 bits

// Sign extension
logic signed [15:0] s16;
logic        [7:0]  u8;
s16 = 16'(signed'(u8));      // sign-extend 8-bit unsigned to 16-bit signed
```

靜態轉換應用於常數時在闡述時求值，應用於執行時值時在指定點求值。合成工具將其對應到連線（截斷、擴展、重新解讀——無邏輯閘）。

### `$cast`

`$cast` 是動態型別轉換，主要用於模擬和驗證。對於 enum 型別，它將來源指定給目標，若值是合法的 enum 成員則回傳 1，否則回傳 0。

```systemverilog
state_t next;
logic [1:0] encoded;
bit ok;

// ok == 0 if encoded is not a valid state_t member
ok = $cast(next, encoded);
```

`$cast` 不可合成。在設計程式碼中，使用靜態型別轉換 `state_t'(v)`，並依靠 `unique case` 加上斷言（Part III）來偵測非法值。將 `$cast` 保留給測試平台。

## 有號算術

SystemVerilog 的運算元預設為無號。使用 `signed` 關鍵字或 `$signed` / `$unsigned` 系統函式來控制算術中的符號擴展：

```systemverilog
logic [7:0]  a, b;
logic [8:0]  sum_u;  // unsigned
logic signed [8:0] sum_s; // signed

sum_u = {1'b0, a} + {1'b0, b};           // unsigned addition
sum_s = $signed({1'b0, a}) + $signed({1'b0, b}); // treat as signed
```

在合成中，有號和無號算術對應到相同的加法器；只有進位/溢位位元的解讀不同。表達式中有號性不一致是細微錯誤的常見來源——請明確標示。

> **設計意圖。** 帶萬用字元樣式的 `case inside` 記錄了某些位元對決策確實不相關——這是硬體編碼決策，而非模擬上的便利。`unique` 修飾詞檢查其餘位元是否完整確定。兩者合在一起，表達了一個精確的、工具可驗證的解碼器規格。

## 常見陷阱

- **使用 `break` 期望節省功耗或面積。** 在合成中，迴圈展開意味著所有迭代都作為組合邏輯執行。`break` 不會使硬體短路。它能讓意圖更清晰，可能幫助合成識別預期的結構，但請勿依賴它來減少面積。
- **在帶時脈的區塊中應用 `++`。** 在 `always_ff` 中請使用 `count <= count + 1`，而非試圖用 `count++` 的非阻塞形式。明確的非阻塞指定是正確且可攜的形式。
- **在可合成 RTL 中使用 `$cast`。** 它僅用於模擬。在設計程式碼中使用靜態型別轉換 `type'(value)`。
- **在 `case inside` 中使用重疊樣式並加上 `unique`。** 若兩個樣式可能匹配相同的輸入，則違反了 `unique`，模擬器會發出警告。在宣告 `unique` 之前，請檢查所有樣式的重疊情況。
- **忽視比較中的有號性。** 將 `logic signed [7:0] a` 與 `logic [7:0] b`（無號）比較時，會套用無號比較規則。要進行正確的有號比較，兩個運算元必須是相同的有號性型別。

## 小結

- `do-while` 和 `foreach` 擴展了迴圈的表達能力；當邊界是靜態的，兩者都可合成。
- `break` 和 `continue` 在靜態邊界迴圈中可合成；它們成為條件邏輯，而非短路硬體。
- 簡寫運算子（`++`、`+=` 等）可合成且改善可讀性；在帶時脈的區塊中使用 `<=` 形式。
- `case inside` 新增萬用字元（`?`）和範圍（`[lo:hi]`）樣式；結合 `unique` 構建完整的、不重疊的解碼器。
- 在可合成程式碼中使用靜態型別轉換 `type'(v)`；將 `$cast` 保留給測試平台。

---

[← 介面與 modport](04-interfaces-and-modports.md) · [目錄](../README.md) · [下一章：參數化與 generate →](06-parameterization-and-generate.md)
