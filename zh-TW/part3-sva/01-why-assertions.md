# 第三部 · 1. 為何需要 assertion

[← 驗證功能概覽](../part2-systemverilog/07-verification-features-overview.md) · [目錄](../README.md) · [下一章：simulation semantics →](02-simulation-semantics.md)

## 學習目標

- 說清楚 RTL 描述的內容與 assertion 描述的內容差在哪裡。
- 解釋 Assertion-Based Verification (ABV)，以及為何它本來就是設計者的工作。
- 把 assertion 定位在設計流程中：simulation、formal 與 emulator（emulation）。
- 一眼分辨 immediate assertion 與 concurrent assertion。
- 理解為何「在源頭失敗」勝過「在下游失敗」。

## 設計者的心智模型

assertion 是可執行的設計意圖。它不取代 RTL、testbench 或 specification，而是用一條規則把三者串起來，說明設計必須遵守什麼。好的 assertion 夠小，失敗時只有一個清楚的理由；也夠靠近 RTL，讓出錯的那個 cycle 本身就能指出 bug 的位置。

先把規則用一句話講清楚，再寫語法。「request 必須在四個 cycle 內得到 answer」是意圖，`req |-> ##[1:4] ack` 是其中一種寫法。原始句子模糊，property 就跟著模糊。好的 SVA 從一句精確的設計敘述開始。

## RTL 說明「如何做」；assertion 說明「什麼必須為真」

一段 RTL 描述硬體*如何*算出結果，本身卻不說明那個結果*應該*是什麼。設計意圖（design intent），例如請求一定會被確認、狀態向量是 one-hot、FIFO 永不溢位，只存在於你的腦中、規格書中，或註解裡，這些地方工具都無法檢查。

**assertion**是對預期行為可檢查的陳述。它把意圖從你的腦中搬進原始碼，化為 simulator 或 formal tool 可以自動評估的形式。RTL 與 assertion 從兩個角度描述同一個設計：RTL 說明它如何行為，assertion 說明什麼必須成立。兩者一旦不一致，assertion 就會觸發，告訴你 RTL 錯了。

```systemverilog
// RTL: how the grant is produced
always_ff @(posedge clk)
    gnt <= req & ~busy;

// Assertion: what must be true — a grant implies a request was pending
assert property (@(posedge clk) gnt |-> $past(req));
```

`always_ff` 區塊是實作。`assert property` 是契約。兩者互不取代。

## Assertion-Based Verification

**Assertion-Based Verification (ABV)** 是一套把 assertion 置於設計檢查核心的方法論。它不只依賴在邊界比對輸出的 testbench，而是在整個設計中嵌入許多小而局部的檢查。每個檢查只陳述關於某一訊號或介面的一項事實，並貼近該事實產生的地方。

這對設計者尤其重要，因為**意圖在你手上**。你知道每個埠上的 protocol、每個狀態暫存器的編碼、每個計數器必須維持的不變式（invariant）。驗證工程師可以從規格書重新找回其中一部分，但你在寫程式碼時就已經掌握這些知識。趁此時把它寫成緊鄰邏輯的 assertion，能在記憶猶新時記錄下來，並讓它變成隨模組同行、由機器持續檢查的永久契約。

ABV 在三方面帶來回報：

- **可觀測性。** 違反不變式的錯誤會當場在不變式處被捕捉，而不是等好幾個週期後、被破壞的值終於抵達輸出時才被發現。
- **文件化。** assertion 是可執行的文件。它不像註解會悄悄過時：一旦變為假，就會觸發。
- **可重用。** 同一組 assertion 可以在區塊層級 simulation、全晶片回歸測試與 formal 中執行，無需修改。

## assertion 在流程中的定位

同一個 assertion 可在設計流程中服務於多種工具：

