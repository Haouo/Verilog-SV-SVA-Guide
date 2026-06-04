# 第二部 · 5. 程序區塊與運算子

[← 介面與 modport](04-interfaces-and-modports.md) · [目錄](../README.md) · [下一章：參數化與 generate →](06-parameterization-and-generate.md)

## 學習目標

- 在可合成的情境中使用 `do-while`、`foreach`、`break` 和 `continue`。
- 應用 `++`、`--`、`+=`、`-=` 及其他簡寫指定運算子。
- 用 `case inside` 做萬用字元樣式比對。
- 以靜態型別轉換 `'` 和 `$cast` 正確轉換型別。
- 知道哪些語法構件可合成，哪些只能用於 simulation。

## 設計者的心智模型

SystemVerilog 的程序語法在能減少枝節細節時才有價值。內嵌的迴圈變數、`foreach`、型別轉換、簡寫指定、`case inside`，都可能比舊有的 Verilog 寫法更清楚地表達你想做的運算。好的用法不只是讓程式碼變短，而是讓程式碼的結構貼合你要描述的決策或資料搬移。

正因為這些構件更有表達力，也就更值得審慎檢視。要問自己：這個 cast 是在記錄一次真正的轉換，還是只為了壓掉型別警告？這個簡寫指定對這個區塊的 timing 安全嗎？這個 `case inside` 是在表達真實的樣式，還是把本該檢查的 don't-care 行為藏了起來？

## 強化的迴圈構造

### `do-while`

`do-while` 會先執行一次迴圈本體，再測試條件。在可合成的程式碼中，迴圈必須有靜態可確定的邊界，因為合成工具會把迴圈展開。當邊界在闡述（elaboration）時就已靜態確定，`do-while` 即可合成。

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

實務上，RTL 裡 `for` 更常見，因為它的邊界在構件開頭就一目瞭然。只有在第一次迭代必須無條件執行時，才用 `do-while`。

### `foreach`

`foreach` 會走訪陣列的每個元素，並自動處理索引範圍，是處理陣列最清晰的寫法：

```systemverilog
logic [7:0] data [16];
logic [7:0] xor_all;

always_comb begin
    xor_all = '0;
    foreach (data[i])
        xor_all ^= data[i];
end
```

用於多維陣列時，`foreach` 會走訪所有維度：

```systemverilog
logic [3:0][7:0] matrix [4];   // 4 unpacked elements, each 4×8 packed

always_comb begin
    foreach (matrix[i, j, k])
        // i: unpacked index, j: outer packed, k: inner packed
        processed[i][j][k] = matrix[i][j][k];
end
```

### `break` 與 `continue`

`break` 會立即跳出最內層迴圈，`continue` 則跳到下一次迭代。只要迴圈有靜態邊界，兩者在 `for` 和 `foreach` 迴圈中都可合成，因為工具展開迴圈後，會把條件求值成組合邏輯。

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

注意：合成後的迴圈裡，`break` 不會在執行時縮短迴圈。工具會展開每一次迭代，並為提前退出插入條件邏輯。硬體仍執行所有迭代，只是忽略 break 條件成立之後的結果。這個行為是正確的，但要知道：跟完整展開的迴圈相比，`break` 並不省面積，只是讓意圖更清晰。

## 簡寫指定運算子

SystemVerilog 新增了 C 風格的簡寫指定，這些全都可合成。

| 運算子 | 含義 |
|--------|------|
| `a++` | `a = a + 1`（後置遞增） |
| `++a` | `a = a + 1`（前置遞增） |
| `a--` | `a = a - 1`（後置遞減） |
| `--a` | `a = a - 1`（前置遞減） |
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

在帶時脈的區塊中，請用非阻塞式指定 `<=` 的明確形式：寫 `count <= count + 1`，而非 `count++`。`++` 一律是阻塞式更新，沒有非阻塞的形式，所以在 `always_ff` 中要寫出完整的指定式。組合邏輯的迴圈變數本來就用阻塞式指定，遞增記號在那裡很清楚，可以保留。

## `case inside`

普通的 `case` 敘述只比對精確的值。`case inside` 在此基礎上加入萬用字元樣式，用 `?` 表示不在意的位元（don't-care bit）。這個寫法可合成。

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

