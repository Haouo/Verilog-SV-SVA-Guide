# 第二部 · 7. 驗證功能概覽（僅提及）

[← 參數化與 generate](06-parameterization-and-generate.md) · [目錄](../README.md) · [下一章：為何需要斷言 →](../part3-sva/01-why-assertions.md)

> **範圍說明。** 本章刻意寫得簡短。SystemVerilog 的驗證子集，也就是類別（class）、約束隨機化（constrained randomization）、覆蓋率（coverage）、mailbox、semaphore 和 UVM，本身就是一個龐大的領域，有自己的專門文獻，**不在**本指南的討論範圍內。第二部只涵蓋可合成的設計子集。本章的目的，是把主要的驗證功能一一點名，讓設計者在閱讀設計與驗證混雜的程式碼時能認得它們，並知道該往哪裡找更多資訊。驗證方法論的部分，請參閱[附錄 D](../appendices/D-references.md) 的參考資料。

## 學習目標

- 能叫得出主要的 SystemVerilog 驗證構件的名稱。
- 理解這些功能只能用於 simulation，不可合成（synthesizable）。
- 清楚設計子集（本指南）與驗證子集之間的界線在哪裡。

## 設計者的心智模型

SystemVerilog 同時包含設計功能與驗證功能。設計者不必精通每一處類別或 UVM 的細節才能寫好 RTL，但應該認得出程式碼何時離開了可合成的設計子集。有了這份辨識力，就不會不小心依賴上只屬於測試平台的構件。

本章是一張地圖，不是一門方法論課程。目的在於說明類別、約束隨機化、功能覆蓋率、UVM 相對於 RTL 和斷言各自的位置。對設計者而言，SVA 是最直接的橋樑：它貼近設計，又能給驗證工具一個精確的檢查目標。

## SystemVerilog 的兩個面向

IEEE 1800 是一份單一標準，卻服務兩個社群。**設計子集**（本指南第一部和第二部）瞄準可合成的 RTL：模組、always 區塊、介面、套件與型別系統。**驗證子集**則以物件導向程式設計、隨機化與覆蓋率擴充了這門語言，而這些都無法合成為硬體。

同一個檔案可以混用這兩個子集。合成工具只接受設計子集，會拒絕或忽略驗證構件；simulator 則兩者皆收。在閱讀 SystemVerilog 程式碼庫時，你會同時碰到這兩塊。

## 物件導向程式設計：類別

SystemVerilog 新增了 `class` 構件，支援繼承（inheritance）、多型（polymorphism）和虛擬方法（virtual method）。在驗證中，類別用來建模交易（transaction）、序列（sequence）和環境（environment）。類別例化以 `new` 配置，存活在堆積（heap）上。

這些都不可合成。只要在檔案裡看到 `class`、`extends`、`virtual function` 或 `new`，那就是驗證程式碼。

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

類別欄位上的 `rand` 和 `randc` 修飾詞，把這些欄位標記為隨機生成的對象。`constraint` 區塊表達這些值之間的關係與限制。`randomize()` 方法則生成一組滿足所有約束的合法值。

```systemverilog
// Verification only
class aligned_transaction extends bus_transaction;
    constraint c_aligned {
        addr[1:0] == 2'b00;   // word-aligned addresses only
        data inside {[0:255]}; // small data values
    }
endclass
```

約束隨機化是現代驗證方法論的基礎，且完全只能用於 simulation。

## 行程間通訊：mailbox 與 semaphore

`mailbox` 是一個參數化的 FIFO，用來在並行的 simulation 執行緒（`fork / join`）之間傳遞物件。`semaphore` 提供互斥（mutual exclusion）。兩者都是 simulation 構件。

```systemverilog
// Verification only
mailbox #(bus_transaction) gen2drv;   // generator to driver channel
semaphore bus_lock;                   // prevent concurrent bus access
```

這些在合成裡沒有對應物。硬體同步靠的是帶時脈的邏輯與握手協定，也就是第一部和第二部的主題。

## 功能覆蓋率

`covergroup` 和 `coverpoint` 量度 simulation 已經測過哪些值與值的組合。覆蓋率報告推動著驗證流程：當覆蓋率達到 100%，驗證計劃就算完成。

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

功能覆蓋率補足了程式碼覆蓋率與斷言覆蓋率，而這些都不會影響合成。

## 通用驗證方法論（UVM）

UVM（Universal Verification Methodology）是建立在 SystemVerilog 類別系統之上的程式庫。它把驗證環境的結構標準化：代理程式（agent）、驅動器（driver）、監視器（monitor）、計分板（scoreboard）和序列（sequence）。業界多數的驗證工作都在 UVM 中進行。

UVM 不在本指南的範圍內。這是個內容廣泛的主題，已有專門的書籍與課程。附錄 D 的參考資料清單指向標準的入門材料。

## 斷言作為橋梁

SystemVerilog Assertions（SVA）站在中間地帶：它們以驗證的風格撰寫，但許多可以合成，也能交給 formal verification tool 使用。SVA 是本指南第三部的主題，也是每位 RTL 設計者都該懂的、與驗證相鄰的功能。

> **設計意圖。** 知道這些驗證功能的存在，並能在程式碼中認出它們，能幫設計者掌握完整的 SystemVerilog 生態系統，又不至於被它淹沒。第一部和第二部的設計子集，已足以描述任何可合成的 RTL。第三部再加上斷言（assertion）這一層，把設計意圖與自動化檢查連接起來。

## 常見陷阱

- **在可合成的設計檔案裡用 `class` 或 `rand`。** 合成工具會拒絕這些構件。請把驗證程式碼放在獨立的檔案或目錄，讓設計檔案不含類別定義與隨機修飾詞。
- **把 `mailbox` 當成硬體 FIFO。** `mailbox` 是 simulation 物件。硬體 FIFO 是一個帶有帶時脈推入與彈出邏輯的模組，如第六章所示。
- **把覆蓋率當成合成的一部分。** 覆蓋率指令是 simulation 的量測手段，不會在合成出的設計裡增加任何邏輯。

## 小結

- SystemVerilog 分成設計子集（可合成）與驗證子集（僅限 simulation）；本指南涵蓋設計子集。
- 類別、約束隨機化、mailbox、semaphore 和 covergroup 都是驗證構件，沒有一個能合成為硬體。
- UVM 是建立在 SV 類別系統上的標準驗證方法論，自成一門獨立學科。
- SVA（第三部）是橋樑：一種設計與 formal 驗證情境都能用的斷言語言。
- 驗證相關內容，請參閱[附錄 D](../appendices/D-references.md) 的參考資料。

---

[← 參數化與 generate](06-parameterization-and-generate.md) · [目錄](../README.md) · [下一章：為何需要斷言 →](../part3-sva/01-why-assertions.md)
