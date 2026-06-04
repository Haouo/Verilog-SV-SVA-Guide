# 第三部 · 8. clock 與 reset

[← property](07-properties.md) · [目錄](../README.md) · [下一章：bind 與放置 →](09-binding-and-placement.md)

## 學習目標

- 以明確方式與預設方式為 concurrent assertion 附加 clock。
- 以 `default clocking` 一次設定 assertion clock。
- 以 `disable iff` 在 reset 期間停用 assertion。
- 理解 multiclock assertion，以及 clock 如何跨越 `##` 邊界。
- 依設計的慣例在正確的邊緣 sampling。

## 設計者的心智模型

clocking 告訴 assertion 該用哪一條時間軸，reset 則告訴它規則在什麼時候不該適用。少了這兩者，即使 temporal property 本身正確，也可能在初始化期間失敗，或取樣到 protocol 的錯誤 edge。

請把 `disable iff` 當成 contract 的一部分，而不是事後才補上的東西。reset 期間，有些訊號本來就會不穩定，或正被 force 到已知值；等到 reset 解除，assertion 才恢復運作，設計平常的承諾也才重新生效。reset 運算式應該貼合設計的這套脈絡。

## assertion clock

每個 concurrent assertion 都需要 clock。clock 決定取樣何時發生(第 2 章),也決定對每個 `##` 與 implication 而言「一個週期」是什麼意思。明確的寫法是在行內為它命名：

```systemverilog
// Sampling and stepping reference: posedge clk
assert property (@(posedge clk) req |=> gnt);
```

在每個 assertion 上都寫 `@(posedge clk)` 既重複又容易出錯，只要有一個邊緣打錯，語意就被無聲地改掉。對於只用一個 clock 的區塊，宣告一次就好。

## default clocking

`default clocking` 區塊會為其作用域內每個沒有指定自身 clock 的 concurrent assertion 設定 clock。在這個區塊內，assertion 讀起來清爽，不必逐行寫 clock:

```systemverilog
module fifo_ctrl (input logic clk, rst_n, /* ... */);

    default clocking cb @(posedge clk);
    endclocking

    // No @(posedge clk) needed — the default supplies it
    assert property (wr_en |-> !full);
    assert property (rd_en |-> !empty);

endmodule
```

default clocking 是建議的寫法：它把 clock 只陳述一次，讓 assertion 保持易讀，也杜絕了不一致的邊緣溜進來。當某個 assertion 確實跑在不同的 clock 上時，仍可為它指定自身的 clock 來覆寫 default。

## disable iff：處理 reset

reset 期間，設計還沒開始遵守它的協定，所以這時的 assertion 不該觸發。`disable iff (cond)` 會在 `cond` 為真時關閉 assertion,標準用途就是非同步 reset:

```systemverilog
// While rst_n is low, this assertion is disabled
assert property (@(posedge clk) disable iff (!rst_n)
    req |=> gnt);
```

`disable iff` 是**非同步**的：在它的條件變為真的瞬間，該 property 任何進行中的評估都會被中止，並回報為既非通過也非失敗。這正好對應非同步 reset:reset 可能在兩個 clock edge 之間 assert,且必須立即作廢任何待處理的檢查。這一點和 antecedent 中的布林閘控不同，後者只在 clock edge 取樣。

```systemverilog
// Guarding in the antecedent (sampled at the edge) — NOT the same as disable iff
assert property (@(posedge clk) (rst_n && req) |=> gnt);
```

reset 以及其他非同步的「放棄檢查」條件，用 `disable iff`;該在邊緣取樣的同步條件，用 antecedent 閘控。把這兩者搞混，是 reset 期間出現費解失敗的常見原因。

常見的一種寫法，是把整個區塊共用的單一 reset 條件，以 `default disable iff` 納入 default clocking 風格：

```systemverilog
module core (input logic clk, rst_n, /* ... */);

    default clocking cb @(posedge clk);
    endclocking
    default disable iff (!rst_n);   // applies to every assertion below

    assert property (req   |=> gnt);
    assert property (start |-> ##[1:8] done);

endmodule
```

