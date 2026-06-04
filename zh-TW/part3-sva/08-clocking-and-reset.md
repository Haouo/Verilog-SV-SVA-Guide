# 第三部 · 8. clock 與 reset

[← property](07-properties.md) · [目錄](../README.md) · [下一章：bind 與放置 →](09-binding-and-placement.md)

## 學習目標

- 以明確方式與預設方式為 concurrent assertion 附加 clock。
- 以 `default clocking` 一次設定 assertion clock。
- 以 `disable iff` 在 reset 期間停用 assertion。
- 對 multiclock assertion 與跨 `##` 邊界的 clock 流進行推理。
- 依設計的慣例在正確的邊緣 sampling。

## 設計者 mental model

clocking 告訴 assertion 使用哪一條 timeline；reset 則告訴它 rule 什麼時候不應該 apply。缺少這兩者，
即使 temporal property 本身正確，也可能在 initialization 失敗，或 sample 到 protocol 的錯誤 edge。

請把 `disable iff` 當成 contract 的一部分，而不是事後補上的東西。reset 期間，有些 signal 本來
就會 unstable，或正在被 force 到 known value。reset release 之後，assertion resume，design 的
normal promise 才重新重要。reset expression 應該吻合這個 design story。

## assertion clock

每個 concurrent assertion 都需要 clock。clock 固定 sampling 何時發生（第 2 章），以及對每個 `##` 與 implication 而言「一個週期」代表什麼。明確形式於行內命名它：

```systemverilog
// Sampling and stepping reference: posedge clk
assert property (@(posedge clk) req |=> gnt);
```

在每個 assertion 上撰寫 `@(posedge clk)` 既重複又易錯——單一個打錯的邊緣會無聲地改變語意。對於只有一個 clock 的區塊，請宣告它一次。

## default clocking

`default clocking` 區塊為其作用域內每個未命名自身 clock 的 concurrent assertion 設定 clock。在該區塊內，assertion 讀來清爽，無需逐行 clock：

```systemverilog
module fifo_ctrl (input logic clk, rst_n, /* ... */);

    default clocking cb @(posedge clk);
    endclocking

    // No @(posedge clk) needed — the default supplies it
    assert property (wr_en |-> !full);
    assert property (rd_en |-> !empty);

endmodule
```

default clocking 是建議的風格：它把 clock 陳述一次，保持 assertion 可讀，並消除不一致邊緣溜入的機會。當 assertion 確實運行於不同 clock 時，仍可藉由命名自身 clock 來 override default。

## disable iff：處理 reset

reset 期間，設計尚未遵守其協定，因此其 assertion 不應觸發。`disable iff (cond)` 在 `cond` 為真時關閉 assertion——標準用途是非同步 reset：

```systemverilog
// While rst_n is low, this assertion is disabled
assert property (@(posedge clk) disable iff (!rst_n)
    req |=> gnt);
```

`disable iff` 是**非同步**的：其條件變為真的瞬間，該 property 任何進行中的評估都被中止，並回報為既非通過也非失敗。這與非同步 reset 相符——它可在 clock edge 之間 assert，且必須立即作廢任何待處理的檢查。它有別於 antecedent 中的布林閘控，後者只在 clock edge sampling。

```systemverilog
// Guarding in the antecedent (sampled at the edge) — NOT the same as disable iff
assert property (@(posedge clk) (rst_n && req) |=> gnt);
```

對 reset 與其他非同步的「放棄檢查」條件使用 `disable iff`；對應在邊緣 sampling 的同步條件使用 antecedent 閘控。把兩者搞混是 reset 期間令人困惑的失敗的常見來源。

一個常見樣式是把整個區塊的單一 reset condition，以 `default disable iff` 納入 default clocking 風格中：

```systemverilog
module core (input logic clk, rst_n, /* ... */);

    default clocking cb @(posedge clk);
    endclocking
    default disable iff (!rst_n);   // applies to every assertion below

    assert property (req   |=> gnt);
    assert property (start |-> ##[1:8] done);

endmodule
```

