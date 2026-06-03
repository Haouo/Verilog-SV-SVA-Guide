# 第一部 · 2. 資料型別與數值

[← 模組與階層](01-modules-and-hierarchy.md) · [目錄](../README.md) · [下一章：運算子與運算式 →](03-operators-and-expressions.md)

## 學習目標

- 區分線網（net）與變數（variable），並知道各自的使用時機。
- 正確撰寫向量、字面值與常數。
- 理解四態值系統，以及 `x` 與 `z` 的含義。
- 使用 `parameter` 與 `localparam` 定義具位元寬度的具名常數。

## 線網與變數

Verilog 有兩類資料物件，這種區分常令初學者困惑，因為它與軟體直覺不符。

- **線網（net）**（最常見的型別是 `wire`）模擬實體連接。它不儲存數值，而是反映驅動它的訊號。線網必須被持續驅動——由模組輸出、基本邏輯元件，或 `assign` 語句。
- **變數（variable）**（Verilog 中型別為 `reg`）持有數值，直到某個程序性語句指定新值為止。儘管名稱如此，`reg` 不一定對應硬體暫存器（register）。它只是一個在 `always` 或 `initial` 區塊中被指定的變數。

可合成（synthesizable）RTL 的使用規則：

- 以 `assign` 或模組埠驅動的訊號 → 宣告為 `wire`。
- 在 `always` 區塊中指定的訊號 → 宣告為 `reg`。

```verilog
wire       enable;       // driven by assign or a port
wire [7:0] data_bus;     // an 8-bit net
reg  [7:0] count;        // assigned inside an always block
```

> 在 SystemVerilog 中，`logic` 型別放寬了這項區別，詳見第二部。在純 Verilog 中，
> 你必須正確選擇 `wire` 或 `reg`。

## 向量與位元順序

向量（vector）是多位元訊號，寫成 `[msb:lsb]`。幾乎所有慣例都以 0 作為最低有效位元（LSB）：

```verilog
wire [7:0] byte_a;       // bit 7 is MSB, bit 0 is LSB
wire [0:7] reversed;     // legal but unconventional; avoid
```

以 `byte_a[3]` 選取單一位元，以 `byte_a[3:0]` 選取範圍。部分選取（part select）的方向必須與宣告方向一致。

## 四態值系統

Verilog 訊號的每個位元攜帶四種值之一：

| 數值 | 意義 |
|---|---|
| `0` | 邏輯零 |
| `1` | 邏輯一 |
| `x` | 未知（unknown） |
| `z` | 高阻抗（high impedance），即未被驅動 |

`x` 與 `z` 是硬體建模的必要元素，它們本身並非錯誤標記。

- `z` 表示沒有任何東西驅動該線網——三態（tri-state）匯流排，或浮接輸入。
- `x` 表示數值未知——未初始化的暫存器、多重驅動衝突，或讀取未定義值的結果。

在模擬中，`x` 常指示真實的錯誤：從未被重置的暫存器，或競態（race）。遇到非預期的 `x`，應追蹤其根源，而非加以遮蔽。斷言（assertion，第三部）是在不應出現 `x` 之處捕捉它的有效手段。

## 字面值

帶位元寬度的字面值（sized literal）寫成 `width'base value`：

```verilog
8'hFF        // 8 bits, hexadecimal, value 255
4'b1010      // 4 bits, binary
8'd200       // 8 bits, decimal
8'b0000_00xx // underscores for readability; low bits unknown
'0, '1       // fill all bits with 0 or 1 (SystemVerilog)
```

進位制以 `b`、`o`、`d` 或 `h` 表示。底線會被忽略，僅用於提升可讀性。未指定寬度的字面值（如 `42`）預設為 32 位元整數；在 RTL 中請優先使用帶寬度的字面值，讓位元寬度明確。

## 常數：parameter 與 localparam

以具名常數取代魔術數字（magic number）。

- `parameter` — 父模組可在實例化時覆寫的常數（見第 1 章）。
- `localparam` — 不可被覆寫的常數。用於從 parameter 衍生出的數值，或固定的內部常數，例如狀態編碼。

```verilog
module fifo #(
    parameter int DEPTH = 16
) (/* ports */);
    localparam int ADDR_W = $clog2(DEPTH);  // derived, not overridable
    reg [ADDR_W-1:0] rd_ptr, wr_ptr;
endmodule
```

以 `localparam` 衍生 `ADDR_W` 能使位址寬度自動與 `DEPTH` 保持一致。若有人修改 `DEPTH`，指標的寬度也會隨之調整。

> **設計意圖。** 位元寬度是對範圍的陳述：「這個數值永遠不需要超過 `ADDR_W` 位元。」
> 以 `localparam` 命名它，記錄了這個意圖，並讓所有相依訊號保持一致。
> 魔術數字把同一個決策散佈在整個檔案各處，使各副本逐漸偏離。

## 常見陷阱

- **線網與變數選擇錯誤。** 在 `always` 中指定 `wire`，或對 `reg` 使用 `assign`，都是錯誤。請依訊號的驅動方式選擇型別。
- **把 `reg` 當作硬體暫存器。** 它只是一個變數；是否成為正反器（flip-flop）取決於*如何*指定它（第 5 章），而非關鍵字本身。
- **RTL 中使用未指定寬度的字面值。** 預設為 32 位元，會在運算式中產生意外的寬度。請使用帶寬度的字面值。
- **忽略 `x`。** 非預期的 `x` 通常意味著遺漏重置或競態，而非外觀問題。請追蹤它。

## 小結

- 線網（`wire`）攜帶被驅動的值；變數（`reg`）持有被指定的值。
- 向量使用 `[msb:lsb]`，慣例上 LSB 為 0。
- 四種狀態 `0 1 x z` 模擬真實硬體；非預期的 `x` 意味著問題。
- 撰寫帶寬度的字面值，並以 `parameter` / `localparam` 命名常數。

---

[← 模組與階層](01-modules-and-hierarchy.md) · [目錄](../README.md) · [下一章：運算子與運算式 →](03-operators-and-expressions.md)
