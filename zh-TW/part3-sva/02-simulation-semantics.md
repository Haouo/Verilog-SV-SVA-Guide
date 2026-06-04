# 第三部 · 2. simulation semantics

[← 為何需要 assertion](01-why-assertions.md) · [目錄](../README.md) · [下一章：assertion kinds →](03-assertion-kinds.md)

## 學習目標

- 說出與 assertion 相關的 SystemVerilog 事件區域（event region）。
- 定義 sampled value，並說明它在何時被取得。
- 解釋 concurrent assertion 為何在 Preponed 區域取樣。
- 以 clock 作為 assertion 時序的單一參考。
- 預測 concurrent assertion 看到的值，與程序式程式碼看到的值差在哪裡。

## 設計者的心智模型

concurrent assertion 觀察的是設計的取樣版本，而不是直接讀同一個 time slot 裡 procedural block 最新指定的值。在 Preponed 區域取樣，讓 assertion 看到 clock edge 當下就已經存在的值，這比較接近 flip-flop 推理 synchronous logic 的方式。

這套 timing model 是幾乎所有 SVA 意外的根源。如果 assertion 看起來差了一個 cycle，或 `$past` 好像跟波形對不上，先問每個值來自哪個 event region。取樣一旦想清楚，implication、用 reset 關閉檢查、local variable 都會少掉很多神秘感。

## 從問題開始

假設 RTL 在同一個 `posedge clk` 更新 `q`，而 assertion 也在同一個 `posedge clk` 檢查 `q`。新手最容易問的是：assertion 看到的是更新前的 `q`，還是更新後的 `q`？如果這個答案不固定，同一條 assertion 就可能因 simulator 排程不同而時好時壞。

所以 SVA 先規定一套取樣故事：concurrent assertion 不在 Active 區域裡追逐正在變動的值，而是在 Preponed 區域拿一張穩定快照，稍後再用那張快照評估 property。本章的 event region、sampled value 與 clock 參考，都是為了回答這個「到底看到哪個值」的問題。

## sampling 所要解決的問題

在單一個 simulation time step 內，許多事情同時發生：clock edge 觸發、正反器更新、組合邏輯穩定，各項指定也搶著完成。assertion 若在這片混亂中的某個任意時刻讀取訊號，可能會讀到更新到一半的值，有時是舊值、有時是新值，全看排程順序。這樣結果就不確定了。

SystemVerilog 的做法是在每個時間步內定義*區域的順序*，並給 concurrent assertion 一個固定、定義明確的值來讀取，也就是 **sampled value**，藉此消除這種模糊。你不需要完整的排程模型才能寫出好 assertion，但下列這幾個區域確實得知道。

## 重要的事件區域

一個 simulation time step 被劃分為若干有序區域。對 assertion 而言，有四個重要：

- **Preponed。** 時間步的第一個區域，在任何設計程式碼執行之前。此處的值是穩定的，本步還沒有任何更新發生。concurrent assertion 在這裡取得它的 **sampled value**。
- **Active。** 正常設計程式碼執行的地方：`always` 區塊執行、阻塞式指定生效、組合邏輯穩定。
- **Observed。** Active 區域穩定之後，concurrent assertion 的 *property* 用稍早在 Preponed 取得的 sampled value 來評估。
- **Reactive。** testbench 端程式碼，以及 assertion 的**動作區塊**（附在 assertion 上的 pass/fail 程式碼）執行的地方。

順序是固定的：Preponed → Active → … → Observed → Reactive。關鍵在於：取樣*先*發生（Preponed），評估則在設計穩定*之後*才發生（Observed）。

## sampled value

一個訊號的 **sampled value**，是它在當前時間步 Preponed 區域中的值，也就是驅動該 assertion 的 clock edge *之前*的值。concurrent assertion 絕不讀取訊號在時間步中途的活值，只讀它的 sampled value。

這帶來一個精確而重要的後果：在某個 clock edge，正反器的輸出與 assertion 指向的是*同一個* sampled value，也就是訊號進入該邊緣時所持有的值，亦即本次邊緣的更新生效之前的值。

```systemverilog
logic clk, a, b;

// On the posedge, this assertion sees the values a and b held
// *before* this edge, not the new values being computed now.
assert property (@(posedge clk) a |-> b);
```

因此 concurrent assertion 觀察設計的方式就像一個同步元件：它看到的是邊緣處有效的穩態值，而不是邊緣期間正在被指定的暫態值。

## concurrent assertion 為何在 Preponed sampling

