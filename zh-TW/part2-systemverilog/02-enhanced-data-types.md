# 第二部 · 2. 強化的資料型別

[← 為何用 SystemVerilog 做設計](01-why-sv-for-design.md) · [目錄](../README.md) · [下一章：套件與範圍 →](03-packages-and-scope.md)

## 學習目標

- 以 `typedef` 定義具名型別，使程式碼更具自我說明性。
- 使用 `enum` 表達 FSM 狀態及其他具名常數集合。
- 以 `struct` 和 `packed struct` 將相關訊號組合在一起。
- 理解 packed 與 unpacked 陣列的差異。
- 知道在可合成設計中，2-state 型別（`bit`、`int`）與 4-state 型別（`logic`）各自何時適用。

## 設計者的心智模型

SystemVerilog 的型別讓你為設計概念命名，而不只是寫出一段位元範圍。`enum` 表明這些編碼代表狀態或命令；`struct` 表明這些欄位會一起搬動；`typedef` 讓這層含義可以重用，不必每次都重寫一遍結構。型別因此成了一種輕量的文件，也讓工具有機會檢查你的意圖。

代價是設計者仍得記住底層的硬體。packed struct 是固定佈局的一串位元，unpacked 陣列是一組元素的集合，而 2-state 型別可能藏住 `x` 資訊。你可以用更強的型別來表達意圖，但永遠要問一句：最後送進合成或 simulation 的，究竟是哪些位元？

## `typedef` — 為型別命名

`typedef` 為任何型別表達式取一個名稱。這和 C 語言的做法相同，目的也一樣：用一個有意義的名稱取代冗長的結構性描述。

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

`enum` 定義一種型別，它的值取自一組具名的集合。凡是希望從名稱就讀出含義的訊號，例如 FSM 狀態變數、運算碼（opcode）欄位，`enum` 都是合適的工具。

```systemverilog
typedef enum logic [1:0] {
    IDLE    = 2'b00,
    FETCH   = 2'b01,
    DECODE  = 2'b10,
    EXECUTE = 2'b11
} state_t;

state_t state, next_state;
```

基底型別（此處為 `logic [1:0]`）決定了編碼方式和位元寬度。若不寫出明確的編碼，工具會從 0 起依序指定整數值。明確指定編碼讓你掌控位元樣式；當合成工具針對特定編碼最佳化，或你要在波形中觀察狀態暫存器時，這一點相當重要。

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

case 表達式直接寫符號名稱。工具會檢查每個 enum 成員是否都有對應的分支，或是否備有 `default`。這讓 FSM 轉換既好讀又可驗證。

### `enum` 方法

SystemVerilog 為 enum 變數提供了內建方法，供 simulation 和測試平台使用。在可合成程式碼裡，enum 的操作應只限於指定和比較；`first()`、`last()`、`next()`、`prev()`、`name()` 這些方法不保證可合成，該留在驗證程式碼中使用。

## `struct` — 將相關訊號組合

`struct` 把多個欄位收攏在同一個名稱底下。當幾個訊號在概念上本就屬於一組時就用它，例如匯流排交易（bus transaction）的各個欄位，或某個管線（pipeline）級的控制字。

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

struct 的欄位用點記法存取。一個 struct 可以當成單一埠傳遞、整體一次指定，也可以逐欄位比較。

### `packed struct`

`packed struct` 把欄位以連續位元向量的形式儲存，各欄位依宣告順序、從最高有效位往下排。這樣一來，同一個 struct 既能看作一組具名欄位，也能看作一個普通的位元向量。

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

packed struct 是可合成設計的標準選擇，因為它的位元佈局是確定的，和硬體實際看到的訊號完全一致。unpacked struct 則可能含有由實作自行決定的填充，在合成中較難預測。

### `union` 與 `packed union`

`union` 允許對同一串位元做不同的解讀。`packed union` 把它變成一個連續的位元欄位，因而可以合成。

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

