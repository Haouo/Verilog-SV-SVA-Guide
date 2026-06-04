# 第二部 · 3. 套件與範圍

[← 強化的資料型別](02-enhanced-data-types.md) · [目錄](../README.md) · [下一章：介面與 modport →](04-interfaces-and-modports.md)

## 學習目標

- 定義 `package` 以存放共用的型別、參數和函式。
- 以明確匯入或萬用字元匯入的方式使用套件內容。
- 理解 `$unit` 範圍及為何應優先使用明確的套件。
- 使用套件在模組間共用定義，避免複製貼上。

## 設計者 mental model

package 是 shared design facts 的 named home。如果多個 module 同意同一個 bus width、command
encoding 或 struct shape，這個 agreement 應該存在一個地方，而不是 copy 到每個 file。import
package 就是 module 可見地宣告：我參與這份 shared contract。

scope rule 是在控制 name 從哪裡來。explicit import 和 qualified name 讓 dependency 可讀；`$unit`
和過大的 wildcard import 可能讓 dependency 隱形。block 越 reusable，package dependency 越值得
寫得明白。

## 套件解決的問題

在 Verilog 設計中，定義在一個模組中的型別對其他模組不可見。設計者的變通做法是在每個需要該定義的模組中重複宣告 `typedef`、`parameter` 和 `localparam`。當定義改變時，每一份複本都必須更新——這是維護負擔，也是細微不一致的來源。

SystemVerilog 套件（package）解決了這個問題。套件是一個具名命名空間，存放型別定義、參數、常數和函式。任何模組都可以匯入套件並使用其內容，無需重複定義。

## 宣告套件

```systemverilog
package bus_pkg;

    // Shared parameters
    parameter int DATA_WIDTH = 32;
    parameter int ADDR_WIDTH = 16;

    // Shared types
    typedef logic [DATA_WIDTH-1:0] data_t;
    typedef logic [ADDR_WIDTH-1:0] addr_t;

    typedef enum logic [1:0] {
        READ  = 2'b00,
        WRITE = 2'b01,
        BURST = 2'b10,
        IDLE  = 2'b11
    } cmd_t;

    typedef struct packed {
        addr_t  addr;
        data_t  data;
        cmd_t   cmd;
        logic   valid;
    } bus_req_t;

endpackage
```

套件在語法上與模組相似，但它沒有埠且不例化任何東西。它被編譯一次，任何匯入它的模組都可以按名稱使用其內容。

套件中不可包含 `always` 區塊、`initial` 區塊或模組例化。它只存放宣告。

## 從套件匯入

### 明確匯入

明確匯入將一個具名項目帶入範圍：

```systemverilog
import bus_pkg::DATA_WIDTH;
import bus_pkg::bus_req_t;

module memory_ctrl (
    input  bus_pkg::bus_req_t req,   // qualified name, no import needed
    output logic [DATA_WIDTH-1:0] rdata
);
```

你也可以直接使用套件名稱作為限定詞，無需匯入：`bus_pkg::bus_req_t`。這是最明確的形式，在每個使用處都清楚標示了來源。

### 萬用字元匯入

萬用字元匯入將套件的所有名稱帶入範圍，遵循名稱解析規則：

```systemverilog
import bus_pkg::*;

module memory_ctrl (
    input  bus_req_t req,
    output data_t    rdata
);
```

萬用字元匯入方便，但當兩個套件定義相同識別字時可能造成名稱衝突。在大型設計中有多個套件時，使用明確匯入或限定名稱更為安全。

### 在埠列表中匯入

你可以在模組標頭的埠列表之前進行匯入，使匯入的名稱在埠宣告中可用：

```systemverilog
module memory_ctrl
    import bus_pkg::*;
(
    input  bus_req_t  req,
    output data_t     rdata,
    input  logic      clk,
    input  logic      rst_n
);
```

這是高度依賴某個套件的模組的慣用 SystemVerilog 風格。

## 套件也可存放參數

透過套件共用參數，比在頂層模組中定義或通過每個模組的參數埠傳遞更為簡潔。