`default disable iff` 把 reset 慣例只陳述一次，就如同 `default clocking` 把 clock 只陳述一次。兩者都讓每個 assertion 的文字聚焦在意圖上。

## multiclock assertion

單一個 assertion 可以橫跨一個以上的 clock。當 sequence 跨越某個 `##` 延遲、進入由不同 clock 驅動的區域時，該 assertion 會在那個邊界*流動*,從一個 clock 轉到下一個：

```systemverilog
// Antecedent sampled on clk_a; consequent sampled on clk_b
assert property (@(posedge clk_a) req ##1 @(posedge clk_b) ack);
```

multiclock assertion 的規則刻意定得嚴格：

- clock 變更只能發生在 `##` 週期延遲邊界，也就是設計從一個 clock domain 交接到另一個的地方。
- 跨過邊界後，`##1` 指的是「`clk_a` 匹配之後的第一個 `clk_b` 邊緣」，而不是某段固定時間。assertion 計算的是當前生效那個 clock 的邊緣。
- 要求單一共同 clock 的運算子，例如 `intersect`、跨重疊跨度的 `and`、或 `throughout`,都不能跨越 clock 變更。

要檢查跨 clock domain 的握手，multiclock assertion 正是合適的工具：請求在一個域發起，在另一個域被確認。讓兩側各自跑在自己的 clock 上，交接就交給 `##` 邊界承載。

## 在正確的邊緣 sampling

`@(posedge clk)` 裡的邊緣必須符合設計的取樣慣例。若 RTL 在上升緣擷取資料，assertion 也應在 `posedge` 取樣，這樣 assertion 看到的值才會和正反器一致。在錯誤的邊緣下 assert,取樣會差半個週期，產生看似莫名其妙的不一致結果。

```systemverilog
// RTL captures on posedge; the assertion must too
always_ff @(posedge clk) q <= d;
assert property (@(posedge clk) load |=> (q == $past(d)));
```

對於同時使用兩個邊緣的設計(雙邊緣邏輯),請讓每個 assertion 以擷取它所檢查訊號的那個邊緣來定時。不確定時，就把 assertion clock 對齊到產生該訊號的那段邏輯所用的 clock 與邊緣。

> **設計意圖。** clock 與 reset 設定告訴工具 assertion 的承諾*何時*適用：哪個邊緣定義它的週期，
> 以及在哪些窗口(reset)期間該承諾被暫停。`default clocking` 與 `default disable iff`
> 為一整個區塊把這些只陳述一次，使每個 assertion 都能表達純粹的意圖，也就是什麼必須為真，
> 至於何時檢查，則交給周圍的宣告來說明。

## 常見陷阱

- **在每個 assertion 上重複寫 `@(posedge clk)`。** 請用 `default clocking` 設定一次，避免不一致的邊緣溜進來。
- **把 reset 放進 antecedent,而沒用 `disable iff`。** antecedent 閘控在邊緣取樣；`disable iff` 是非同步的，會中止進行中的檢查。非同步 reset 請用 `disable iff`。
- **完全忘了處理 reset。** 沒有 reset 閘控，assertion 會在未知的啟動窗口期間就觸發。請加上 `disable iff (!rst_n)` 或 `default disable iff`。
- **在 `##` 邊界之外跨越 clock。** clock 變更只在週期延遲邊界才合法；single-clock 運算子不能跨越它。
- **在錯誤的邊緣取樣。** 把 assertion clock 與邊緣對齊到產生該訊號的那段邏輯，否則 assertion 會差半個週期取樣。

## 小結

- 每個 concurrent assertion 都需要 clock;`default clocking` 為作用域設定一次。
- `disable iff` 會非同步地關閉 assertion,是非同步 reset 的標準處理方式，而 `default disable iff` 把 reset 慣例只陳述一次。
- antecedent 中的布林閘控是同步的(在邊緣取樣),和非同步的 `disable iff` 不同。
- multiclock assertion 只在 `##` 邊界於各 clock 間流動；single-clock 運算子不能跨越該變更。
- 在符合設計擷取慣例的邊緣上取樣。

---

[← property](07-properties.md) · [目錄](../README.md) · [下一章：bind 與放置 →](09-binding-and-placement.md)
