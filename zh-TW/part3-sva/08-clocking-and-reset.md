# 第三部 · 8. 時脈與重置

[← 性質（property）](07-properties.md) · [目錄](../README.md) · [下一章：綁定與放置 →](09-binding-and-placement.md)

## 學習目標

- 以明確方式與預設方式為並行斷言附加時脈。
- 以 `default clocking` 一次設定斷言時脈。
- 以 `disable iff` 在重置期間停用斷言。
- 對多時脈斷言與跨 `##` 邊界的時脈流進行推理。
- 依設計的慣例在正確的邊緣取樣。

## 斷言時脈

每個並行斷言都需要時脈。時脈固定取樣何時發生（第 2 章），以及對每個 `##` 與蘊涵而言「一個週期」代表什麼。明確形式於行內命名它：

```systemverilog
// Sampling and stepping reference: posedge clk
assert property (@(posedge clk) req |=> gnt);
```

在每個斷言上撰寫 `@(posedge clk)` 既重複又易錯——單一個打錯的邊緣會無聲地改變語意。對於只有一個時脈的區塊，請宣告它一次。

## default clocking

`default clocking` 區塊為其作用域內每個未命名自身時脈的並行斷言設定時脈。在該區塊內，斷言讀來清爽，無需逐行時脈：

```systemverilog
module fifo_ctrl (input logic clk, rst_n, /* ... */);

    default clocking cb @(posedge clk);
    endclocking

    // No @(posedge clk) needed — the default supplies it
    assert property (wr_en |-> !full);
    assert property (rd_en |-> !empty);

endmodule
```

default clocking 是建議的風格：它把時脈陳述一次，保持斷言可讀，並消除不一致邊緣溜入的機會。當斷言確實運行於不同時脈時，仍可藉由命名自身時脈來覆蓋它。

## disable iff：處理重置

重置期間，設計尚未遵守其協定，因此其斷言不應觸發。`disable iff (cond)` 在 `cond` 為真時關閉斷言——標準用途是非同步重置：

```systemverilog
// While rst_n is low, this assertion is disabled
assert property (@(posedge clk) disable iff (!rst_n)
    req |=> gnt);
```

`disable iff` 是**非同步**的：其條件變為真的瞬間，該性質任何進行中的評估都被中止，並回報為既非通過也非失敗。這與非同步重置相符——它可在時脈緣之間斷言，且必須立即作廢任何待處理的檢查。它有別於前提中的布林閘控，後者只在時脈緣取樣。

```systemverilog
// Guarding in the antecedent (sampled at the edge) — NOT the same as disable iff
assert property (@(posedge clk) (rst_n && req) |=> gnt);
```

對重置與其他非同步的「放棄檢查」條件使用 `disable iff`；對應在邊緣取樣的同步條件使用前提閘控。把兩者搞混是重置期間令人困惑的失敗的常見來源。

一個常見樣式是把整個區塊的單一重置條件，以 `default disable iff` 納入 default clocking 風格中：

```systemverilog
module core (input logic clk, rst_n, /* ... */);

    default clocking cb @(posedge clk);
    endclocking
    default disable iff (!rst_n);   // applies to every assertion below

    assert property (req   |=> gnt);
    assert property (start |-> ##[1:8] done);

endmodule
```

`default disable iff` 把重置慣例陳述一次，正如 `default clocking` 把時脈陳述一次。兩者皆使每個斷言的文字聚焦於意圖。

## 多時脈斷言

單一斷言可橫跨多於一個時脈。當序列跨越一個 `##` 延遲進入不同時脈的區域時，該斷言在該邊界*流動*，從一個時脈轉到下一個：

```systemverilog
// Antecedent sampled on clk_a; consequent sampled on clk_b
assert property (@(posedge clk_a) req ##1 @(posedge clk_b) ack);
```

多時脈斷言的規則刻意嚴格：

- 時脈變更只能發生在 `##` 週期延遲邊界，即設計從一個時脈域交接到另一個之處。
- 跨越邊界後，`##1` 意指「`clk_a` 匹配之後的第一個 `clk_b` 邊緣」，而非固定時間。斷言計算當前生效時脈的邊緣。
- 要求單一共同時脈的運算子——例如 `intersect`、跨重疊跨度的 `and`、或 `throughout`——不能跨越時脈變更。

多時脈斷言是檢查跨時脈域握手的正確工具，其中請求在一個域發起並在另一個域被確認。讓每一側各自處於自身時脈，並讓 `##` 邊界承載交接。

## 在正確的邊緣取樣

`@(posedge clk)` 中的邊緣必須符合設計的取樣慣例。若 RTL 在上升緣擷取資料，斷言也應在 `posedge` 取樣，使斷言看到與正反器相同的值。在錯誤的邊緣斷言會差半個週期取樣，產生看似莫名其妙地不一致的結果。

```systemverilog
// RTL captures on posedge; the assertion must too
always_ff @(posedge clk) q <= d;
assert property (@(posedge clk) load |=> (q == $past(d)));
```

對使用雙邊緣的設計（雙邊緣邏輯），請以擷取其所檢查訊號的那個邊緣為每個斷言定時。不確定時，請把斷言時脈對齊到產生被斷言訊號之邏輯的時脈與邊緣。

> **設計意圖。** 時脈與重置設定告訴工具斷言的承諾*何時*適用：哪個邊緣定義其週期，
> 以及在哪些窗口（重置）期間該承諾被暫停。`default clocking` 與 `default disable iff`
> 為一個區塊把這些陳述一次，使每個斷言能表達純粹的意圖——什麼必須為真——
> 而周圍的宣告則說明何時檢查它。

## 常見陷阱

- **在每個斷言上重複 `@(posedge clk)`。** 請用 `default clocking` 設定一次，避免不一致的邊緣溜入。
- **把重置放進前提而非 `disable iff`。** 前提閘控在邊緣取樣；`disable iff` 是非同步的並中止進行中的檢查。對非同步重置請用 `disable iff`。
- **完全忘記重置。** 沒有重置閘控，斷言會在未知的啟動窗口期間觸發。請加上 `disable iff (!rst_n)` 或 `default disable iff`。
- **在 `##` 邊界之外跨越時脈。** 時脈變更只在週期延遲邊界合法；單時脈運算子不能跨越它。
- **在錯誤的邊緣取樣。** 把斷言時脈與邊緣對齊到產生該訊號的邏輯，否則斷言會差半個週期取樣。

## 小結

- 每個並行斷言都需要時脈；`default clocking` 為作用域設定一次。
- `disable iff` 非同步地關閉斷言——非同步重置的標準處理方式——而 `default disable iff` 把重置慣例陳述一次。
- 前提中的布林閘控是同步的（在邊緣取樣），不同於非同步的 `disable iff`。
- 多時脈斷言只在 `##` 邊界於時脈間流動；單時脈運算子不能跨越該變更。
- 在符合設計擷取慣例的邊緣取樣。

---

[← 性質（property）](07-properties.md) · [目錄](../README.md) · [下一章：綁定與放置 →](09-binding-and-placement.md)
