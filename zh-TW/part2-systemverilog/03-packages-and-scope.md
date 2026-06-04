# 第二部 · 3. 套件與範圍

[← 強化的資料型別](02-enhanced-data-types.md) · [目錄](../README.md) · [下一章：介面與 modport →](04-interfaces-and-modports.md)

## 學習目標

- 定義 `package` 以存放共用的型別、參數和函式。
- 以明確匯入或萬用字元匯入的方式使用套件內容。
- 理解 `$unit` 範圍及為何應優先使用明確的套件。
- 使用套件在模組間共用定義，避免複製貼上。

## 設計者的心智模型

package 是共用設計事實的一個具名歸宿。如果多個模組對同一個匯流排寬度、命令編碼或 struct 結構有共識，這份共識就該集中放在一處，而不是複製到每個檔案裡。匯入一個 package，等於模組明明白白地宣告：我參與了這份共用合約。

範圍規則的作用，是控制名稱究竟從哪裡來。明確匯入和限定名稱讓相依關係清楚可讀；`$unit` 和範圍過大的萬用字元匯入，卻可能讓相依關係隱形。一個區塊越是要重複使用，把它的 package 相依關係寫明白就越有價值。

## 套件解決的問題

在 Verilog 設計中，定義在某個模組裡的型別，其他模組看不到。設計者的變通做法，是在每個需要該定義的模組裡都重複宣告一遍 `typedef`、`parameter` 和 `localparam`。一旦定義有變，每一份複本都得跟著改，既是維護負擔，也是細微不一致的來源。

SystemVerilog 套件（package）解決了這個問題。套件是一個具名命名空間，用來存放型別定義、參數、常數和函式。任何模組都能匯入套件、使用其中的內容，不必重複定義。

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

套件的語法和模組相似，但它沒有埠，也不例化任何東西。它只編譯一次，凡是匯入它的模組都能按名稱取用其中的內容。

套件裡不可放 `always` 區塊、`initial` 區塊或模組例化，它只存放宣告。

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

你也可以直接拿套件名稱當限定詞，不必匯入：`bus_pkg::bus_req_t`。這是最明確的寫法，在每個使用處都標清楚了來源。

### 萬用字元匯入

萬用字元匯入將套件的所有名稱帶入範圍，遵循名稱解析規則：

```systemverilog
import bus_pkg::*;

module memory_ctrl (
    input  bus_req_t req,
    output data_t    rdata
);
```

萬用字元匯入很方便，但兩個套件若定義了相同的識別字，就可能造成名稱衝突。在使用多個套件的大型設計中，改用明確匯入或限定名稱會比較安全。

### 在埠列表中匯入

你可以在模組標頭裡、埠列表之前先匯入，讓匯入的名稱在埠宣告中就能使用：

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

對於高度依賴某個套件的模組，這是慣用的 SystemVerilog 寫法。

## 套件也可存放參數

用套件共用參數，比在頂層模組裡定義、或經由每個模組的參數埠層層傳遞都來得乾淨。

```systemverilog
package config_pkg;
    parameter int FIFO_DEPTH    = 16;
    parameter int PIPELINE_STAGES = 4;
    localparam int ADDR_BITS    = $clog2(FIFO_DEPTH);
endpackage
```

任何需要 `FIFO_DEPTH` 的模組，只要匯入 `config_pkg` 並直接寫名稱即可。對套件改一處，重新編譯後就會傳播到所有使用處。

要注意的是，套件常數無法像模組參數那樣被覆寫：套件不會被例化，所以套件中宣告的 `parameter` 實質上就是固定常數。請優先用 `localparam`，把「永不覆寫」的意圖講明白。

## `$unit` 範圍

SystemVerilog 有一個編譯單元（compilation-unit）範圍，寫作 `$unit`，是同一個編譯單元（大致上就是一次編譯器調用）的隱式全域命名空間。凡是在任何模組或套件之外宣告的內容，都會落入 `$unit`，並對同一單元中編譯的一切可見。

```systemverilog
// In $unit scope (outside any module/package)
typedef logic [7:0] byte_t;   // visible to all modules in this compilation unit
```

`$unit` 能用，但很脆弱：

- 它的內容受檔案順序和工具調用方式影響，使設計對編譯順序敏感。
- 兩個編譯單元未必共享同一個 `$unit` 範圍，會讓橫跨多個編譯作業的設計出問題。
- 它不提供命名空間：所有內容都擠進同一個平坦的全域命名空間。

請優先用明確的套件，而不是 `$unit`。養成宣告套件、再從中匯入的習慣，能讓相依關係看得見，也讓設計在不同工具和編譯策略間更好移植。

> **設計意圖。** 套件表明一組定義在設計合約上本屬一體、且被共同使用。當你在模組頂端看到 `import bus_pkg::*`，立刻就知道這個模組參與了該套件所定義的匯流排協定。套件是規格，匯入是宣告。

## 在專案中組織套件

常見的模式是每個協定或子系統一個套件：

```text
bus_pkg        — 匯流排型別與寬度
config_pkg     — 頂層參數與衍生常數
alu_pkg        — ALU 運算碼與控制型別
soc_pkg        — SoC 層級的列舉
```

套件要小而聚焦。塞滿不相關定義的大套件難以維護，還會帶來不必要的編譯順序相依。

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

這樣就建立起清晰的相依圖：`alu_pkg` 依賴 `bus_pkg`，而不是依賴某個特定模組。

## 常見陷阱

- **在模組內定義型別，卻指望其他模組看得到。** 在模組本體中定義的型別只屬於該模組。若另一個模組也要用同一型別，請把定義移到套件。
- **靠 `$unit` 來共用定義。** `$unit` 對工具和檔案順序很敏感，因而脆弱。請改用明確的套件。
- **萬用字元匯入衝突。** 若兩個套件都定義了 `data_t`，同時對兩者做萬用字元匯入就會造成名稱歧義。請用限定名稱或明確匯入來化解。
- **在套件裡放 `always` 區塊或模組例化。** 套件只存放宣告，硬體行為屬於模組。
- **混淆套件中的 `parameter` 與 `localparam`。** 在套件裡兩者實質上都是固定常數，因為套件不會被例化。請優先用 `localparam`，把永不覆寫的意圖講明白。

## 小結

- `package` 是共用型別、參數和常數的具名命名空間。
- 使用 `import pkg::name`（明確）或 `import pkg::*`（萬用字元）匯入；限定名稱 `pkg::name` 無需匯入即可使用。
- 避免使用 `$unit`；為了可攜性和清晰性，優先使用明確的套件。
- 每個協定或子系統一個套件，使依賴關係清晰且套件保持聚焦。

---

[← 強化的資料型別](02-enhanced-data-types.md) · [目錄](../README.md) · [下一章：介面與 modport →](04-interfaces-and-modports.md)