在 Preponed 取樣，讓 assertion 的結果不受排程順序影響。兩個在同一時間步更新的訊號，可能在 Active 區域中發生競態：哪個 `always` 區塊先執行並無保證。assertion 若在它們更新*之後*才讀取，結果就可能被這場競態左右。

改成讀取 Preponed 的值，也就是本步更新*之前*的值，assertion 看到的就是一張乾淨、已穩定的快照。它不會被做到一半的非阻塞式更新騙到，也不會被兩個 `always` 區塊的執行順序騙到。這正是設計者要的行為：assertion 推理的，是正反器所取樣的那組穩定值。

```systemverilog
// Both blocks update q and r in the same step. The assertion is not
// affected by which block the simulator runs first, because it samples
// q and r in Preponed, before either update.
always_ff @(posedge clk) q <= d;
always_ff @(posedge clk) r <= q;

assert property (@(posedge clk) r == $past(q));
```

這裡 `$past(q)` 回傳 `q` 在前一個 clock 所持有的值，它本身也是一個 sampled value，正好就是第二個正反器擷取到的值。

## clock 是參考

concurrent assertion 沒有 clock 就毫無意義。clock 同時定義兩件事：

1. **取樣何時發生**：相對於指定的 clock edge，值在 Preponed 取樣。
2. **「一個週期之後」是什麼意思**：sequence 或 property 中的每一個時序步驟（`##1`、`|=>` 等）都依該 clock 的一個跳動往前走。

```systemverilog
// @(posedge clk) is the sampling and stepping reference for the whole property
assert property (@(posedge clk) start |=> ##2 done);
```

這裡 `start`、`done` 與 `##2` 延遲全都以 `posedge clk` 為基準衡量。assertion 不管牆鐘時間或 delta 週期，它數的是自己這個 clock 的邊緣數。第 8 章會介紹如何用 default clocking 區塊一次設好這個 clock，以及 `disable iff` 如何處理 reset。

## sampled value 與程序式值

程序式程式碼（在 `always` 區塊中）在 Active 區域執行，concurrent assertion 則在 Preponed 取樣，因此兩者在同一時間步可能看到不同的值。這是刻意的設計，值得記牢：

- `always` 區塊中的 immediate assertion 和任何程序式語句一樣，看到的是**當前**、執行到一半的值。
- concurrent assertion 看到的是**取樣**（Preponed）的值。

```systemverilog
always_comb begin
    x = a + b;            // x updates here, in the Active region
    assert (x < LIMIT);   // immediate: sees the new x right now
end

// concurrent: would sample x in Preponed — its value before this step
assert property (@(posedge clk) x < LIMIT);
```

兩者混用時，務必分清楚：immediate 看的是*現在*，concurrent 看的是*邊緣處的值*。

> **設計意圖。** sampled value 讓 assertion 以正反器的方式推理設計：針對 clock edge 處存在的穩定值，
> 而不是單一時間步裡的暫態翻動。正是這份穩定性，讓 concurrent assertion 成為可靠的意圖陳述，
> 而不會淪為排程順序的人質。

## 常見陷阱

- **以為 concurrent assertion 會看到剛指定的值。** 它在 Preponed 取樣，因此看到的是邊緣前的值，而不是某個 `always` 區塊這一步正在寫入的值。
- **搞混 immediate 與 concurrent 的時序。** 程序式程式碼中的 immediate `assert` 看的是當前值，concurrent `assert property` 看的是 sampled value，兩者在同一步內可能不同。
- **寫一個沒有 clock 的 concurrent assertion，還期望它「自動運作」。** 沒有 clock（不論明確或預設），就沒有取樣的參考。第 8 章會介紹 default clocking。
- **拿 delta 週期來推理。** assertion 數的是 clock edge，不是 delta。請以 assertion clock 的週期思考，而不是以 simulator 的排程步驟思考。

## 小結

- 一個時間步被劃分為有序的區域；對 assertion 重要的是 Preponed、Active、Observed 與 Reactive。
- concurrent assertion 在 Preponed 區域取得 **sampled value**，也就是 clock edge 之前的值。
- 在 Preponed 取樣，讓結果不受排程競態影響。
- clock 是取樣與時序推進共用的單一參考。
- immediate assertion 看當前的程序式值，concurrent assertion 看 sampled value，兩者在同一步內可能不同。

---

[← 為何需要 assertion](01-why-assertions.md) · [目錄](../README.md) · [下一章：assertion kinds →](03-assertion-kinds.md)
