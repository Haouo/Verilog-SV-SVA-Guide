# 第三部 · 9. bind 與放置

[← clock 與 reset](08-clocking-and-reset.md) · [目錄](../README.md) · [下一章：RTL assertion pattern →](10-rtl-assertion-patterns.md)

## 學習目標

- 決定 assertion 放在何處：內嵌於 RTL，還是放在獨立模組中。
- 用 `bind` 在不修改設計的前提下，把 assertion 附加上去。
- bind 到某個模組類型，或 bind 到某個特定實例。
- 用 port 把設計訊號傳入被 bind 的 checker。
- 選擇一種同時符合設計與驗證權責歸屬的放置風格。

## 設計者的心智模型

放置位置決定一條 assertion 歸誰負責，以及它能看見哪些訊號。內嵌的 assertion 與 RTL 寫在一起，最適合用來表達設計者自己的局部契約。獨立的 assertion 模組則適合兩種場合：必須在不修改既有設計的情況下加上檢查，或驗證環境想把自己的 checker 分開管理。

`bind` 之所以強大，在於它把原始碼的歸屬與觀察的位置分開了。但如果被 bind 的模組依賴脆弱的內部名稱或語焉不詳的階層路徑，也很容易誤用。良好的放置會讓一條 assertion 的權限與可見範圍一目了然。

## assertion 放在哪裡

concurrent assertion 幾乎可以放在任何能放連續陳述的地方：設計模組本身、獨立模組、`interface`，或 `checker` 之中。選擇主要關乎權責歸屬與侵入程度。

- **內嵌（inline）** assertion 緊貼著它所檢查的 RTL。在脈絡中易讀，並隨程式碼一起移動，但會增加設計檔案的行數，並需要對它的編輯權限。
- **獨立（separate）** assertion 放在自己的模組中，與 RTL 分開，之後再連接起來。設計檔案維持不動；當 RTL 為共用、由工具產生，或屬於其他團隊所有時，這一點很重要。

兩者編譯與執行的結果完全相同。問題在於這個檢查應該放在設計原始碼*之中*，還是放在它*旁邊*。

## 內嵌 assertion

當設計者擁有 RTL，且該檢查表達的正是設計者自己的意圖時，內嵌是最簡單的放置方式。assertion 讀起來就是模組契約的一部分：

```systemverilog
module fifo_ctrl (input logic clk, rst_n, wr_en, rd_en, full, empty /* ... */);

    default clocking cb @(posedge clk); endclocking
    default disable iff (!rst_n);

    // Intent stated right where the signals are declared
    assert property (wr_en |-> !full);
    assert property (rd_en |-> !empty);

    // ... rest of the controller ...
endmodule
```

將 assertion 放在它所約束的邏輯旁邊，使下一位讀者一眼看出意圖，並讓檢查與程式碼在每次修改中保持同步。

## 獨立的 assertion module

當 assertion 由驗證工程師撰寫，或 RTL 不得被觸碰時，將它們收攏到自己的模組中。該模組以 port 宣告相同的訊號，且只包含檢查：

```systemverilog
// A pure-assertion module: no logic, only checks
module fifo_assertions (
    input logic clk, rst_n,
    input logic wr_en, rd_en, full, empty
);
    default clocking cb @(posedge clk); endclocking
    default disable iff (!rst_n);

    assert property (wr_en |-> !full);
    assert property (rd_en |-> !empty);
endmodule
```

這個模組現在必須連接到設計上。在 RTL 內手動實例化它會違背初衷，因為那會修改到設計檔案。`bind` 這個語法構件能在不做該修改的情況下完成連接。

## bind：不修改即可附加

`bind` 從外部把一個模組（或 `checker`、`interface`）實例化*進入*另一個模組。設計原始碼完全不動；連接另外宣告，通常放在驗證檔案中：

```systemverilog
// Attach fifo_assertions to every instance of module fifo
bind fifo fifo_assertions u_fifo_sva (
    .clk    (clk),
    .rst_n  (rst_n),
    .wr_en  (wr_en),
    .rd_en  (rd_en),
    .full   (full),
    .empty  (empty)
);
```

