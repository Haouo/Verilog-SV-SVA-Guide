# 第一部 · 6. 有限狀態機

[← 循序邏輯](05-sequential-logic.md) · [目錄](../README.md) · [下一章：面向合成的撰寫 →](07-synthesis-aware-coding.md)

## 學習目標

- 將有限狀態機（FSM）組織為清楚、分離的關注點。
- 撰寫推薦的雙區塊（two-block）風格。
- 理解 Moore 與 Mealy 輸出的差異。
- 選擇狀態編碼並避免鎖死狀態（lockup state）。

## RTL 中的有限狀態機

有限狀態機（finite state machine，FSM）是以一組狀態、狀態之間的轉換，以及各狀態產生的輸出來建模的控制邏輯。設計中大多數控制路徑——握手（handshake）、協定、仲裁器——都是 FSM。挑戰不在於概念本身，而在於寫出清晰且能乾淨合成的程式碼。

FSM 涉及三個關注點：

1. **狀態暫存器（state register）** — 儲存當前狀態的帶時脈元件。
2. **次態邏輯（next-state logic）** — 決定下一個狀態的組合邏輯。
3. **輸出邏輯（output logic）** — 產生輸出的組合邏輯。

不同的撰寫風格在於如何組合這三個關注點。

## 雙區塊風格（推薦）

將帶時脈的狀態暫存器與組合的次態及輸出邏輯分開。這使循序與組合部分清楚劃分。

```verilog
module fsm (
    input  wire clk,
    input  wire rst_n,
    input  wire start,
    input  wire done,
    output reg  busy
);
    // State encoding (see encoding section)
    localparam [1:0] IDLE = 2'd0,
                     RUN  = 2'd1,
                     WAIT = 2'd2;

    reg [1:0] state, next;

    // Block 1: state register (sequential)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) state <= IDLE;
        else        state <= next;
    end

    // Block 2: next-state and output logic (combinational)
    always @* begin
        next = state;     // default: hold state, avoids a latch
        busy = 1'b0;      // default output
        case (state)
            IDLE: if (start) next = RUN;
            RUN:  begin
                      busy = 1'b1;
                      if (done) next = WAIT;
                  end
            WAIT: next = IDLE;
            default: next = IDLE;   // recover from illegal states
        endcase
    end
endmodule
```

組合區塊頂端的預設值至關重要：`next = state` 與 `busy = 1'b0` 確保每條路徑都對兩個訊號賦值，因此不會推斷出閂鎖器（第 4 章）。

部分設計者偏好*三區塊*風格，將次態與輸出分成兩個獨立的組合區塊。這同樣有效；當輸出邏輯夠複雜、值得擁有自己的區塊時使用它。*單區塊*風格將所有內容放入帶時脈的區塊也可行，但輸出會被暫存，改變其時序——選用前請確認這是你的意圖。

## Moore 與 Mealy

- **Moore** 輸出僅取決於當前狀態。上例中的 `busy` 是 Moore 輸出：它由狀態決定，而非由輸入決定。Moore 輸出在整個狀態期間保持穩定，易於推理。
- **Mealy** 輸出取決於當前狀態*與*輸入。它們可以提前一個週期響應，但也可能隨輸入產生毛刺（glitch）並使時序複雜化。

除非確實需要 Mealy 輸出提前響應的特性，否則對控制訊號優先選用 Moore 輸出。

## 狀態編碼

`localparam` 的數值選擇了狀態對位元的映射方式：

- **二進制（Binary）** — `2'd0, 2'd1, ...`。使用最少的正反器；次態邏輯較多。
- **一位元熱碼（One-hot）** — 每個狀態對應一個位元（`4'b0001, 4'b0010, ...`）。正反器較多，但次態邏輯更簡單、速度更快。在正反器充足的 FPGA 上常見。
- **格雷碼（Gray）** — 相鄰狀態只差一個位元；在特定情況下有用。

無論採用哪種編碼，都應以具名的 `localparam` 常數表示狀態，使編碼決策集中在一處。許多合成工具能自動重新編碼 FSM，但明確的具名狀態讓原始碼保持可讀。

## 非法狀態與恢復

以二進制編碼三個狀態時，2 位元中的 `2'b11` 未被使用。雜訊、單粒子翻轉（SEU）或錯誤可能使 FSM 落入此狀態。`default: next = IDLE` 分支能將任何非預期狀態導回安全狀態。務必提供此分支。這也是放置斷言的自然位置：「狀態永遠是合法值之一」（第三部）。

> **設計意圖。** FSM *就是*被明確表達的設計意圖：這些是合法狀態，
> 這些是允許的轉換，每個狀態各自驅動什麼輸出。
> 雙區塊風格、具名狀態，以及帶有恢復的 `default`，清楚地寫出了這個意圖。
> 斷言在之後證明狀態機從不執行你未允許的轉換。

## 常見陷阱

- **組合區塊缺少預設值。** 遺漏 `next = state` 或預設輸出會推斷出閂鎖器。
- **使用魔術數字狀態。** 請使用具名的 `localparam` 常數。
- **沒有非法狀態恢復。** 加入 `default` 回到安全狀態。
- **非預期的 Mealy 輸出。** 在輸出邏輯中讀取輸入會使輸出在那些輸入上組合響應；只在刻意這樣做時才這麼寫。
- **使用單區塊風格時意外地暫存輸出**，而原本想要的是組合輸出。

## 小結

- FSM 包含狀態暫存器、次態邏輯與輸出邏輯。
- 雙區塊風格乾淨地分離循序與組合部分；預設組合輸出以避免閂鎖器。
- 對穩定的控制訊號優先選用 Moore 輸出。
- 以 `localparam` 命名狀態，刻意選擇編碼，並始終提供非法狀態的恢復路徑。

---

[← 循序邏輯](05-sequential-logic.md) · [目錄](../README.md) · [下一章：面向合成的撰寫 →](07-synthesis-aware-coding.md)
