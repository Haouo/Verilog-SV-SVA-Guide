# 第二部 · 4. 介面與 modport

[← 套件與範圍](03-packages-and-scope.md) · [目錄](../README.md) · [下一章：程序區塊與運算子 →](05-procedural-and-operators.md)

## 學習目標

- 宣告 `interface` 以將相關訊號聚合在一個名稱下。
- 使用 `modport` 為連接到介面的每個角色指定埠方向。
- 用介面來例化與連接模組。
- 理解介面對設計本身的益處，而不僅限於驗證用途。

## 設計者的心智模型

interface 是一束協定，不只是省去一堆埠的捷徑。它替那些本就該一起搬動的訊號取名，也可以把協定專屬的輔助函式或 assertion 放在這些訊號旁邊。`modport` 則說明某個模組在這個協定裡扮演哪一個角色。

當一束訊號的意義不只是「方便」時，就適合用 interface：ready/valid、request/grant、address/data/control，或其他反覆出現的關係。若這些訊號彼此無關，interface 反而會模糊掉重點；若它們構成一個協定，interface 就能讓這個協定在模組邊界上一目了然。

## 介面解決的問題

典型的匯流排或握手（handshake）協定，包含好幾個總是一起傳遞的訊號：資料、位址、valid、ready、寫入致能、位元組致能等等。在普通 Verilog 裡，這些訊號在每個參與協定的模組上都是各自獨立的埠，連接兩個模組就得逐條接過去。協定裡要多加一個訊號，就得改動每個模組、每處例化，既繁瑣又容易出錯。

SystemVerilog 介面（interface）把這些訊號收進一個具名的束（bundle）。這個束只宣告一次、連接一次，要擴充也只在一處進行。

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

介面的語法和模組相似，但裡頭只有訊號宣告，以及選用的 modport、函式和任務。它也像模組一樣可以有參數。但它不是模組：它沒有埠，也無法單獨拿去合成。

## `modport` — 每個角色的方向

介面本身不帶方向資訊。同一個 `data` 訊號，由主機（master）驅動，由從機（slave）讀取。`modport` 為每個邏輯角色附上一個名稱和一組方向：

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

如此一來，`master` 和 `slave` 各自圈定了介面訊號的一個子集及其方向，模組則宣告自己用的是哪一個 modport。

## 將介面用作埠

模組宣告介面埠的方式，是寫出介面型別和 modport：

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

兩個模組都用欄位名稱存取訊號（`bus.valid`、`bus.data` 等），不必再去打理一長串個別線路。

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

介面就是單一的連接點。要在 `simple_bus` 裡新增一個訊號，只需改動介面宣告，以及用到該新訊號的那一兩個模組，不必動到每一份埠列表、每一處例化。

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

各家合成工具對介面陣列的支援程度不一，在正式 RTL 採用之前，請先查清楚你的工具支援情況。

## 介面與測試平台

介面在驗證中用得很多，測試平台的驅動器（driver）和監視器（monitor）都連到同一個介面。這個用途不在本指南範圍內（見附錄 D）。本章要強調的是：介面為設計本身帶來簡潔而有型別的連接，它縮短了埠列表、讓連接受型別檢查，也為協定提供了單一的定義點。

> **設計意圖。** 介面是用程式碼寫出來的協定。當你在模組的埠列表中看到 `simple_bus.master bus`，一眼就知道這個模組是 simple_bus 協定的發起者。modport 強制執行方向合約，讓合成或 lint 工具能夠揪出意外的驅動者／接收者方向不符。

## 帶參數的介面

介面參數的運作方式和模組參數完全一樣，讓同一個介面能服務多種匯流排寬度：

```systemverilog
simple_bus #(.DATA_W(64), .ADDR_W(32)) wide_bus ();
simple_bus #(.DATA_W(8),  .ADDR_W(8))  narrow_bus ();
```

每個例化的欄位寬度各自獨立。modport 的方向不變，變的只有寬度。

## 常見陷阱

- **埠宣告漏掉 `modport`。** 沒有 modport，模組就照單全收整個介面、不做方向檢查，任何訊號都能從任一側驅動，工具也無從驗證正確性。請一律指定 modport。
- **驅動宣告為 `input` 的 modport 訊號。** 若 `bus.data` 在 modport 中宣告為 `input`，對它指定就是 modport 違規。lint 工具會報告，部分 simulator 只在闡述時警告。請把 modport 違規當成錯誤看待。
- **例化介面時漏寫 `()`。** `simple_bus bus_if;` 只是宣告了一個型別為 `simple_bus` 的東西，並未建立帶有實際儲存的例化。要例化，請寫 `simple_bus bus_if ();`。
- **把合成邏輯塞進介面。** 介面可以放 `function` 和 `task` 定義，但可合成的邏輯應該留在模組裡。請讓介面維持為單純的連接描述。
- **工具支援的落差。** 並非所有合成工具都對每項介面特性一視同仁，參數化介面和介面陣列可能需要變通做法。請及早確認工具支援情況。

## 小結

- `interface` 把相關訊號收在一個名稱、一份宣告之下。
- `modport` 為每個邏輯角色指定名稱和埠方向，請在每個介面埠上都用它。
- 模組經由單一埠連到介面，縮短了埠列表，也讓協定的變動只需改一處。
- 介面首先服務於設計的連接性，驗證上的好處則是額外收穫。

---

[← 套件與範圍](03-packages-and-scope.md) · [目錄](../README.md) · [下一章：程序區塊與運算子 →](05-procedural-and-operators.md)