```systemverilog
package config_pkg;
    parameter int FIFO_DEPTH    = 16;
    parameter int PIPELINE_STAGES = 4;
    localparam int ADDR_BITS    = $clog2(FIFO_DEPTH);
endpackage
```

任何需要 `FIFO_DEPTH` 的模組只需匯入 `config_pkg` 並直接使用名稱。對套件進行的單一修改，在重新編譯後即可傳播到所有使用處。

注意，套件中的 `localparam` 不能被父模組覆寫——它是一個計算所得的常數。套件中的 `parameter` 原則上可以透過參數化套件例化來覆寫，但這種功能在實踐中鮮少使用。對於不應被覆寫的共用常數，`localparam` 更為安全。

## `$unit` 範圍

SystemVerilog 有一個編譯單元（compilation-unit）範圍，寫作 `$unit`，是同一編譯單元（大致上是一次編譯器調用）的隱式全域命名空間。在任何模組或套件之外宣告的內容落入 `$unit`，對同一單元中編譯的所有內容可見。

```systemverilog
// In $unit scope (outside any module/package)
typedef logic [7:0] byte_t;   // visible to all modules in this compilation unit
```

`$unit` 能用，但很脆弱：

- 其內容依賴於檔案順序和工具調用方式，使設計對編譯順序敏感。
- 兩個編譯單元可能不共享同一個 `$unit` 範圍，導致跨多個編譯作業的設計出現問題。
- 它不提供命名空間——所有內容落入同一個平坦的全域命名空間。

請優先使用明確的套件而非 `$unit`。養成宣告套件並從中匯入的習慣，能讓依賴關係可見，並使設計跨工具和編譯策略更具可攜性。

> **設計意圖。** 套件表達了一組定義在設計合約中屬於一體且被共享的事實。當你在模組頂端看到 `import bus_pkg::*` 時，你立刻知道該模組參與了該套件中定義的匯流排協定。套件是規格；匯入是宣告。

## 在專案中組織套件

常見的模式是每個協定或子系統一個套件：

```text
bus_pkg        — 匯流排型別與寬度
config_pkg     — 頂層參數與衍生常數
alu_pkg        — ALU 運算碼與控制型別
soc_pkg        — SoC 層級的列舉
```

保持套件小巧且聚焦。存放不相關定義的大型套件難以維護，並產生不必要的編譯順序依賴。

套件可以從其他套件匯入：

```systemverilog
package alu_pkg;
    import bus_pkg::data_t;   // reuse the shared data type

    typedef enum logic [2:0] {
        ADD = 3'd0,
        SUB = 3'd1,
        AND = 3'd2,
        OR  = 3'd3,
        XOR = 3'd4
    } opcode_t;

endpackage
```

這構建了清晰的依賴圖：`alu_pkg` 依賴 `bus_pkg`，而非依賴特定的模組。

## 常見陷阱

- **在模組內定義型別並期望其他模組可見。** 在模組本體中定義的型別是該模組的局部型別。若另一個模組需要相同的型別，請將定義移至套件。
- **依賴 `$unit` 共用定義。** 工具和檔案順序的敏感性使 `$unit` 很脆弱。請使用明確的套件。
- **萬用字元匯入衝突。** 若兩個套件定義了 `data_t`，同時對兩者進行萬用字元匯入會造成名稱歧義。使用限定名稱或明確匯入來解決衝突。
- **在套件中放入 `always` 區塊或模組例化。** 套件只存放宣告。硬體行為屬於模組。
- **套件中 `parameter` 與 `localparam` 的混淆。** 對不應被覆寫的常數使用 `localparam`；只有打算支援參數化套件例化時才使用 `parameter`。

## 小結

- `package` 是共用型別、參數和常數的具名命名空間。
- 使用 `import pkg::name`（明確）或 `import pkg::*`（萬用字元）匯入；限定名稱 `pkg::name` 無需匯入即可使用。
- 避免使用 `$unit`；為了可攜性和清晰性，優先使用明確的套件。
- 每個協定或子系統一個套件，使依賴關係清晰且套件保持聚焦。

---

[← 強化的資料型別](02-enhanced-data-types.md) · [目錄](../README.md) · [下一章：介面與 modport →](04-interfaces-and-modports.md)
