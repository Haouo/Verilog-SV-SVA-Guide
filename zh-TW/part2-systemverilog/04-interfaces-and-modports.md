# 第二部 · 4. 介面與 modport

[← 套件與範圍](03-packages-and-scope.md) · [目錄](../README.md) · [下一章：程序區塊與運算子 →](05-procedural-and-operators.md)

## 學習目標

- 宣告 `interface` 以將相關訊號聚合在一個名稱下。
- 使用 `modport` 為連接到介面的每個角色指定埠方向。
- 透過介面對模組進行例化和連接。
- 理解介面對設計本身的益處，而不僅限於驗證用途。

## 介面解決的問題

典型的匯流排或握手（handshake）協定包含多個總是一起傳遞的訊號：資料、位址、valid、ready、寫入致能、位元組致能等等。在普通 Verilog 中，每個訊號都是參與該協定的每個模組上的一個獨立埠。連接兩個模組意味著逐一連接每個訊號。在協定中增加一個訊號，就必須編輯每個模組和每個例化——這是繁瑣且容易出錯的過程。

SystemVerilog 介面（interface）將這些訊號收集到一個具名的束（bundle）中。這個束宣告一次、連接一次，並在一處進行擴展。

## 宣告介面

```systemverilog
interface simple_bus #(
    parameter int DATA_W = 32,
    parameter int ADDR_W = 16
);
    logic [DATA_W-1:0] data;
    logic [ADDR_W-1:0] addr;
    logic              valid;
    logic              ready;
    logic              write;

endinterface
```

介面的語法與模組相似，但只包含訊號宣告（以及可選的 modport、函式和任務）。它有像模組一樣的參數。它不是模組——它沒有埠，也無法單獨合成。

## `modport` — 每個角色的方向

介面本身沒有方向資訊。同一個 `data` 訊號，由主機（master）驅動，由從機（slave）讀取。`modport` 為每個邏輯角色附加一個名稱和方向集合：

```systemverilog
interface simple_bus #(
    parameter int DATA_W = 32,
    parameter int ADDR_W = 16
);
    logic [DATA_W-1:0] data;
    logic [ADDR_W-1:0] addr;
    logic              valid;
    logic              ready;
    logic              write;

    modport master (
        output data, addr, valid, write,
        input  ready
    );

    modport slave (
        input  data, addr, valid, write,
        output ready
    );

endinterface
```

現在 `master` 和 `slave` 各自命名了介面訊號的一個子集和方向。模組宣告它使用哪個 modport。

## 將介面用作埠

模組透過命名介面型別和 modport 來宣告一個介面埠：

```systemverilog
module bus_master (
    input  logic      clk,
    input  logic      rst_n,
    simple_bus.master bus      // interface type, modport
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            bus.valid <= 1'b0;
            bus.write <= 1'b0;
        end else begin
            bus.valid <= 1'b1;
            bus.addr  <= next_addr;
            bus.data  <= next_data;
            bus.write <= do_write;
        end
    end

    logic [15:0] next_addr;
    logic [31:0] next_data;
    logic        do_write;
    // ... internal logic not shown
endmodule
```

```systemverilog
module bus_slave (
    input  logic     clk,
    input  logic     rst_n,
    simple_bus.slave bus
);
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            bus.ready <= 1'b0;
        else
            bus.ready <= 1'b1;   // simplified accept-all
    end
    // ... memory access not shown
endmodule
```

兩個模組都透過欄位名稱存取訊號（`bus.valid`、`bus.data` 等），無需管理個別線路的列表。

## 例化與連接

在頂層，例化一次介面，然後將其傳遞給每個模組：

```systemverilog
module top;
    logic clk, rst_n;

    // One interface instance
    simple_bus #(.DATA_W(32), .ADDR_W(16)) bus_if ();

    bus_master u_master (
        .clk   (clk),
        .rst_n (rst_n),
        .bus   (bus_if)   // interface port
    );

    bus_slave u_slave (
        .clk   (clk),
        .rst_n (rst_n),
        .bus   (bus_if)
    );

    // ... clock generation not shown
endmodule
```

介面是單一的連接點。在 `simple_bus` 中新增一個訊號，意味著編輯介面宣告以及一到兩個使用該新訊號的模組——而非每個埠列表和每個例化。

## 介面陣列

介面陣列適用於多通道或多埠設計：

```systemverilog
simple_bus #(.DATA_W(32), .ADDR_W(16)) port_if [4] ();  // 4 instances

// Connect to an array of masters
for (genvar i = 0; i < 4; i++) begin : gen_masters
    bus_master u_master (
        .clk  (clk),
        .rst_n(rst_n),
        .bus  (port_if[i])
    );
end
```

各合成工具對介面陣列的支援程度不一；在正式 RTL 中使用之前，請確認工具支援情況。

## 介面與測試平台

介面在驗證中被大量使用，測試平台的驅動器（driver）和監視器（monitor）都連接到同一個介面。該用途不在本指南的範圍內（見附錄 D）。本章的重點是：介面為設計本身提供了簡潔、有型別的連接性：縮小了埠列表、實現了型別檢查的連接，並為協定提供了單一定義點。

> **設計意圖。** 介面是以程式碼表達的協定。當你看到模組的埠列表中出現 `simple_bus.master bus`，你一眼就能知道這個模組是 simple_bus 協定的發起者。modport 強制執行方向合約，使合成或 lint 工具能夠標記意外的驅動者/接收者不符。

## 帶參數的介面

介面參數的工作方式與模組參數完全相同，允許同一介面服務多種匯流排寬度：

```systemverilog
simple_bus #(.DATA_W(64), .ADDR_W(32)) wide_bus ();
simple_bus #(.DATA_W(8),  .ADDR_W(8))  narrow_bus ();
```

每個例化都有自己獨立大小的欄位寬度。modport 方向保持不變；只有寬度改變。

## 常見陷阱

- **埠宣告中缺少 `modport`。** 若沒有 modport，模組接受整個介面而不進行方向檢查，任何訊號都可以從任意一側驅動，工具無法驗證正確性。請一律指定 modport。
- **驅動 `input` modport 訊號。** 若 `bus.data` 在 modport 中宣告為 `input`，對其進行指定是 modport 違規。Lint 工具會報告此問題；部分模擬器只在闡述時發出警告。請將 modport 違規視為錯誤。
- **例化介面時沒有寫 `()`。** `simple_bus bus_if;` 是型別 `simple_bus` 的宣告，但並未建立具有實際儲存的例化。請寫 `simple_bus bus_if ();` 來例化。
- **在介面中放入合成邏輯。** 介面可包含 `function` 和 `task` 定義，但可合成邏輯應存在於模組中。保持介面作為純粹的連接描述器。
- **工具支援缺口。** 並非所有合成工具都同等支援每個介面特性。參數化介面和介面陣列可能需要變通方案。請儘早驗證工具支援情況。

## 小結

- `interface` 將相關訊號聚合在一個名稱和一個宣告下。
- `modport` 為每個邏輯角色指定名稱和埠方向；請在每個介面埠上使用它。
- 模組透過單一埠連接到介面，縮小了埠列表，使協定更改成為一處編輯。
- 介面首先服務於設計連接性；驗證的益處是額外收穫。

---

[← 套件與範圍](03-packages-and-scope.md) · [目錄](../README.md) · [下一章：程序區塊與運算子 →](05-procedural-and-operators.md)
