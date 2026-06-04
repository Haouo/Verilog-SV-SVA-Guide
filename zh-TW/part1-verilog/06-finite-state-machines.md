# 第一部 · 6. 有限狀態機

[← 循序邏輯](05-sequential-logic.md) · [目錄](../README.md) · [下一章：面向合成的撰寫 →](07-synthesis-aware-coding.md)

## 學習目標

- 將有限狀態機（FSM）組織為清楚、分離的關注點。
- 撰寫推薦的雙區塊（two-block）風格。
- 理解 Moore 與 Mealy 輸出的差異。
- 選擇狀態編碼並避免鎖死狀態（lockup state）。

## 設計者的心智模型

FSM 是一份具名的控制契約。state register 指出這個區塊目前處於哪個階段；next-state logic 指出哪些
transition 合法；output logic 指出每個階段對設計其餘部分許下什麼承諾。把這三種角色分開，狀態機就更好
debug，也更容易補上 assertion。

不要只把 FSM 當成一堆 `case` 分支來讀，要把它讀成一張圖：哪些 state 合法、哪些 edge 允許、什麼 event
會觸發移動、若 state 變得非法時有沒有復原路徑。這張圖通常也是日後推導 assertion 的最佳起點。

## RTL 中的有限狀態機

有限狀態機（finite state machine，FSM）是一種控制邏輯，由一組狀態、狀態之間的轉換，以及各狀態產生的輸出共同建模。設計裡大多數控制路徑，例如握手（handshake）、協定、仲裁器，本質上都是 FSM。難處不在概念本身，而在於把程式碼寫得清晰、又能乾淨地合成。

FSM 涉及三個關注點：

1. **狀態暫存器（state register）** — 儲存當前狀態的帶時脈元件。
2. **次態邏輯（next-state logic）** — 決定下一個狀態的組合邏輯。
3. **輸出邏輯（output logic）** — 產生輸出的組合邏輯。

各種撰寫風格的差別，就在於如何把這三個關注點分組。

## 雙區塊風格（推薦）

把帶時脈的狀態暫存器，跟組合的次態與輸出邏輯分開來寫，讓循序與組合兩部分清楚劃分。

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

組合區塊頂端的預設值非常重要：`next = state` 與 `busy = 1'b0` 確保每條路徑都會對這兩個訊號賦值，因此不會推斷出閂鎖器（第 4 章）。

也有設計者偏好*三區塊*風格，把次態與輸出拆成兩個各自獨立的組合區塊。這同樣有效，適合在輸出邏輯夠複雜、值得獨立成一個區塊時採用。把所有東西全塞進帶時脈區塊的*單區塊*風格也行得通，只是輸出會被暫存而改變時序，選用前要先確認這正是你要的。

## Moore 與 Mealy

- **Moore** 輸出只取決於當前狀態。上例的 `busy` 就是 Moore 輸出：它由狀態決定，而非由輸入決定。Moore 輸出在整個狀態期間保持穩定，也較好推敲。
- **Mealy** 輸出取決於當前狀態*與*輸入。它能提早一個週期反應，但也可能隨輸入產生毛刺（glitch），讓時序變得更複雜。

除非確實需要 Mealy 輸出提早反應的特性，否則控制訊號優先採用 Moore 輸出。

## 狀態編碼

`localparam` 的數值決定了狀態如何對應到位元：

- **二進制（Binary）**：`2'd0, 2'd1, ...`。用的正反器最少，但次態邏輯較多。
- **一位元熱碼（One-hot）**：每個狀態對應一個位元（`4'b0001, 4'b0010, ...`）。正反器較多，但次態邏輯更簡單、速度更快，在正反器充足的 FPGA 上很常見。
- **格雷碼（Gray）**：相鄰狀態只差一個位元，在特定情況下派得上用場。

不論採用哪種編碼，都應以具名的 `localparam` 常數來表示狀態，讓編碼決策集中在一處。許多合成工具能自動重新替 FSM 編碼，但具名的明確狀態能讓原始碼保持可讀。

## 非法狀態與恢復

以二進制把三個狀態編進 2 位元時，`2'b11` 這個值用不到。雜訊、單粒子翻轉（SEU）或臭蟲都可能讓 FSM 落到這個狀態。`default: next = IDLE` 分支會把任何非預期狀態導回安全狀態，務必提供這個分支。這裡也是放斷言的好地方：「狀態永遠是合法值之一」（第三部）。

> **設計意圖。** FSM *本身*就是把設計意圖明講出來：這些是合法狀態，
> 這些是允許的轉換，每個狀態各自驅動什麼輸出。
> 雙區塊風格、具名狀態，加上會復原的 `default`，把這份意圖寫得清清楚楚。
> 斷言則在之後證明：狀態機從不執行你沒允許過的轉換。

## 常見陷阱

- **組合區塊缺少預設值。** 漏掉 `next = state` 或預設輸出會推斷出閂鎖器。
- **使用魔術數字狀態。** 請改用具名的 `localparam` 常數。
- **沒有非法狀態的復原路徑。** 加上一個回到安全狀態的 `default`。
- **非預期的 Mealy 輸出。** 在輸出邏輯裡讀取輸入，會讓輸出隨那些輸入組合反應；只在刻意如此時才這麼寫。
- **想要組合輸出，卻在單區塊風格下意外暫存了輸出。**

## 小結

- FSM 由狀態暫存器、次態邏輯與輸出邏輯組成。
- 雙區塊風格能乾淨地切開循序與組合部分；替組合輸出設預設值以避免閂鎖器。
- 穩定的控制訊號優先採用 Moore 輸出。
- 以 `localparam` 替狀態命名，刻意挑選編碼，並一律為非法狀態留好復原路徑。

---

[← 循序邏輯](05-sequential-logic.md) · [目錄](../README.md) · [下一章：面向合成的撰寫 →](07-synthesis-aware-coding.md)
