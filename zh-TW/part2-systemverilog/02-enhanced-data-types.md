# 第二部 · 2. 強化的資料型別

[← 為何用 SystemVerilog 做設計](01-why-sv-for-design.md) · [目錄](../README.md) · [下一章：套件與範圍 →](03-packages-and-scope.md)

## 學習目標

- 以 `typedef` 定義具名型別，使程式碼更具自我說明性。
- 使用 `enum` 表達 FSM 狀態及其他具名常數集合。
- 以 `struct` 和 `packed struct` 將相關訊號組合在一起。
- 理解 packed 與 unpacked 陣列的差異。
- 知道在可合成設計中，2-state 型別（`bit`、`int`）與 4-state 型別（`logic`）各自何時適用。

## 設計者 mental model

SystemVerilog type 讓你命名 design concept，而不只是寫 bit range。`enum` 表示這些 encoding 是
state 或 command；`struct` 表示這些 field 會一起移動；`typedef` 讓這個 meaning 可以重用，不必
每次重寫 shape。type 因此成為一種 lightweight documentation，也讓 tool 有機會檢查你的意圖。

tradeoff 是 designer 仍然要記得底下的 hardware。packed struct 是固定 layout 的 bits，unpacked
array 是 element collection，2-state type 可能隱藏 `x` information。可以用更強的 type 來表達 intent，
但永遠要問：最後 synthesis 或 simulation 看到的是哪些 bit？

## `typedef` — 為型別命名

`typedef` 為任何型別表達式賦予一個名稱。這和 C 語言的概念相同，目的也相同：用有意義的名稱取代結構性描述。

```systemverilog
typedef logic [7:0]  byte_t;
typedef logic [31:0] word_t;
typedef logic [15:0] addr_t;

module alu (
    input  word_t a,
    input  word_t b,
    output word_t result
);
```

後綴 `_t` 是型別別名的常見慣例，語言本身不強制要求。使用具名型別能讓埠列表和訊號宣告更短、更易讀，且當寬度需要變更時只需修改一處。

## `enum` — 具名符號值

`enum` 定義了一種型別，其值從一組具名集合中選取。它是 FSM 狀態變數、運算碼（opcode）欄位，以及任何其他需要從名稱就能看出含義的訊號的正確工具。

```systemverilog
typedef enum logic [1:0] {
    IDLE    = 2'b00,
    FETCH   = 2'b01,
    DECODE  = 2'b10,
    EXECUTE = 2'b11
} state_t;

state_t state, next_state;
```

基底型別（此處為 `logic [1:0]`）設定了編碼方式和位元寬度。若省略明確的編碼，工具會從 0 開始依序指定整數值。明確的編碼讓你掌控位元樣式，這在合成工具針對特定編碼進行最佳化或在波形中觀察狀態暫存器時非常重要。

### Enum 搭配 case 敘述

`enum` 與 `unique case` 天然契合：

```systemverilog
always_comb begin
    unique case (state)
        IDLE:    next_state = FETCH;
        FETCH:   next_state = DECODE;
        DECODE:  next_state = EXECUTE;
        EXECUTE: next_state = IDLE;
    endcase
end
```

case 表達式使用符號名稱。工具檢查每個 enum 成員是否都有對應的分支（或存在 `default`）。這使 FSM 轉換可讀且可驗證。

### `enum` 方法

SystemVerilog 為 enum 變數提供內建方法，供 simulation 和測試平台使用。在可合成程式碼中，enum 操作僅限於指定和比較；`first()`、`last()`、`next()`、`prev()`、`name()` 等方法不保證可合成，應留在驗證程式碼中使用。

## `struct` — 將相關訊號組合

`struct` 將多個欄位組合在一個名稱下。當多個訊號在概念上屬於一起時使用它——例如匯流排交易（bus transaction）的各欄位，或流水線（pipeline）級的控制字。

```systemverilog
typedef struct {
    logic [31:0] data;
    logic [3:0]  byte_en;
    logic        valid;
    logic        write;
} bus_req_t;

bus_req_t req;

// Field access
assign req.valid = 1'b1;
assign req.data  = payload;
```

struct 欄位以點記法存取。struct 可以作為單一埠傳遞、整體指定，或逐欄位比較。

### `packed struct`

`packed struct` 將欄位以連續位元向量的形式儲存。欄位依宣告順序從最高有效位開始排列。這使 struct 既能被視為具名欄位的集合，也能被視為普通的位元向量。

```systemverilog
typedef struct packed {
    logic [7:0]  opcode;   // bits [15:8]
    logic [7:0]  operand;  // bits [7:0]
} instr_t;

instr_t instr;
logic [15:0] raw;

// Both are valid:
assign instr.opcode = 8'hAB;
assign raw = instr;          // treat as 16-bit vector
```

Packed struct 是可合成設計的標準選擇，因為位元佈局是確定性的，與硬體看到的訊號完全一致。Unpacked struct 可能有實現定義的填充，在合成中預測性較差。

### `union` 與 `packed union`

`union` 允許對相同的位元有不同的解讀。`packed union` 使這成為一個連續的位元欄位，這是可合成的。

```systemverilog
typedef union packed {
    logic [31:0]  raw;
    struct packed {
        logic [15:0] high;
        logic [15:0] low;
    } halves;
} word_u;

word_u w;
assign w.raw = 32'hDEADBEEF;
// w.halves.high == 16'hDEAD, w.halves.low == 16'hBEEF
```