`default disable iff` 把 reset convention 陳述一次，正如 `default clocking` 把 clock 陳述一次。兩者皆使每個 assertion 的文字聚焦於意圖。

## multiclock assertion

單一 assertion 可橫跨多於一個 clock。當 sequence 跨越一個 `##` 延遲進入不同 clock 的區域時，該 assertion 在該邊界*流動*，從一個 clock 轉到下一個：

```systemverilog
// Antecedent sampled on clk_a; consequent sampled on clk_b
assert property (@(posedge clk_a) req ##1 @(posedge clk_b) ack);
```

multiclock assertion 的規則刻意嚴格：

- clock 變更只能發生在 `##` 週期延遲邊界，即設計從一個 clock domain 交接到另一個之處。
- 跨越邊界後，`##1` 意指「`clk_a` 匹配之後的第一個 `clk_b` 邊緣」，而非固定時間。assertion 計算當前生效 clock 的邊緣。
- 要求單一共同 clock 的運算子——例如 `intersect`、跨重疊跨度的 `and`、或 `throughout`——不能跨越 clock 變更。

multiclock assertion 是檢查跨 clock domain 握手的正確工具，其中請求在一個域發起並在另一個域被確認。讓每一側各自處於自身 clock，並讓 `##` 邊界承載交接。

## 在正確的邊緣 sampling

`@(posedge clk)` 中的邊緣必須符合設計的 sampling convention。若 RTL 在上升緣擷取資料，assertion 也應在 `posedge` sampling，使 assertion 看到與正反器相同的值。在錯誤的邊緣 assertion 會差半個週期 sampling，產生看似莫名其妙地不一致的結果。

```systemverilog
// RTL captures on posedge; the assertion must too
always_ff @(posedge clk) q <= d;
assert property (@(posedge clk) load |=> (q == $past(d)));
```

對使用雙邊緣的設計（雙邊緣邏輯），請以擷取其所檢查訊號的那個邊緣為每個 assertion 定時。不確定時，請把 assertion clock 對齊到產生被 checked signal 的邏輯的 clock 與邊緣。

> **設計意圖。** clock 與 reset 設定告訴工具 assertion 的承諾*何時*適用：哪個邊緣定義其週期，
> 以及在哪些窗口（reset）期間該承諾被暫停。`default clocking` 與 `default disable iff`
> 為一個區塊把這些陳述一次，使每個 assertion 能表達純粹的意圖——什麼必須為真——
> 而周圍的宣告則說明何時檢查它。

## 常見陷阱

- **在每個 assertion 上重複 `@(posedge clk)`。** 請用 `default clocking` 設定一次，避免不一致的邊緣溜入。
- **把 reset 放進 antecedent 而非 `disable iff`。** antecedent 閘控在邊緣 sampling；`disable iff` 是非同步的並中止進行中的檢查。對非同步 reset 請用 `disable iff`。
- **完全忘記 reset。** 沒有 reset 閘控，assertion 會在未知的啟動窗口期間觸發。請加上 `disable iff (!rst_n)` 或 `default disable iff`。
- **在 `##` 邊界之外跨越 clock。** clock 變更只在週期延遲邊界合法；single-clock 運算子不能跨越它。
- **在錯誤的邊緣 sampling。** 把 assertion clock 與邊緣對齊到產生該訊號的邏輯，否則 assertion 會差半個週期 sampling。

## 小結

- 每個 concurrent assertion 都需要 clock；`default clocking` 為作用域設定一次。
- `disable iff` 非同步地關閉 assertion——非同步 reset 的標準處理方式——而 `default disable iff` 把 reset convention 陳述一次。
- antecedent 中的布林閘控是同步的（在邊緣 sampling），不同於非同步的 `disable iff`。
- multiclock assertion 只在 `##` 邊界於 clock 間流動；single-clock 運算子不能跨越該變更。
- 在符合設計擷取慣例的邊緣 sampling。

---

[← property](07-properties.md) · [目錄](../README.md) · [下一章：bind 與放置 →](09-binding-and-placement.md)
