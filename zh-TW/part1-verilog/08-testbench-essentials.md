# 第一部 · 8. 測試平台基礎（僅提及）

[← 面向合成的撰寫](07-synthesis-aware-coding.md) · [目錄](../README.md) · [下一章：第二部：為何用 SystemVerilog 做設計 →](../part2-systemverilog/01-why-sv-for-design.md)

> **範圍說明。** 本章刻意保持簡短。驗證（verification）——建構測試平台（testbench）、
> UVM、約束隨機激勵、覆蓋率收斂——是一門有其自身文獻的大型學科，**並非**本指南的重點。
> 此處的目標僅是讓設計者認識基本組成元素，並能對自己的區塊執行快速檢查。
> 如需完整的驗證資訊，請參閱 [附錄 D](../appendices/D-references.md) 中的參考資料。

## 學習目標

- 認識測試平台的最小結構。
- 驅動時脈與重置以對自己的區塊進行測試。
- 了解設計與驗證之間的界線所在。

## 設計者 mental model

simple testbench 是產生 stimulus、觀察 behavior 的方式，不是 RTL 正確性的 proof。它可以顯示
某個 scenario 成功，但它本身沒有陳述「永遠應該成立」的 design rule。那個缺口就是 assertion
有價值的地方。

對 designer 來說，小型 testbench 的價值是 speed 和 visibility。它讓你 bring up 一個 block、
看 waveform、抓 obvious wiring 或 reset mistake。當你發現自己反覆看 waveform 來判斷某件事
「對不對」時，那通常就是一條 candidate assertion。

## 什麼是測試平台

測試平台（testbench）是不可合成的程式碼，用於實例化你的設計（即*待測裝置*，DUT），驅動其輸入，並檢查其輸出。它是一個simulation程式，因此可自由使用第 7 章要求排除在 RTL 之外的語言結構：`initial`、延遲（delay）與系統任務（system task）。

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

各組成部分：

- **時脈產生（Clock generation）** — 帶有延遲的 `always` 區塊切換 `clk`。
- **激勵（Stimulus）** — `initial` 區塊套用重置，再隨時間驅動輸入。
- **觀測（Observation）** — `$monitor` 或 `$display` 印出訊號值；`$finish` 結束simulation執行。

這已足夠讓一個區塊啟動並觀察其行為，但尚不足以*驗證*它。

## 設計在哪裡結束，驗證從哪裡開始

上述測試平台印出數值供人檢視。真正的驗證用自我檢查（self-checking）程式碼取代人工：它預測正確輸出，並在大量定向與隨機場景中自動標記任何差異，同時量測覆蓋率以了解測試了哪些內容。這套機制——計分板（scoreboard）、驅動器（driver）、監測器（monitor）、約束隨機產生器、UVM——是驗證工程師的領域。

然而，有一種檢查確實屬於設計者：斷言（assertion）。斷言與設計並存，陳述設計者持有的意圖，並在*任何*simulation中自動被檢查——包括上面這個簡單的測試平台。這正是第三部的主題，也是本指南深入介紹 SVA 而只在此處提及測試平台的原因。

> **設計意圖。** 印出的波形顯示了發生了什麼，但它無法說明那是否正確。
> 設計者對檢查的貢獻是斷言，它將預期行為編碼為可讓工具——而非閱讀日誌的人——
> 在每次執行時確認的條件。

## 常見陷阱

- **將目視波形當作「驗證」。** 人工檢視會遺漏案例且無法規模化。它用於初步啟動（bring-up），不用於簽核（sign-off）。
- **讓測試平台語言結構滲入 RTL。** 請將 `initial`、延遲與 `$display` 保留在測試平台中（第 7 章）。
- **因「測試平台已在檢查」而跳過斷言。** 斷言從內部檢查設計，在每次simulation中都有效，並在錯誤的源頭捕捉失敗。

## 小結

- 測試平台實例化 DUT，產生時脈與重置，並以不可合成的語言結構施加激勵。
- 最小測試平台足以用於初步啟動，但不足以用於驗證。
- 自我檢查、覆蓋率與 UVM 是驗證工程師的領域——超出本指南範疇。
- 設計者的檢查工具是斷言，第三部將完整介紹。

---

[← 面向合成的撰寫](07-synthesis-aware-coding.md) · [目錄](../README.md) · [下一章：第二部：為何用 SystemVerilog 做設計 →](../part2-systemverilog/01-why-sv-for-design.md)
