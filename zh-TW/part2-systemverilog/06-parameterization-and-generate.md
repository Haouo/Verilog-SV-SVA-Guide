# 第二部 · 6. 參數化與 generate

[← 程序區塊與運算子](05-procedural-and-operators.md) · [目錄](../README.md) · [下一章：驗證功能概覽（僅提及） →](07-verification-features-overview.md)

## 學習目標

- 宣告帶型別的 `parameter` 與 `localparam` 值。
- 使用 `$bits` 和 `$clog2` 計算衍生參數。
- 以 `for`、`if` 和具名範圍撰寫 `generate` 區塊。
- 構建參數化、可重用的設計模組。

## 設計者 mental model

parameterization 把 design choice 移到 elaboration time。parameterized module 是一個 hardware
family 的 template；`generate` 在 simulation 或 synthesis 開始前選擇或複製 structure。把 parameter
當成 module contract 的一部分：caller 選擇 legal value，module 再推導 internal width 和 instance。

危險在於 flexible module 可能變成 under-specified。每個 parameter 都應該有 meaning、range、
consequence。derived `localparam` 很重要，因為它把 caller choice 轉成穩定的 internal fact，讓
implementation 更容易讀，也更不容易誤用。

## 帶型別的參數

在 Verilog 中，參數是無型別的整數。SystemVerilog 允許參數攜帶明確的型別，從而改善錯誤檢查並記錄設計意圖。

```systemverilog
module fifo #(
    parameter int          DEPTH     = 16,    // must be positive integer
    parameter int          DATA_W    = 8,     // bit width
    parameter bit          FALL_THRU = 1'b0  // boolean flag
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic [DATA_W-1:0] wdata,
    input  logic              push,
    output logic [DATA_W-1:0] rdata,
    output logic              pop_valid
);
```

將參數型別指定為 `int` 意味著工具會檢查覆寫值是否為相容的整數。型別指定為 `bit` 則記錄了它是布林標誌。帶型別的參數能在闡述（elaboration）時就捕獲 `DEPTH = -1` 或 `FALL_THRU = 5` 這類覆寫錯誤，而非在 simulation 時才發現。

### `localparam`

`localparam` 是不能在例化時被覆寫的參數。用它表示從其他參數衍生出的常數：

```systemverilog
module fifo #(
    parameter int DEPTH  = 16,
    parameter int DATA_W = 8
) ( ... );

    localparam int PTR_W  = $clog2(DEPTH);    // pointer width
    localparam int BITS   = $bits(logic [DATA_W-1:0]) * DEPTH; // total storage

endmodule
```

`localparam` 值出現在展開的階層中，但不能被父模組更改。只對呼叫者應能覆寫的值使用 `parameter`。

## 用於參數的系統函式

### `$bits`

`$bits(expression)` 回傳一個表達式或型別的總位元數。它在闡述時求值。

```systemverilog
typedef struct packed {
    logic [15:0] addr;
    logic [31:0] data;
    logic [3:0]  byte_en;
    logic        valid;
} req_t;

localparam int REQ_BITS = $bits(req_t);   // 53
```

當下游模組必須知道一個 struct 或陣列的寬度而無需手動計算欄位時，`$bits` 是不可或缺的。

### `$clog2`

`$clog2(n)` 回傳 n 以 2 為底的對數的上取整。它是計算深度為 `n` 的記憶體所需位址位元數的標準方法。

```systemverilog
parameter int DEPTH = 1024;
localparam int ADDR_W = $clog2(DEPTH);   // 10

logic [ADDR_W-1:0] rd_addr, wr_addr;
```

`$clog2(1)` 回傳 0。對於非 2 的冪次的深度，`$clog2` 給出定址所有條目所需的最少位元數。

## `generate` 區塊

`generate` 區塊允許在闡述時進行結構性條件判斷和迴圈。它建立硬體結構，而非執行時行為。`generate` 區塊內的所有內容在 simulation 或合成開始之前就已確定。

### `generate for` — 複製結構

`genvar` 是一個闡述時的整數，用作 generate for 迴圈的迴圈變數。它不作為硬體訊號存在。

```systemverilog
module parity_tree #(
    parameter int N = 8   // number of input bits
) (
    input  logic [N-1:0] in,
    output logic         parity
);
    // Generate a reduction tree of XOR gates
    generate
        genvar i;
        for (i = 0; i < N; i++) begin : gen_xor
            if (i == 0)
                assign parity_stage[i] = in[i];
            else
                assign parity_stage[i] = parity_stage[i-1] ^ in[i];
        end
    endgenerate

    logic [N-1:0] parity_stage;
    assign parity = parity_stage[N-1];

endmodule
```

`begin : gen_xor` 標籤為 generate 範圍命名。具名範圍允許從外部以階層性引用的方式存取其中的項目：測試平台可存取 `gen_xor[3].parity_stage`。標籤是可選的，但建議使用以提升可讀性和可除錯性。

更常見的模式是例化複製的模組：

```systemverilog
module replicated_adder #(
    parameter int LANES  = 4,
    parameter int DATA_W = 8
) (
    input  logic [LANES-1:0][DATA_W-1:0] a,
    input  logic [LANES-1:0][DATA_W-1:0] b,
    output logic [LANES-1:0][DATA_W:0]   sum
);
    generate
        genvar i;
        for (i = 0; i < LANES; i++) begin : gen_add
            assign sum[i] = {1'b0, a[i]} + {1'b0, b[i]};
        end
    endgenerate

endmodule
```

