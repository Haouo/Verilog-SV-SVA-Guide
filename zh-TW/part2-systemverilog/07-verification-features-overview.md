# 第二部 · 7. 驗證功能概覽（僅提及）

[← 參數化與 generate](06-parameterization-and-generate.md) · [目錄](../README.md) · [下一章：為何需要斷言 →](../part3-sva/01-why-assertions.md)

> **範圍說明。** 本章刻意簡短。SystemVerilog 的驗證子集——類別（class）、約束隨機化（constrained randomization）、覆蓋率（coverage）、mailbox、semaphore 和 UVM——是一個龐大的領域，有其獨立的文獻，**不在**本指南的討論範圍之內。第二部僅涵蓋可合成的設計子集。本章的目標是列舉主要的驗證功能，使設計者在閱讀混合設計與驗證的程式碼時能夠識別它們，並知道在哪裡尋找進一步的資訊。關於驗證方法論，請參閱[附錄 D](../appendices/D-references.md) 中的參考資料。

## 學習目標

- 能以名稱識別主要的 SystemVerilog 驗證構造。
- 理解這些功能僅用於 simulation，不可合成（synthesizable）。
- 了解設計子集（本指南）與驗證子集的邊界。

## 設計者 mental model

SystemVerilog 同時包含 design feature 和 verification feature。designer 不需要精通每個 class-based
或 UVM 細節才能寫好 RTL，但應該能辨識 code 何時離開 synthesizable design subset。這個辨識能力
可以避免不小心依賴 testbench-only construct。

本章是一張地圖，而不是 methodology course。目的在於說明 class、constrained randomization、
functional coverage、UVM 相對於 RTL 和 assertion 的位置。對 designer 來說，SVA 是最直接的 bridge：
它靠近 design，也提供 verification tool 精準的 check target。

## SystemVerilog 的兩個面向

IEEE 1800 是一個服務兩個社群的單一標準。**設計子集**（本指南第一部和第二部）以可合成 RTL 為目標：模組、always 區塊、介面、套件和型別系統。**驗證子集**以物件導向程式設計、隨機化和覆蓋率擴展了語言——這些都不能合成為硬體。

一個檔案可以混合這兩個子集。合成工具只接受設計子集；它們拒絕或忽略驗證構造。simulator 接受兩者。當閱讀 SystemVerilog 程式碼庫時，你會遇到這兩個部分。

## 物件導向程式設計：類別

SystemVerilog 新增了帶有繼承（inheritance）、多型（polymorphism）和虛擬方法（virtual method）的 `class` 構造。類別在驗證中用於建模交易（transaction）、序列（sequence）和環境（environment）。類別例化以 `new` 配置，存活在堆積（heap）上。

這些都不可合成。若你在檔案中看到 `class`、`extends`、`virtual function` 或 `new`，那個檔案是驗證程式碼。

```systemverilog
// Verification only — not synthesizable
class bus_transaction;
    rand logic [31:0] addr;
    rand logic [31:0] data;
    rand logic        write;

    function new();
        addr  = '0;
        data  = '0;
        write = 1'b0;
    endfunction
endclass
```

## 約束隨機化

類別欄位上的 `rand` 和 `randc` 修飾詞將它們標記為隨機生成的對象。`constraint` 區塊表達這些值的關係和限制。`randomize()` 方法生成滿足所有約束的合法值集合。

```systemverilog
// Verification only
class aligned_transaction extends bus_transaction;
    constraint c_aligned {
        addr[1:0] == 2'b00;   // word-aligned addresses only
        data inside {[0:255]}; // small data values
    }
endclass
```

約束隨機化是現代驗證方法論的基礎，完全是 simulation 專用的。

## 行程間通訊：mailbox 與 semaphore

`mailbox` 是一個參數化的 FIFO，用於在並行 simulation 執行緒（`fork / join`）之間傳遞物件。`semaphore` 提供互斥（mutual exclusion）。兩者都是 simulation 構造。

```systemverilog
// Verification only
mailbox #(bus_transaction) gen2drv;   // generator to driver channel
semaphore bus_lock;                   // prevent concurrent bus access
```

這些在合成中沒有對應物。硬體同步使用帶時脈的邏輯和握手協定——即第一部和第二部的主題。

## 功能覆蓋率

`covergroup` 和 `coverpoint` 測量 simulation 已測試的值和值組合。覆蓋率報告推動驗證過程：當覆蓋率達到 100% 時，驗證計劃完成。

```systemverilog
// Verification only
covergroup bus_cg @(posedge clk);
    cp_cmd: coverpoint bus.cmd {
        bins read  = {READ};
        bins write = {WRITE};
    }
    cp_len: coverpoint bus.len { bins short = {[1:4]}; bins long = {[5:16]}; }
    cx_cmd_len: cross cp_cmd, cp_len;
endgroup
```

功能覆蓋率補充了程式碼覆蓋率和斷言覆蓋率。這些對合成都沒有影響。

## 通用驗證方法論（UVM）

UVM（Universal Verification Methodology）是建立在 SystemVerilog 類別系統之上的程式庫。它標準化了驗證環境的結構：代理程式（agent）、驅動器（driver）、監視器（monitor）、計分板（scoreboard）和序列（sequence）。大多數產業驗證工作都在 UVM 中進行。

UVM 超出了本指南的範圍。這是一個廣泛的主題；已有專門的書籍和課程。附錄 D 的參考資料列表指向標準的入門材料。

## 斷言作為橋梁

SystemVerilog Assertions（SVA）占據了中間地帶：它們以驗證風格撰寫，但許多可以合成，也可以交給 formal verification tool 使用。SVA 是本指南第三部的主題，也是每位 RTL 設計者都應了解的驗證相鄰功能。

> **設計意圖。** 了解驗證功能的存在——並能在程式碼中識別它們——幫助設計者理解完整的 SystemVerilog 生態系統，而不至於被它淹沒。第一部和第二部的設計子集已足以描述任何可合成的 RTL。第三部新增了將設計意圖與自動化檢查相連接的斷言（assertion）層。

## 常見陷阱

- **在可合成設計檔案中使用 `class` 或 `rand`。** 合成工具會拒絕這些構造。將驗證程式碼保存在單獨的檔案或目錄中，並使設計檔案不含類別定義和隨機修飾詞。
- **將 `mailbox` 與硬體 FIFO 混淆。** `mailbox` 是 simulation 物件。硬體 FIFO 是帶有帶時脈的推入和彈出邏輯的模組，如第六章所示。
- **將覆蓋率視為合成的一部分。** 覆蓋率指令是 simulation 儀器。它們不會在合成設計中增加任何邏輯。

## 小結

- SystemVerilog 有一個設計子集（可合成）和一個驗證子集（僅限 simulation）；本指南涵蓋設計子集。
- 類別、約束隨機化、mailbox、semaphore 和 covergroup 都是驗證構造，無一可合成為硬體。
- UVM 是建立在 SV 類別系統上的標準驗證方法論；它是一個獨立的學科。
- SVA（第三部）是橋梁：可用於設計和 formal 驗證情境的斷言語言。
- 關於驗證，請參閱[附錄 D](../appendices/D-references.md) 中的參考資料。

---

[← 參數化與 generate](06-parameterization-and-generate.md) · [目錄](../README.md) · [下一章：為何需要斷言 →](../part3-sva/01-why-assertions.md)