這一行可讀作：「在模組 `fifo` 內部，建立 `fifo_assertions` 的一個實例 `u_fifo_sva`，把它的 port 接到這些名稱上。」右側的名稱是*在 `fifo` 的範圍中*解析的，因此會直接指向該模組的內部訊號，包括那些並非 `fifo` port 的訊號。這正是 `bind` 的關鍵威力：assertion 模組可以觀察設計的內部狀態，而不必把該狀態暴露在任何邊界上。

## bind 到類型或實例

`bind` 之後的第一個識別符選定目標。有兩種形式。

### 依模組類型 bind

指定一個模組類型，會將 checker 附加到該模組的*每一個*實例：

```systemverilog
// Every fifo in the whole design gets these assertions
bind fifo fifo_assertions u_sva (.clk(clk), .rst_n(rst_n) /* ... */);
```

對於可重用的區塊，這是常見的選擇：檢查只寫一次，便會跟隨該區塊出現在每個被實例化之處。

### 依實例 bind

指定一個特定的實例路徑，會將 checker 只附加到該實例：

```systemverilog
// Only this one fifo instance is checked
bind dut.u_rx_fifo fifo_assertions u_sva (.clk(clk), .rst_n(rst_n) /* ... */);
```

逐實例 bind 適合只套用於一個位置的檢查，例如某個深度或協定與其同類不同的 fifo，或某個正在重點除錯的單一實例。

## 傳遞 port 與參數

被 bind 的模組以一般的 port 連接，遵循所有常規規則。實務上有兩點需要注意。

- **Port 運算式在目標的範圍中求值。** 每個連接的右側指向被綁入模組內可見的訊號，因此你能取得內部線網，而不只是目標的 port。
- **參數可以前傳。** 帶參數的 checker 可以接收目標自己的參數，讓檢查隨實例的尺寸調整：

```systemverilog
// Forward the design's WIDTH into the parameterized checker
bind alu #(.WIDTH(WIDTH)) alu_assertions u_sva (
    .clk (clk),
    .a   (a),
    .b   (b),
    .y   (result)
);
```

前傳參數使一個 checker 在不同寬度、深度或模式的實例間皆正確，而不必為每種配置另外撰寫一個 checker。

> **設計意圖。** 放置關乎 assertion 捕捉的是*誰的*意圖，以及該意圖可以存在於*何處*。內嵌 assertion 是設計者自己的契約，陳述於 RTL 之中。被 bind 的 assertion module 讓驗證工程師能將意圖附加到他們不該編輯的設計上，同時仍能觸及其內部狀態。`bind` 將檢查與原始碼解耦：設計保持乾淨，檢查保持獨立，而兩者描述的是同一份硬體。

## 常見陷阱

- **為了實例化 checker 而修改 RTL。** 這等於重新引入 `bind` 本要避免的侵入。請在獨立檔案中用 `bind` 宣告連接。
- **本意只針對一個實例卻依類型 bind。** 類型 bind 命中每一個實例；當檢查僅針對其中一個時，請使用實例路徑。
- **port 方向或寬度不符。** 被 bind 的模組遵循一般 port 規則；寬度或方向不符會是錯誤或無聲截斷，與任何實例化相同。
- **忘記前傳參數。** 寫死寬度的 checker 在尺寸不同的實例上會出錯。請前傳目標的參數。
- **誤以為名稱在 bind 檔案的範圍中解析。** Port 運算式是在*目標*模組的範圍中解析，而不是在 bind 陳述所在的範圍；請依此引用設計的內部名稱。

## 小結

- assertion 可內嵌於 RTL，或放在獨立模組中；兩者執行結果相同。
- 內嵌放置適合設計者自己的意圖；獨立模組適合針對不得編輯的 RTL 所做的檢查。
- `bind` 從外部將 assertion module 實例化進設計，不更動設計原始碼。
- 依模組類型 bind 以涵蓋每個實例，或依實例路徑 bind 以涵蓋單一實例。
- Port 運算式在目標的範圍中解析，因此被 bind 的模組能觀察內部訊號；前傳參數可使 checker 在各實例間保持正確。

---

[← clock 與 reset](08-clocking-and-reset.md) · [目錄](../README.md) · [下一章：RTL assertion pattern →](10-rtl-assertion-patterns.md)