四個加法器被展開，每個通道一個。參數 `LANES` 控制數量。需要 8 個通道的父模組覆寫 `LANES = 8` 即可得到 8 個加法器，無需修改模組。

### `generate if` — 條件性結構

`generate if` 在闡述時在兩種備選硬體結構之間選擇。它是闡述時的條件判斷，而非執行時的 `if`。

```systemverilog
module registered_adder #(
    parameter int  DATA_W    = 8,
    parameter bit  PIPELINED = 1'b1   // 1 = add a register stage
) (
    input  logic             clk,
    input  logic [DATA_W-1:0] a, b,
    output logic [DATA_W:0]  sum
);
    generate
        if (PIPELINED) begin : gen_pipe
            logic [DATA_W:0] sum_comb;
            always_comb  sum_comb = {1'b0, a} + {1'b0, b};
            always_ff @(posedge clk) sum <= sum_comb;
        end else begin : gen_comb
            always_comb  sum = {1'b0, a} + {1'b0, b};
        end
    endgenerate

endmodule
```

當 `PIPELINED = 1'b1` 時，工具展開 `gen_pipe` 分支並捨棄 `gen_comb`。當 `PIPELINED = 1'b0` 時，反之。產生的硬體完全不同，但模組介面保持不變。

### 省略 `generate` 關鍵字

在 SystemVerilog 中，`generate` / `endgenerate` 關鍵字是可選的。直接出現在模組本體中、帶有 `genvar` 的 `for` 迴圈或 `if` 仍然是 generate 構造。省略關鍵字是合法的，在現代程式碼中也很常見：

```systemverilog
module gray_encoder #(parameter int N = 4) (
    input  logic [N-1:0] bin,
    output logic [N-1:0] gray
);
    assign gray[N-1] = bin[N-1];

    for (genvar i = 0; i < N-1; i++) begin : gen_bits
        assign gray[i] = bin[i+1] ^ bin[i];
    end

endmodule
```

兩種風格——帶或不帶 `generate` / `endgenerate`——都是正確的。在一個專案中選擇一種並保持一致。

## 完整的參數化範例

```systemverilog
package mem_pkg;
    parameter int DEFAULT_DEPTH = 256;
    parameter int DEFAULT_WIDTH = 8;
endpackage

module sync_ram
    import mem_pkg::*;
#(
    parameter int DEPTH = DEFAULT_DEPTH,
    parameter int WIDTH = DEFAULT_WIDTH
) (
    input  logic                  clk,
    input  logic                  we,
    input  logic [$clog2(DEPTH)-1:0] waddr,
    input  logic [WIDTH-1:0]         wdata,
    input  logic [$clog2(DEPTH)-1:0] raddr,
    output logic [WIDTH-1:0]         rdata
);
    localparam int ADDR_W = $clog2(DEPTH);

    logic [WIDTH-1:0] mem [DEPTH];

    always_ff @(posedge clk) begin
        if (we)
            mem[waddr] <= wdata;
        rdata <= mem[raddr];
    end

endmodule
```

此模組適用於任何 2 的冪次深度和任何寬度。位址寬度由 `$clog2` 自動計算。參數來自套件以保持全專案一致性。

> **設計意圖。** 參數化模組是可重用的規格，而非特定的硬體。參數列表是合約：呼叫者宣告其需求，模組進行適配。`localparam` 衍生值是承諾：「給定你的 `DEPTH`，我將計算正確的位址寬度」——工具在闡述時驗證這個算術。

## 常見陷阱

- **將 `genvar` 用作執行時訊號。** `genvar` 只存在於闡述時。它不能在 generate 迴圈標頭之外的 `always` 區塊或 `assign` 敘述中使用。在程序性程式碼中請使用普通的 `int`。
- **在多敘述的 generate 本體上忘記 `begin : label`。** 若沒有 `begin / end`，只有第一個敘述在 generate 迴圈中。這和程序性程式碼中 `if` 和 `for` 的規則相同——即使只有一個敘述，在 generate 中也要加上區塊，使範圍可見。
- **對執行時條件使用 `generate if`。** 條件必須是在闡述時可求值的常數表達式。依賴執行時訊號的條件不是 generate 條件；應在 `always` 區塊中撰寫執行時的 `if`。
- **`$clog2(0)` 未定義。** 若 `DEPTH` 可能為 0，請透過斷言或參數約束確保 `DEPTH >= 1`。
- **參數型別不符。** 將負值或實數傳遞給 `int` 參數，只有在參數帶型別時才能被捕獲。若省略型別，工具可能悄悄截斷或強制轉換值。

## 小結

- 帶型別的 `parameter` 值記錄意圖並啟用闡述時的檢查。
- `localparam` 表達呼叫者無法覆寫的衍生常數。
- `$bits` 在闡述時測量任何型別的大小；`$clog2` 計算給定深度的最小位址寬度。
- `generate for` 複製結構；`generate if` 在備選方案之間選擇；兩者都在 simulation 或合成之前的闡述時確定。
- 具名的 generate 範圍（`begin : label`）改善可讀性並支援階層性引用。

---

[← 程序區塊與運算子](05-procedural-and-operators.md) · [目錄](../README.md) · [下一章：驗證功能概覽（僅提及） →](07-verification-features-overview.md)