`unique` 和 `priority` 用在 `case inside` 上的行為，和用在普通 `case` 上完全一樣。當各樣式互不重疊且涵蓋完整時，用 `unique case inside`。

## 型別轉換

### 靜態型別轉換 `'`

靜態型別轉換運算子 `'` 在編譯時把一個值轉成目標型別，是可合成程式碼裡主要的轉換機制。

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

靜態轉換套用在常數上時於闡述時求值，套用在執行時的值上時則在指定當下求值。合成工具會把它對應成連線：截斷、擴展或重新解讀，不會產生邏輯閘。

### `$cast`

`$cast` 是動態型別轉換，主要用於 simulation 和驗證。對 enum 型別來說，它會把來源指定給目標，若該值是合法的 enum 成員就回傳 1，否則回傳 0。

```systemverilog
state_t next;
logic [1:0] encoded;
bit ok;

// ok == 0 if encoded is not a valid state_t member
ok = $cast(next, encoded);
```

`$cast` 不可合成。設計程式碼裡請改用靜態型別轉換 `state_t'(v)`，並靠 `unique case` 搭配斷言（Part III）來偵測非法值。`$cast` 留給測試平台用。

## 有號算術

SystemVerilog 的運算元預設無號。要控制算術中的符號擴展，用 `signed` 關鍵字或 `$signed` / `$unsigned` 系統函式：

```systemverilog
logic [7:0]  a, b;
logic [8:0]  sum_u;  // unsigned
logic signed [8:0] sum_s; // signed

sum_u = {1'b0, a} + {1'b0, b};           // unsigned addition
sum_s = $signed({1'b0, a}) + $signed({1'b0, b}); // treat as signed
```

在合成裡，有號和無號算術對應到同一個加法器，只差在進位/溢位位元的解讀。運算式中有號性不一致是細微錯誤的常見來源，請明確標示。

> **設計意圖。** 帶萬用字元樣式的 `case inside`，記錄了某些位元對這個決策確實無關緊要，這是硬體編碼上的選擇，不是 simulation 的方便手段。`unique` 修飾詞則檢查其餘位元是否完全確定。兩者合在一起，表達出一份精確、且工具可驗證的解碼器規格。

## 常見陷阱

- **以為 `break` 能省功耗或面積。** 合成時迴圈會展開，所有迭代都當成組合邏輯執行，`break` 不會讓硬體短路。它能讓意圖更清晰，也可能幫合成識別出你預期的結構，但別指望它來縮減面積。
- **在帶時脈的區塊裡用 `++`。** `always_ff` 中請寫 `count <= count + 1`，不要硬湊 `count++` 的非阻塞形式。明確的非阻塞指定才是正確又可移植的寫法。
- **在可合成 RTL 裡用 `$cast`。** 它只能用於 simulation。設計程式碼請用靜態型別轉換 `type'(value)`。
- **在 `case inside` 用了重疊樣式還加 `unique`。** 若兩個樣式可能匹配同一筆輸入，就違反了 `unique`，simulator 會發出警告。宣告 `unique` 之前，請先檢查所有樣式是否有重疊。
- **比較時忽略有號性。** 把 `logic signed [7:0] a` 跟無號的 `logic [7:0] b` 比較，會套用無號比較規則。要正確做有號比較，兩個運算元必須是相同有號性的型別。

## 小結

- `do-while` 和 `foreach` 提升了迴圈的表達力；只要邊界是靜態的，兩者都可合成。
- `break` 和 `continue` 在靜態邊界的迴圈裡可合成；它們會變成條件邏輯，而非短路硬體。
- 簡寫運算子（`++`、`+=` 等）可合成，也能改善可讀性；帶時脈的區塊請用 `<=` 形式。
- `case inside` 加入了萬用字元（`?`）和範圍（`[lo:hi]`）樣式；結合 `unique` 可建出涵蓋完整、互不重疊的解碼器。
- 可合成程式碼用靜態型別轉換 `type'(v)`；`$cast` 留給測試平台。

---

[← 介面與 modport](04-interfaces-and-modports.md) · [目錄](../README.md) · [下一章：參數化與 generate →](06-parameterization-and-generate.md)
