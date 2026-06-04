# 第二部 · 6. 參數化與 generate

[← 程序區塊與運算子](05-procedural-and-operators.md) · [目錄](../README.md) · [下一章：驗證功能概覽（僅提及） →](07-verification-features-overview.md)

## 學習目標

- 宣告帶型別的 `parameter` 與 `localparam` 值。
- 使用 `$bits` 和 `$clog2` 計算衍生參數。
- 以 `for`、`if` 和具名範圍撰寫 `generate` 區塊。
- 構建參數化、可重用的設計模組。

## 設計者的心智模型

參數化把設計上的選擇移到闡述（elaboration）階段決定。參數化模組是某一族硬體的範本，`generate` 則在 simulation 或合成開始前，先選定或複製出結構。可以把參數看成模組合約的一部分：呼叫者挑選合法的值，模組再據此推導內部的位元寬與例化。

風險在於，過度彈性的模組可能變得規格不足。每個參數都應該有明確的意義、範圍與後果。衍生的 `localparam` 很重要，因為它把呼叫者的選擇轉成穩定的內部事實，讓實作更好讀，也更不容易誤用。

## 帶型別的參數

在 Verilog 中，參數是無型別的整數。SystemVerilog 允許參數帶有明確的型別，藉此強化錯誤檢查，也記錄了設計意圖。

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

把參數型別定為 `int`，工具就會檢查覆寫的值是否為相容的整數；定為 `bit` 則記錄了它是個布林標誌。帶型別的參數能在闡述（elaboration）時就抓到 `DEPTH = -1` 或 `FALL_THRU = 5` 這類覆寫錯誤，不必等到 simulation 才發現。

### `localparam`

`localparam` 是例化時不能被覆寫的參數。用它來表示由其他參數衍生出的常數：

```systemverilog
module fifo #(
    parameter int DEPTH  = 16,
    parameter int DATA_W = 8
) ( ... );

    localparam int PTR_W  = $clog2(DEPTH);    // pointer width
    localparam int BITS   = $bits(logic [DATA_W-1:0]) * DEPTH; // total storage

endmodule
```

`localparam` 的值會出現在展開後的階層中，但父模組無法更動。只有呼叫者該能覆寫的值，才用 `parameter`。

## 用於參數的系統函式

### `$bits`

`$bits(expression)` 回傳一個運算式或型別的總位元數，於闡述時求值。

```systemverilog
typedef struct packed {
    logic [15:0] addr;
    logic [31:0] data;
    logic [3:0]  byte_en;
    logic        valid;
} req_t;

localparam int REQ_BITS = $bits(req_t);   // 53
```

當下游模組需要知道某個 struct 或陣列的寬度，又不想手動數欄位時，`$bits` 不可或缺。

### `$clog2`

`$clog2(n)` 回傳 n 以 2 為底取對數後的上取整值，是計算深度為 `n` 的記憶體所需位址位元數的標準做法。

```systemverilog
parameter int DEPTH = 1024;
localparam int ADDR_W = $clog2(DEPTH);   // 10

logic [ADDR_W-1:0] rd_addr, wr_addr;
```

`$clog2(1)` 回傳 0。深度不是 2 的冪次時，`$clog2` 會給出定址所有條目所需的最少位元數。

## `generate` 區塊

`generate` 區塊讓你在闡述時做結構上的條件判斷與迴圈。它建立的是硬體結構，不是執行時的行為。`generate` 區塊裡的一切，都在 simulation 或合成開始前就已定案。

### `generate for` — 複製結構

`genvar` 是闡述時的整數，當作 generate for 迴圈的迴圈變數使用。它不會以硬體訊號的形式存在。

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

`begin : gen_xor` 這個標籤為 generate 範圍命名。具名範圍讓外部可以用階層引用的方式存取裡頭的項目：測試平台便能存取 `gen_xor[3].parity_stage`。標籤可加可不加，但為了可讀性與可除錯性，建議加上。

更常見的做法是例化複製出來的模組：

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

這裡展開出四個加法器，每個通道一個，數量由參數 `LANES` 控制。需要 8 個通道的父模組，只要把 `LANES` 覆寫成 8，就能得到 8 個加法器，不必改動模組。

### `generate if` — 條件性結構

`generate if` 在闡述時於兩種備選硬體結構之間做選擇。它是闡述時的條件判斷，不是執行時的 `if`。

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

當 `PIPELINED = 1'b1` 時，工具展開 `gen_pipe` 分支，捨棄 `gen_comb`；`PIPELINED = 1'b0` 時則相反。產生的硬體截然不同，但模組介面維持一致。

### 省略 `generate` 關鍵字

在 SystemVerilog 中，`generate` / `endgenerate` 關鍵字可加可不加。直接寫在模組本體裡、帶有 `genvar` 的 `for` 迴圈或 `if`，仍然是 generate 構件。省略關鍵字是合法的，在現代程式碼中也很常見：

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

兩種寫法都正確：帶或不帶 `generate` / `endgenerate` 皆可。在同一個專案裡選定一種，並保持一致。

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

這個模組適用於任何 2 的冪次深度與任何寬度，位址寬度由 `$clog2` 自動算出。參數取自套件，以維持全專案一致。

> **設計意圖。** 參數化模組是一份可重用的規格，而不是某一塊特定的硬體。參數列表就是合約：呼叫者宣告自己的需求，模組隨之適配。`localparam` 衍生值則是一種承諾，等於在說「給我你的 `DEPTH`，我就算出正確的位址寬度」，而這段算術由工具在闡述時驗證。

## 常見陷阱

- **把 `genvar` 當執行時訊號用。** `genvar` 只在闡述時存在。除了 generate 迴圈標頭，它不能用在 `always` 區塊或 `assign` 敘述裡。程序性程式碼請改用普通的 `int`。
- **多敘述的 generate 本體忘了加 `begin : label`。** 少了 `begin / end`，只有第一個敘述會落在 generate 迴圈裡。這和程序性程式碼中 `if`、`for` 的規則一樣：即使只有一個敘述，generate 裡也要加上區塊，好讓範圍清楚可見。
- **對執行時條件用 `generate if`。** 條件必須是闡述時可求值的常數運算式。會隨執行時訊號變動的條件並不是 generate 條件；那種情況請在 `always` 區塊裡寫執行時的 `if`。
- **`$clog2(0)` 沒有定義。** 若 `DEPTH` 有可能為 0，請用斷言或參數約束確保 `DEPTH >= 1`。
- **參數型別不符。** 把負值或實數傳給 `int` 參數，只有在參數帶型別時才抓得到。若省略型別，工具可能默默把值截斷或強制轉換。

## 小結

- 帶型別的 `parameter` 值記錄了意圖，也讓闡述時得以檢查。
- `localparam` 用來表達呼叫者無法覆寫的衍生常數。
- `$bits` 在闡述時量出任何型別的大小；`$clog2` 算出給定深度所需的最小位址寬度。
- `generate for` 複製結構，`generate if` 在備選方案間做選擇，兩者都在 simulation 或合成之前的闡述階段定案。
- 具名的 generate 範圍（`begin : label`）能改善可讀性，也支援階層引用。

---

[← 程序區塊與運算子](05-procedural-and-operators.md) · [目錄](../README.md) · [下一章：驗證功能概覽（僅提及） →](07-verification-features-overview.md)
