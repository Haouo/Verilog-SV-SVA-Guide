# 第一部 · 1. 模組與階層

[← 導論](../00-introduction.md) · [目錄](../README.md) · [下一章：資料型別與數值 →](02-data-types-and-values.md)

## 學習目標

- 以清楚的埠（port）列表宣告模組。
- 實例化（instantiate）模組並以名稱連接。
- 建立階層，並理解它如何闡述（elaborate）。
- 傳遞參數讓模組可重複使用。

## 設計者 mental model

`module` 不只是文字容器，而是 design 用來命名一塊 hardware、宣告 boundary 上有哪些 signal、
並讓 elaboration 建出 instance hierarchy 的單位。讀一個 module 時，先把 port list 和
parameter 視為 contract，再往下看 implementation。

好的 hierarchy 會降低一次需要理解的 context。caller 不應該需要知道 child block 裡每個
internal register；它應該只需要理解 ports、parameter 的意義，以及 timing expectation。
所以本章不只講 `module ... endmodule` syntax，也會說明 naming、instantiation 和
parameterization，因為這些共同決定 design boundary 是否清楚。

## 模組是設計的基本單位

`module` 是 Verilog 的基本建構單元。它有名稱、一份埠列表，以及描述行為或結構的主體。
硬體是透過在模組中實例化其他模組來建構，形成一棵樹。頂層模組是樹根，葉節點則是基本邏輯。

```verilog
module adder (
    input  wire [7:0] a,
    input  wire [7:0] b,
    output wire [8:0] sum
);
    assign sum = a + b;
endmodule
```

本指南採用上方的 **ANSI 埠樣式**，將方向、型別與位元寬度都寫在埠列表中。較舊的
非 ANSI 樣式會在主體中分開宣告埠及其方向。請優先使用 ANSI 樣式：它較精簡，並把每個埠
的完整描述集中在一處。

## 埠與方向

每個埠都有方向：

- `input` — 由外部驅動，內部讀取。
- `output` — 內部驅動，外部讀取。
- `inout` — 雙向，用於含三態（tri-state）驅動器的匯流排。

在可合成 RTL 中，多數埠是 `input` 或 `output`。埠的位元寬度寫成 `[msb:lsb]`，幾乎
都是 `[N-1:0]`。

## 實例化與連接

實例化的做法是：指明模組、為實例命名，並連接其埠。請一律**以名稱**連接，而非位置。
具名連接能在埠列表變動時保持正確，也讓意圖一目了然。

```verilog
module datapath (
    input  wire [7:0] x,
    input  wire [7:0] y,
    output wire [8:0] total
);
    // 具名連接：.port(signal)
    adder u_adder (
        .a   (x),
        .b   (y),
        .sum (total)
    );
endmodule
```

位置連接——`adder u_adder (x, y, total)`——雖可運作但脆弱。只要有一個埠重新排序或插入，
就會悄悄接錯線。具名連接是正式 RTL 的準則。

## 階層與闡述

工具讀入設計時會執行*闡述（elaboration）*：選定頂層模組、建立其實例，再建立這些實例的
實例，依此類推，直到整棵樹建構完成。參數會在這個步驟解析，發生在 simulation 或合成開始之前。
結果是一個完全展開、由具體模組構成的階層。

某模組內的訊號，除非透過埠，否則在其他模組中不可見。這是刻意的設計。埠是模組與其
父模組之間的契約；讓契約保持明確，正是使設計可組合的關鍵。

## 參數讓模組可重複使用

`parameter` 是編譯期常數，父模組可在實例化時覆寫。請用參數表示位元寬度、深度等尺寸，
讓單一模組服務多種情況。

```verilog
module adder #(
    parameter WIDTH = 8
) (
    input  wire [WIDTH-1:0] a,
    input  wire [WIDTH-1:0] b,
    output wire [WIDTH:0]   sum
);
    assign sum = a + b;
endmodule

// 在實例化時覆寫寬度。
adder #(.WIDTH(16)) u_adder16 (.a(a16), .b(b16), .sum(sum17));
```

如同埠一樣，請以名稱覆寫參數。寫死寬度的模組只能用一次；參數化的模組則處處可用。

> **設計意圖。** 埠列表就是一個區塊以介面形式陳述的意圖：這些是跨越邊界的訊號，
> 這些是它們的方向與寬度。清楚、具名、參數化的埠列表，能準確告訴下一位工程師
> 這個區塊該如何連接。

## 常見陷阱

- **位置連接埠。** 埠變動時會悄悄接錯。請一律以名稱連接。
- **在同一模組混用 ANSI 與非 ANSI 樣式。** 選定 ANSI 並保持一致。
- **意外的隱含線網。** 未宣告的訊號會變成 1 位元的 `wire`。埠名打錯字可能產生一條
 多餘的 1 位元線網與難找的錯誤。（線網宣告見第 2 章；可考慮以 \`\`default_nettype none\`
 關閉隱含線網。）
- **寫死寬度。** 會妨礙重複使用。從一開始就把尺寸參數化。

## 小結

- 模組有名稱、埠與主體；設計是由模組實例構成的樹。
- 使用 ANSI 埠樣式，並以名稱連接實例。
- 闡述會展開階層並在執行前解析參數。
- 參數讓單一模組成為可重複使用、可調整尺寸的元件。

---

[← 導論](../00-introduction.md) · [目錄](../README.md) · [下一章：資料型別與數值 →](02-data-types-and-values.md)
