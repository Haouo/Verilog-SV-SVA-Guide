# 第一部 · 8. 測試平台基礎（僅提及）

[← 面向合成的撰寫](07-synthesis-aware-coding.md) · [目錄](../README.md) · [下一章：第二部：為何用 SystemVerilog 做設計 →](../part2-systemverilog/01-why-sv-for-design.md)

> **範圍說明。** 本章刻意寫得簡短。驗證（verification），也就是建構測試平台（testbench）、
> UVM、約束隨機激勵、覆蓋率收斂這一整套，是一門自成體系、有其專屬文獻的大學科，**並非**本指南的重點。
> 這裡的目標只是讓設計者認得基本組成元件，並能對自己的區塊做一次快速檢查。
> 想深入了解真正的驗證，請參閱 [附錄 D](../appendices/D-references.md) 的參考資料。

## 學習目標

- 認識測試平台的最小結構。
- 驅動時脈與重置，測試自己的區塊。
- 了解設計與驗證之間的界線所在。

## 設計者的心智模型

簡單的 testbench 是用來產生激勵、觀察行為的工具，並不是 RTL 正確性的證明。它能顯示某個情境跑通了，
卻不會自動陳述那條「永遠都該成立」的設計規則。正是這道缺口，讓 assertion 有了用武之地。

對設計者來說，小型 testbench 的價值在於快和看得見。它讓你把一個區塊先跑起來、看波形，揪出明顯的接線
或重置錯誤。當你發現自己一再盯著波形來判斷某件事「對不對」時，那往往就是一條候選 assertion。

## 什麼是測試平台

測試平台（testbench）是不可合成的程式碼，負責實例化你的設計（即*待測裝置*，DUT）、驅動它的輸入，並檢查它的輸出。它是一支 simulation 程式，所以可以放心使用第 7 章要你擋在 RTL 之外的那些語法構件：`initial`、延遲（delay）與系統任務（system task）。

## 最小測試平台

```verilog
module tb;
    reg        clk = 1'b0;
    reg        rst_n;
    reg        en;
    wire [7:0] count;

    // DUT instance
    counter #(.WIDTH(8)) dut (
        .clk(clk), .rst_n(rst_n), .en(en), .count(count)
    );

    // Clock: toggle every 5 time units -> 10-unit period
    always #5 clk = ~clk;

    // Stimulus
    initial begin
        rst_n = 1'b0; en = 1'b0;   // apply reset
        #20 rst_n = 1'b1;          // release reset
        #10 en = 1'b1;             // start counting
        #100 $finish;              // end simulation
    end

    // Simple monitor
    initial
        $monitor("t=%0t count=%0d", $time, count);
endmodule
```

各個組成部分：

- **時脈產生（Clock generation）**：帶有延遲的 `always` 區塊持續切換 `clk`。
- **激勵（Stimulus）**：`initial` 區塊先套用重置，再隨時間驅動輸入。
- **觀測（Observation）**：`$monitor` 或 `$display` 印出訊號值，`$finish` 結束 simulation 的執行。

這已足夠讓一個區塊跑起來、觀察它的行為，但還不足以*驗證*它。

## 設計在哪裡結束，驗證從哪裡開始

上面這個測試平台只是把數值印出來給人看。真正的驗證會用自我檢查（self-checking）的程式碼取代人工：它預測正確的輸出，在大量定向與隨機情境中自動標出任何差異，同時量測覆蓋率，好知道究竟測到了哪些地方。這一整套機制，包括計分板（scoreboard）、驅動器（driver）、監測器（monitor）、約束隨機產生器與 UVM，屬於驗證工程師的領域。

不過，有一種檢查確實該由設計者負責：斷言（assertion）。斷言和設計擺在一起，把設計者心中的意圖陳述出來，並在*任何*一次 simulation 中自動受到查核，連上面這個簡單的測試平台也算。這正是第三部的主題，也是本指南為何深入講 SVA、卻只在這裡點到測試平台的原因。

> **設計意圖。** 印出的波形說明了發生過什麼，卻說不出那是否正確。
> 設計者在查核上能出的力就是斷言：它把預期行為編成一條條件，交給工具在每次執行時確認，
> 而不是讓人去翻日誌。

## 常見陷阱

- **把目視波形當成「驗證」。** 人工檢視會漏掉案例，也擴展不開來。它適合用在初步啟動（bring-up），不適合用來簽核（sign-off）。
- **讓測試平台的語法構件滲進 RTL。** 請把 `initial`、延遲與 `$display` 留在測試平台裡（第 7 章）。
- **以「測試平台已經在檢查了」為由跳過斷言。** 斷言是從設計內部檢查，在每次 simulation 都有效，並且能在錯誤的源頭就抓到失敗。

## 小結

- 測試平台會實例化 DUT、產生時脈與重置，並以不可合成的語法構件施加激勵。
- 最小測試平台夠用來做初步啟動，但不足以拿來驗證。
- 自我檢查、覆蓋率與 UVM 屬於驗證工程師的領域，超出本指南範疇。
- 設計者的檢查工具是斷言，第三部會完整介紹。

---

[← 面向合成的撰寫](07-synthesis-aware-coding.md) · [目錄](../README.md) · [下一章：第二部：為何用 SystemVerilog 做設計 →](../part2-systemverilog/01-why-sv-for-design.md)