Union 適用於定義暫存器或協定欄位的多種解讀方式。保持 union 成員寬度一致；`packed union` 中寬度不一致的成員需要明確的截斷或擴展。

## Packed 與 unpacked 陣列

SystemVerilog 區分兩種陣列維度：

- **Packed 維度** 出現在型別關鍵字與訊號名稱之間，形成連續的位元向量，對其索引或切片得到 logic 位元。
- **Unpacked 維度** 出現在訊號名稱之後，是宣告型別的陣列；各元素在記憶體或硬體中不一定連續。

```systemverilog
// Packed: 4 × 8-bit vector = one 32-bit signal
logic [3:0][7:0] packed_array;   // [31:0] as a flat bit vector

// Unpacked: 4 separate 8-bit signals
logic [7:0] unpacked_array [4];

// Mixed: 4 elements, each a 32-bit vector
logic [31:0] mixed_array [8];    // 8 unpacked, each 32 packed bits
```

對於可合成設計，當整個結構代表一個硬體字（word）時，優先使用 packed 維度。當個別元素需要以索引存取時（如記憶體、暫存器檔案、查找表），使用 unpacked 陣列。

```systemverilog
// Synthesizable register file: 16 entries, 32 bits wide
logic [31:0] regfile [16];

always_ff @(posedge clk) begin
    if (we)
        regfile[waddr] <= wdata;
end

assign rdata = regfile[raddr];
```

## 2-state 與 4-state 型別

Verilog 和 SystemVerilog 有兩個型別家族：

| 家族 | 值域 | 範例 |
|------|------|------|
| 4-state | 0、1、X、Z | `logic`、`reg`、`wire` |
| 2-state | 僅 0、1 | `bit`、`byte`、`shortint`、`int`、`longint` |

### `bit` 與 `int`

`bit` 是 1-bit 的 2-state 型別。`int` 是 32-bit 有號 2-state 型別（等同於 Verilog 的 `integer`，但為 2-state）。`byte`、`shortint`、`longint` 分別是 8-、16-、64-bit 有號 2-state 整數。

```systemverilog
bit        flag;       // 1-bit, 2-state
int        counter;    // 32-bit signed, 2-state
bit [7:0]  mask;       // 8-bit, 2-state
```

### 2-state 型別在設計中何時安全

2-state 型別適用於以下情況：

- 訊號是迴圈變數、計數器，或不會合法地保持 X 或 Z 的算術量。
- 在闡述（elaboration）時計算 parameter 或 localparam 值。
- 訊號位於測試平台內部（simulation 專用算術很常見）。

所有由硬體驅動的 RTL 埠和內部訊號都應使用 4-state `logic`。原因在於：若一個 `logic` 訊號未連接或未初始化，simulator 會傳播 X 值，提醒你問題所在。而 `bit` 訊號會悄悄初始化為 0，隱藏未初始化的狀態。在 RTL 中，隱藏 X 是危險的。

```systemverilog
// GOOD: logic for hardware signals — X propagation catches mistakes
logic [7:0] data_in;
logic [7:0] result;

// OK: bit or int for synthesis-time constants and loop variables
localparam int DEPTH = 256;
for (genvar i = 0; i < DEPTH; i++) begin : gen_cells
    // ...
end
```

> **設計意圖。** 對硬體訊號選擇 `logic`、對計數器和參數選擇 `int`/`bit`，傳達了哪些訊號屬於硬體構造，哪些是闡述時的量。型別選擇是工具可以檢查的文件形式。

## 常見陷阱

- **對硬體埠使用 unpacked struct。** 合成工具可能不支援 unpacked struct 埠。請對埠型別使用 `packed struct` 或 typedef 一個 packed struct。
- **省略 enum 的基底型別。** 預設基底型別是 `int`（2-state，32 位元），通常比需要的寬，可能引發工具警告。請一律明確宣告基底型別。
- **將整數字面值直接指定給 enum 變數。** 在 SystemVerilog 中，這需要明確的型別轉換：`state = state_t'(2'b01)`。直接指定原始字面值是型別不符。部分工具以警告接受它；為了可攜性，請依賴型別轉換。
- **對模組埠使用 2-state `bit`。** 若父模組以 X（未初始化）驅動一個埠，`bit` 型別的埠會悄悄轉換為 0。在模組邊界請使用 `logic`。
- **Packed 陣列的位元順序。** 在 `[3:0][7:0]` 的 packed 陣列中，元素 `[3]` 佔據最高有效位。在指定整平位元向量之前，請對照協定規範確認順序。

## 小結

- `typedef` 為型別表達式命名；用它讓埠列表和宣告可讀且易於維護。
- `enum` 為一組值賦予符號名稱；它最適合用於 FSM 狀態，並可由 `unique case` 進行檢查。
- `packed struct` 將欄位組合為連續位元向量，適合合成；對硬體訊號優先選擇它而非 unpacked struct。
- `packed union` 對相同位元提供多種解讀——適用於具有多種解讀方式的暫存器。
- 對硬體訊號使用 4-state `logic`；將 2-state `int`/`bit` 保留給闡述時的常數和迴圈索引。

---

[← 為何用 SystemVerilog 做設計](01-why-sv-for-design.md) · [目錄](../README.md) · [下一章：套件與範圍 →](03-packages-and-scope.md)