當你要為暫存器或協定欄位定義多種解讀方式時，union 很好用。請讓各 union 成員的寬度一致；`packed union` 中寬度不一的成員，需要明確的截斷或擴展。

## Packed 與 unpacked 陣列

SystemVerilog 區分兩種陣列維度：

- **Packed 維度** 寫在型別關鍵字與訊號名稱之間，形成一個連續的位元向量，對它索引或切片會得到 logic 位元。
- **Unpacked 維度** 寫在訊號名稱之後，是一個由宣告型別構成的陣列，各元素在記憶體或硬體中不一定連續。

```systemverilog
// Packed: 4 × 8-bit vector = one 32-bit signal
logic [3:0][7:0] packed_array;   // [31:0] as a flat bit vector

// Unpacked: 4 separate 8-bit signals
logic [7:0] unpacked_array [4];

// Mixed: 4 elements, each a 32-bit vector
logic [31:0] mixed_array [8];    // 8 unpacked, each 32 packed bits
```

在可合成設計裡，當整個結構代表一個硬體字（word）時，優先用 packed 維度；當需要逐一以索引存取個別元素時，例如記憶體、暫存器檔案、查找表，則用 unpacked 陣列。

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

凡是由硬體驅動的 RTL 埠和內部訊號，都應使用 4-state `logic`。原因在於：`logic` 訊號一旦未接或未初始化，simulator 會把 X 值傳播出去，提醒你出了問題；而 `bit` 訊號會悄悄初始化為 0，把未初始化的狀態藏了起來。在 RTL 中，藏住 X 是危險的。

```systemverilog
// GOOD: logic for hardware signals — X propagation catches mistakes
logic [7:0] data_in;
logic [7:0] result;

// OK: bit or int for synthesis-time constants and loop variables
localparam int DEPTH = 256;

// Generate loops use genvar — an elaboration-time index, not int/bit
for (genvar i = 0; i < DEPTH; i++) begin : gen_cells
    // ...
end
```

> **設計意圖。** 對硬體訊號選 `logic`、對計數器和參數選 `int`／`bit`，就傳達出哪些訊號屬於硬體結構、哪些只是闡述時的量。型別選擇本身就是一種工具能檢查的文件。

## 常見陷阱

- **對硬體埠使用 unpacked struct。** 合成工具可能不支援 unpacked struct 埠。請對埠型別使用 `packed struct` 或 typedef 一個 packed struct。
- **省略 enum 的基底型別。** 預設基底型別是 `int`（2-state，32 位元），通常比需要的寬，可能引發工具警告。請一律明確宣告基底型別。
- **把整數字面值直接指定給 enum 變數。** 在 SystemVerilog 中，這需要明確的型別轉換：`state = state_t'(2'b01)`。直接指定原始字面值屬於型別不符；有些工具會發出警告後接受，但為了可攜性，請一律用型別轉換。
- **對模組埠使用 2-state `bit`。** 若父模組以 X（未初始化）驅動一個埠，`bit` 型別的埠會悄悄轉換為 0。在模組邊界請使用 `logic`。
- **Packed 陣列的位元順序。** 在 `[3:0][7:0]` 的 packed 陣列中，元素 `[3]` 佔據最高有效位。在指定整平位元向量之前，請對照協定規範確認順序。

## 小結

- `typedef` 為型別表達式命名；用它讓埠列表和宣告可讀且易於維護。
- `enum` 為一組值賦予符號名稱；它最適合用於 FSM 狀態，並可用 `unique case` 檢查。
- `packed struct` 將欄位組合為連續位元向量，適合合成；對硬體訊號優先選擇它而非 unpacked struct。
- `packed union` 對同一串位元提供多種解讀，適用於有多種解讀方式的暫存器。
- 對硬體訊號使用 4-state `logic`；將 2-state `int`/`bit` 保留給闡述時的常數和迴圈索引。

---

[← 為何用 SystemVerilog 做設計](01-why-sv-for-design.md) · [目錄](../README.md) · [下一章：套件與範圍 →](03-packages-and-scope.md)
