# 第三部 · 15. checker 與 library

[← formal verification 入門](14-formal-verification-primer.md) · [目錄](../README.md) · [下一章：除錯與反樣式 →](16-debugging-and-antipatterns.md)

## 學習目標

- 將 `checker` 構造用作 assertion 的可重用容器。
- 將訊號與參數傳入 checker，並像模組一樣 bind（bind）它。
- 比較 `checker` 與 property、以及與 assertion module 之間的差異。
- 認識標準的可重用 assertion library：OVL 與 Accellera SVA library。
- 為跨專案的重用而封裝你自己的 assertion。

## 設計者的心智模型

checker 是一個帶有具名介面、可重用的 assertion 容器。它讓團隊把一條協定規則封裝一次，再到同樣規則出現的地方實例化。如此一來，library 就成了設計意圖的一套詞彙：不溢位、收到 accept 前保持穩定、one-hot、延遲有界等等。

好用的 checker 介面應該小而精準。它只暴露陳述規則所需的訊號、參數、clocking 與 reset，並把呼叫端不該重寫的 SVA 細節藏起來。唯有當 checker 名稱與參數讓意圖一眼可辨時，重用才有價值。

## 從問題開始

當同一種 handshake 在十個模組出現時，複製十份 property 看似最快，但很快會變成維護負擔：有些忘了 cover antecedent，有些 latency 參數不同，有些 reset 條件漏掉。這時真正要重用的不是幾行語法，而是一個完整的協定檢查單元。

checker 和 library 的目的，就是把這個單元包起來：明確的 port、參數、clock/reset 慣例、assert 與 cover 一起出現。呼叫端只提供訊號與協定參數，不需要重新發明 property 內部怎麼寫。

## checker 構造

**checker** 是 SystemVerilog 中專為容納 assertion 而設的容器，裡頭裝著 assertion、cover，以及支援它們的建模程式碼。它類似模組，有 port，可以實例化或 bind，但它專用於驗證：它可以包含 `assert`、`assume`、`cover`、sequence、property，以及有限的程序化建模，而且天生就是設計來重用的。

```systemverilog
// A reusable request/acknowledge checker
checker req_ack_chk (logic clk, logic rst_n, logic req, logic ack, int unsigned n);
    default clocking cb @(posedge clk); endclocking
    default disable iff (!rst_n);

    a_ack: assert property ($rose(req) |-> ##[1:n] ack);
    c_req: cover  property ($rose(req));
endchecker
```

這個 checker 把一個完整、能自我說明的意圖單元封裝在一個具名介面之後，這個單元包含 assertion、它配對的 cover，以及 clock 與 reset 慣例。只要這種握手形態反覆出現，實例化一次就把整個組合套用上去。

## 實例化與 bind checker

checker 像模組一樣以名稱加 port 連接來實例化。將它附加到設計的自然方式是 `bind`（第 9 章），使設計原始碼維持不動：

```systemverilog
// Attach the checker to every fifo instance, forwarding its ports
bind fifo req_ack_chk u_chk (
    .clk   (clk),
    .rst_n (rst_n),
    .req   (rd_req),
    .ack   (rd_ack),
    .n     (4)
);
```

因為 checker 接受 port 與參數，一份定義就能適配許多場址：不同的訊號名稱靠 port 對映，而像延遲界限 `n` 這樣的參數則逐實例調校檢查。把 checker bind 上去，可重用的驗證程式碼就完全留在 RTL 之外。

## checker 與 property、與 assertion module

三種構造都能容納 assertion；它們處於不同的尺度。

- **named property** 是最小的重用單元：一條帶引數的時序陳述。用於單一反覆出現的形態（第 7 章）。
- **`checker`** 是專為此打造的組合，裝著數條相關的 assertion、cover 與支援建模，並有自己的 port 與參數。當一*組*相關的檢查需要一起搬動時，例如某協定的整份契約，就用它。
- **單純的 assertion module**（第 9 章）同樣裝著 assertion，但它是一個被改用於驗證的一般模組。`checker` 才是語言*為這份工作*提供的構件：它允許模組可能會限制的驗證建模，也把意圖示意得更清楚。

