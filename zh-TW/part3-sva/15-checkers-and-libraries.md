# 第三部 · 15. checker 與 library

[← formal verification 入門](14-formal-verification-primer.md) · [目錄](../README.md) · [下一章：除錯與反樣式 →](16-debugging-and-antipatterns.md)

## 學習目標

- 將 `checker` 構造用作 assertion 的可重用容器。
- 將訊號與參數傳入 checker，並像模組一樣 bind（bind）它。
- 比較 `checker` 與 property、以及與 assertion module 之間的差異。
- 認識標準的可重用 assertion library：OVL 與 Accellera SVA library。
- 為跨專案的重用而封裝你自己的 assertion。

## 設計者 mental model

checker 是帶有 named interface 的 reusable assertion container。它讓 team 把 protocol rule 封裝
一次，然後在同樣 rule 出現的地方 instantiate。library 於是變成 design intent 的 vocabulary：no
overflow、stable until accept、one-hot、bounded latency 等等。

有用的 checker interface 應該小而精準。它只暴露 rule 所需的 signal、parameter、clocking、
reset，並隱藏 caller 不應重寫的 SVA detail。reuse 只有在 checker name 和 parameter 讓 intent
一眼明白時才有價值。

## checker 構造

**checker**（checker）是 SystemVerilog 中專為容納 assertion 而設的容器，盛裝 assertion、cover，以及支援它們的建模程式碼。它類似模組，具有 port，可被實例化或 bind，但它專用於驗證：它可包含 `assert`、`assume`、`cover`、sequence、property，以及有限的程序化建模，且設計用於重用。

```systemverilog
// A reusable request/acknowledge checker
checker req_ack_chk (logic clk, logic rst_n, logic req, logic ack, int unsigned n);
    default clocking cb @(posedge clk); endclocking
    default disable iff (!rst_n);

    a_ack: assert property ($rose(req) |-> ##[1:n] ack);
    c_req: cover  property ($rose(req));
endchecker
```

這個 checker 將一個完整、自我說明的意圖單元——assertion、其配對的 cover，以及 clock 與 reset convention——封裝在一個具名的介面之後。凡此握手形態反覆出現之處，一次實例化便套用了整個組合。

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

因為 checker 接受 port 與參數，一份定義便能適配許多場址：不同的訊號名稱透過 port 對映，而像延遲界限 `n` 這樣的參數則逐實例調校檢查。bind checker 使可重用的驗證程式碼完全留在 RTL 之外。

## checker 與 property、與 assertion module

三種構造都能容納 assertion；它們處於不同的尺度。

- **named property**是最小的重用單元：一條時序陳述，帶引數。用於單一反覆出現的形態（第 7 章）。
- **`checker`** 是專為此目的打造、盛裝數條相關 assertion、cover 與支援建模的組合，具有自己的 port 與參數。當一*組*相關的檢查需要一同移動時——例如某協定的整份契約——便使用它。
- **單純的 assertion module**（第 9 章）同樣盛裝 assertion，但它是被改用於驗證的一般模組。`checker` 是語言*為此工作*所提供的構造：它允許模組可能限制的驗證建模，並清楚地示意意圖。

請選擇最小而合適者：單一規則用 property，相關的一組用 checker，唯有需要 checker 所不具備的模組層級功能時，才保留一個完整模組。

## 可重用的 assertion library

常見的檢查你鮮少需要從頭撰寫。有兩套廣為可得的可重用 assertion。

### OVL（Open Verification Library）

OVL 是 Accellera 的一套預先封裝的 checker 元件 library——溢位、one-hot、handshake、FIFO 等等——可從 Verilog 與 SystemVerilog 使用。每個 checker 以描述特定情形的參數實例化。OVL 早於廣泛的 SVA 支援，在工具或流程偏好可實例化 checker 而非內嵌 SVA 之處，至今仍然有用。

### Accellera SVA 標準 checker library

SVA 標準 checker library 是一組以原生 SVA 撰寫的 `checker` 元件，以參數化 checker 涵蓋同樣反覆出現的意圖——資料穩定性、handshake、gray code、奇偶校驗等等。由於是原生 SVA，它能與你自己的 assertion 乾淨地組合，並以相同方式 bind。

```systemverilog
// Conceptual: instantiate a library checker rather than hand-writing it
// (exact name and ports depend on the library version)
bind dma assert_handshake #(.MIN(1), .MAX(8))
    u_hs (.clk(clk), .reset_n(rst_n), .req(req), .ack(ack));
```

> **設計意圖。** library 把反覆出現的設計意圖轉化為一套詞彙。「不溢位」、「gray 單一位元變化」、「N 週期內被回應」都是一個區塊接一個區塊出現的意圖；checker library 將每個意圖命名一次、經過驗證且參數化，使設計者得以實例化意圖，而非重新推導 SVA。此處的重用不只是便利——library 的檢查身經百戰，這使它比一條新手寫的 property 更值得信賴。

## 封裝你自己的 assertion

專案特定的意圖值得同等待遇。將團隊反覆撰寫的檢查收攏成 checker，把可變的部分參數化，並放入共用的 package 或檔案。其紀律與任何可重用程式碼相同：

- 一個 checker 對應一個連貫的意圖單元（一個協定、一種結構類型）。
- 將寬度、深度與延遲界限參數化，而非寫死。
- 將每條 assertion 與證明其 antecedent 的 cover 配對（第 13 章），使被重用的檢查自帶 vacuity 防護。
- bind，絕不手動實例化，使 RTL 維持乾淨。

一座由被 bind checker 構成的自家 library，意味著一個新區塊只需透過實例化，便繼承了團隊累積的驗證意圖，且角落情形已預先編碼。

## 常見陷阱

- **重新發明標準檢查。** 溢位、one-hot 與 handshake 的 checker 已存在於 OVL 與 SVA library 中。請偏好經過驗證的元件。
- **在 checker 中寫死參數。** 寬度或界限固定的 checker 無法重用。請將可變部分參數化。
- **在 RTL 中手動實例化 checker。** 那會修改設計原始碼；請改為 bind checker。
- **交付不含其 cover 的 checker。** 被重用的 assertion 在新場址可能 vacuous pass。請納入 antecedent cover，使檢查自守其 vacuity。
- **在 checker 適用處使用模組。** `checker` 是語言為此打造的容器，並允許模組可能限制的驗證建模。對於成組的檢查，請偏好它。

## 小結

- `checker` 是 assertion、cover 與支援建模的可重用容器，具有 port 與參數，像模組一樣實例化或 bind。
- bind checker，便能在不修改設計的情況下，將一組相關檢查附加上去，並逐場址前傳訊號與參數。
- 選擇最小而合適者：單一規則用 named property，相關的一組用 checker，唯有需要模組層級功能時才用完整模組。
- OVL 與 Accellera SVA checker library 為常見意圖提供經驗證、參數化的檢查；請偏好它們勝過手寫的等價物。
- 將專案特定的意圖封裝成被 bind、參數化、且自帶 antecedent cover 的 checker。

---

[← formal verification 入門](14-formal-verification-primer.md) · [目錄](../README.md) · [下一章：除錯與反樣式 →](16-debugging-and-antipatterns.md)