- **simulation。** assertion 每個 clock 週期都對實際訊號值評估一次。一旦違反，就在精確的時間與位置印出錯誤。
- **formal verification。** formal tool 會嘗試*證明* assertion 對每個合法輸入都成立，證不出來就產生反例軌跡。在這裡 assertion 分成兩類：要證明的部分（`assert`），以及對環境的假設（`assume`）。
- **emulator（emulation）與晶片上電除錯。** 可合成的 assertion 子集可以在 emulator 上執行，而它們捕捉到的意圖能指引矽後（post-silicon）除錯。

正因為一個 assertion 可以服務於上述全部，在 RTL 開發期間寫一次，價值就能倍增。

## 一眼看懂兩種 assertion

SystemVerilog 有兩大 assertion 家族。後續章節各有深入處理；此處先說明其區別。

**immediate assertion**是一條程序式語句。它和 `if` 一樣，在控制流抵達它的*當下*評估運算式，檢查某一瞬間的條件。

```systemverilog
// Immediate: checked the moment this statement executes
always_comb
    assert (onehot_count <= 1);
```

**concurrent assertion**帶有 clock。它隨時間評估，在 clock edge 取樣訊號，並推理跨週期的行為。它檢查的是一個時序陳述，也就是某種在一個或多個 clock 上展開的行為。

```systemverilog
// Concurrent: checked every clock, can span multiple cycles
assert property (@(posedge clk) req |=> gnt);
```

經驗法則：要檢查程序式程式碼中某一點的條件，就用 immediate assertion；要檢查帶 clock 時間上的預期行為，就用 concurrent assertion。關於 protocol、handshake 與狀態機的設計意圖多半是時序性的，因此本部大部分內容都在談 concurrent assertion。

## 在源頭失敗

assertion 的核心好處，在於它*在何處*失敗。想像一個被破壞的 FIFO 指標。沒有 assertion 時，錯誤的指標先被寫入，稍後又被讀回，於是錯誤的資料離開 FIFO；症狀要到下游好幾個模組之外才浮現，可能已是數千個週期之後，很難回溯到原因。

有了針對指標不變式的 assertion，失敗會在指標越界的當下就被回報，就在源頭，並指明正確的週期與正確的訊號。原因與症狀之間的距離縮減為零。這就是「一下午的波形考古」與「一行訊息」之間的差別。

```systemverilog
// Catch the bad pointer where it happens, not downstream
assert property (@(posedge clk) disable iff (!rst_n)
    wr_ptr < DEPTH);
```

> **設計意圖。** RTL 捕捉實作，assertion 捕捉實作必須遵守的承諾。把兩者並排寫下，
> 工具就能在實作違反承諾的當下告訴你：就在源頭，而非三個模組之外。

## 常見陷阱

- **把 assertion 當成只與驗證者有關。** 意圖在設計者手上，應該趁邏輯記憶猶新時，自己寫下捕捉意圖的 assertion。
- **寫註解而不寫 assertion。** 註解不會觸發。意圖只要可檢查，就把它寫成 assertion，逼它保持誠實。
- **為單一瞬間的檢查動用 concurrent assertion。** 單純的組合不變式用 immediate assertion 就好，別替它套上一個它不需要的 clock。
- **把所有 assertion 都延後到獨立的驗證階段。** 最省成本的錯誤，就是 assertion 在程式碼第一次執行時當場捕捉到的那些。

## 小結

- RTL 說明硬體*如何*行為；assertion 說明*什麼必須為真*。
- ABV 在整個設計中嵌入許多小檢查，由握有意圖的設計者親自撰寫。
- 一個 assertion 在流程中可同時服務於 simulation、formal 與 emulator。
- immediate assertion 檢查某一瞬間的條件，concurrent assertion 檢查帶 clock 時間上的行為。
- assertion 在源頭失敗，把原因與症狀之間的距離縮到零。

---

[← 驗證功能概覽](../part2-systemverilog/07-verification-features-overview.md) · [目錄](../README.md) · [下一章：simulation semantics →](02-simulation-semantics.md)