請挑最小而合適的：單一規則用 property，相關的一組用 checker，唯有需要 checker 沒有的模組層級功能時，才保留一個完整模組。

## 可重用的 assertion library

常見的檢查你很少需要從頭寫起。有兩套廣為可得的可重用 assertion。

### OVL（Open Verification Library）

OVL 是 Accellera 的一套預先封裝好的 checker 元件 library，涵蓋溢位、one-hot、handshake、FIFO 等等，可從 Verilog 與 SystemVerilog 使用。每個 checker 都用描述特定情形的參數來實例化。OVL 比廣泛的 SVA 支援還早出現，在工具或流程偏好可實例化的 checker、而非內嵌 SVA 的場合，至今仍然管用。

### Accellera SVA 標準 checker library

SVA 標準 checker library 是一組以原生 SVA 寫成的 `checker` 元件，用參數化 checker 涵蓋同樣反覆出現的意圖：資料穩定性、handshake、gray code、奇偶校驗等等。由於是原生 SVA，它能與你自己的 assertion 乾淨地組合，bind 的方式也一樣。

```systemverilog
// Conceptual: instantiate a library checker rather than hand-writing it
// (exact name and ports depend on the library version)
bind dma assert_handshake #(.MIN(1), .MAX(8))
    u_hs (.clk(clk), .reset_n(rst_n), .req(req), .ack(ack));
```

> **設計意圖。** library 把反覆出現的設計意圖轉化成一套詞彙。「不溢位」、「gray 只變一個位元」、「N 週期內被回應」，都是一個區塊接一個區塊不斷冒出來的意圖；checker library 把每個意圖命名一次、驗證過、也參數化，於是設計者只要實例化意圖，不必再重新推導 SVA。這裡的重用不只是圖個方便，library 裡的檢查身經百戰，這就讓它比一條剛手寫出來的 property 更值得信賴。

## 封裝你自己的 assertion

專案特定的意圖也值得同等待遇。把團隊反覆撰寫的檢查收攏成 checker，將可變的部分參數化，再放進共用的 package 或檔案。它的紀律跟任何可重用程式碼一樣：

- 一個 checker 對應一個連貫的意圖單元（一個協定、一種結構類型）。
- 把寬度、深度與延遲界限參數化，別寫死。
- 把每條 assertion 與證明其 antecedent 的 cover 配對（第 13 章），讓被重用的檢查自帶 vacuity 防護。
- 用 bind，絕不手動實例化，讓 RTL 維持乾淨。

一座由 bind 進去的 checker 構成的自家 library，代表一個新區塊只要實例化，就繼承了團隊累積的驗證意圖，角落情形也早已編碼進去。

## 常見陷阱

- **重新發明標準檢查。** 溢位、one-hot 與 handshake 的 checker，OVL 與 SVA library 裡早就有了。請優先用驗證過的元件。
- **在 checker 裡寫死參數。** 寬度或界限固定的 checker 無法重用。請把可變部分參數化。
- **在 RTL 裡手動實例化 checker。** 那會動到設計原始碼；請改用 bind。
- **交付不含 cover 的 checker。** 被重用的 assertion 在新場址可能 vacuous pass。請帶上 antecedent cover，讓檢查自己守住 vacuity。
- **在該用 checker 的地方用模組。** `checker` 是語言為此打造的容器，還允許模組可能會限制的驗證建模。對於成組的檢查，請優先選它。

## 小結

- `checker` 是 assertion、cover 與支援建模的可重用容器，帶有 port 與參數，像模組一樣實例化或 bind。
- 把 checker bind 上去，就能在不動設計的情況下附加一組相關檢查，並逐場址前傳訊號與參數。
- 挑最小而合適的：單一規則用 named property，相關的一組用 checker，唯有需要模組層級功能時才用完整模組。
- OVL 與 Accellera SVA checker library 為常見意圖提供驗證過、參數化的檢查；請優先用它們，而非手寫的等價物。
- 把專案特定的意圖封裝成 bind 進去、參數化、且自帶 antecedent cover 的 checker。

---

[← formal verification 入門](14-formal-verification-primer.md) · [目錄](../README.md) · [下一章：除錯與反樣式 →](16-debugging-and-antipatterns.md)
