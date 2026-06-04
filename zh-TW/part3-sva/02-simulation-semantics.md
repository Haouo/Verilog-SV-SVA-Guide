# 第三部 · 2. simulation semantics

[← 為何需要 assertion](01-why-assertions.md) · [目錄](../README.md) · [下一章：assertion kinds →](03-assertion-kinds.md)

## 學習目標

- 命名與 assertion 相關的 SystemVerilog 事件區域（event region）。
- 定義 sampled value 並說明它於何時被取得。
- 解釋 concurrent assertion 為何在 Preponed 區域 sampling。
- 以 clock 作為 assertion 時序的單一參考。
- 預測 concurrent assertion 所見的值與程序式程式碼所見的值有何不同。

## 設計者 mental model

concurrent assertion 觀察的是 sampled version of the design。它不是單純讀同一個 time slot 裡
procedural block 最新 assign 的 value。Preponed region sampling 讓 assertion 看到 clock edge 當下
已存在的 value，這比較接近 flip-flop 對 synchronous logic 的推理方式。

這個 timing model 是幾乎所有 SVA 驚訝點的地基。如果 assertion 看起來差一個 cycle，或 `$past`
好像跟 waveform 不一致，先問每個 value 來自哪個 event region。sampling 一清楚，implication、
reset disabling、local variable 都會少很多神秘感。

## sampling 所要解決的問題

在單一個 simulation time step（time step）內，許多事情同時發生：clock edge 觸發、正反器更新、組合邏輯穩定、各項指定爭相完成。若 assertion 在這片混亂中的某個任意時刻讀取訊號，它可能讀到更新到一半的值——有時是舊值、有時是新值，取決於排程順序。其結果將是非確定性的。

SystemVerilog 透過在每個時間步內定義*區域的順序*，並給予 concurrent assertion 一個固定、定義明確的值來讀取——即 **sampled value**——來消除這種模糊性。你不需要完整的排程模型才能寫出好 assertion，但你確實需要下列這幾個區域。

## 重要的事件區域

一個 simulation time step 被劃分為若干有序區域。對 assertion 而言，有四個重要：

- **Preponed。** 時間步的最前一個區域，在任何設計程式碼執行之前。此處的值是穩定的——本步尚未有任何更新發生。concurrent assertion 在此取得其**sampled value**。
- **Active。** 正常設計程式碼執行之處：`always` 區塊執行、阻塞式指定生效、組合邏輯穩定。
- **Observed。** 在 Active 區域穩定之後，concurrent assertion 的*property*使用稍早在 Preponed 取得的 sampled value 進行評估。
- **Reactive。** 測試平台端程式碼與 assertion 的**動作區塊**（附在 assertion 上的 pass/fail 程式碼）執行之處。

順序是固定的：Preponed → Active → … → Observed → Reactive。關鍵要點是：sampling *先*發生（Preponed），而評估在設計穩定*之後*發生（Observed）。

## sampled value

一個訊號的**sampled value**是它在當前時間步 Preponed 區域中的值——也就是驅動該 assertion 的 clock edge*之前*的值。concurrent assertion 絕不讀取訊號於時間步中途的活值；它讀取其 sampled value。

這帶來一個精確且重要的後果。在某個 clock edge，正反器的輸出與 assertion 皆指向*同一個*sampled value：訊號在進入該邊緣時所持有的值，亦即本次邊緣的更新生效之前的值。

```systemverilog
logic clk, a, b;

// On the posedge, this assertion sees the values a and b held
// *before* this edge, not the new values being computed now.
assert property (@(posedge clk) a |-> b);
```

因此 concurrent assertion 觀察設計的方式如同一個同步元件：它看到的是邊緣處有效的穩態值，而非邊緣期間正在被指定的暫態值。

## concurrent assertion 為何在 Preponed sampling

在 Preponed sampling 使 assertion 結果獨立於排程順序。兩個在同一時間步更新的訊號，可能在 Active 區域中發生競態——哪個 `always` 區塊先執行並無保證。若 assertion 在它們更新*之後*讀取，其結果可能取決於該競態。

改為讀取 Preponed 的值——本步更新*之前*的值——assertion 便看到一張乾淨、已穩定的快照。它不會被半完成的非阻塞式更新或兩個 `always` 區塊的執行順序所欺騙。這正是設計者所要的行為：assertion 對正反器所 sampling 的相同穩定值進行推理。

```systemverilog
// Both blocks update q and r in the same step. The assertion is not
// affected by which block the simulator runs first, because it samples
// q and r in Preponed, before either update.
always_ff @(posedge clk) q <= d;
always_ff @(posedge clk) r <= q;

assert property (@(posedge clk) r == $past(q));
```

此處 `$past(q)` 回傳 `q` 在前一個 clock 所持有的值——它本身也是一個 sampled value——這正是第二個正反器所擷取的值。

## clock 是參考

concurrent assertion 沒有 clock 便毫無意義。clock 同時定義兩件事：

1. **sampling 何時發生**——值在 Preponed sampling，相對於所指定的 clock edge。
2. **「一個週期之後」代表什麼**——sequence 或 property 中的每一個時序步驟（`##1`、`|=>` 等）都依該 clock 的一個跳動前進。

```systemverilog
// @(posedge clk) is the sampling and stepping reference for the whole property
assert property (@(posedge clk) start |=> ##2 done);
```

此處 `start`、`done` 與 `##2` 延遲全部相對於 `posedge clk` 衡量。assertion 不在意牆鐘時間或 delta 週期；它計算其 clock 的邊緣數。第 8 章介紹如何以 default clocking 區塊一次設定此 clock，以及 `disable iff` 如何處理 reset。

## sampled value 與程序式值

由於程序式程式碼（在 `always` 區塊中）在 Active 區域執行，而 concurrent assertion 在 Preponed sampling，兩者在同一時間步可能看到不同的值。這是刻意的，值得牢記：

- `always` 區塊中的 immediate assertion 看到**當前**、執行中途的值，如同任何程序式語句。
- concurrent assertion 看到**sampling**（Preponed）的值。

```systemverilog
always_comb begin
    x = a + b;            // x updates here, in the Active region
    assert (x < LIMIT);   // immediate: sees the new x right now
end

// concurrent: would sample x in Preponed — its value before this step
assert property (@(posedge clk) x < LIMIT);
```

若混用兩者，務必釐清區別：即時看*現在*，並行看*邊緣處的值*。

> **設計意圖。** sampled value 讓 assertion 以正反器的方式對設計推理——針對 clock edge 處存在的穩定值，
> 而非單一時間步的暫態翻動。正是這份穩定性，使 concurrent assertion 成為可靠的意圖陳述，
> 而非排程順序的人質。

## 常見陷阱

- **期望 concurrent assertion 看到剛被指定的值。** 它在 Preponed sampling，因此看到的是邊緣前的值，而非某個 `always` 區塊本步正在寫入的值。
- **混淆即時與並行的時序。** 程序式程式碼中的即時 `assert` 看當前值；並行的 `assert property` 看 sampled value。兩者在同一步內可能不同。
- **寫一個無 clock 的 concurrent assertion 並期望它「自動運作」。** 沒有 clock（明確或預設），就沒有 sampling reference。第 8 章介紹 default clocking。
- **對 delta 週期推理。** assertion 計算 clock edge，而非 delta。請以 assertion clock 的週期思考，而非以 simulator 排程步驟思考。

## 小結

- 一個時間步被劃分為有序區域；Preponed、Active、Observed 與 Reactive 是對 assertion 重要的幾個。
- concurrent assertion 在 Preponed 區域取得**sampled value**——clock edge 之前的值。
- 在 Preponed sampling 使結果獨立於排程競態。
- clock 是 sampling 與時序推進的單一參考。
- immediate assertion 看當前的程序式值；concurrent assertion 看 sampled value，兩者在同一步內可能不同。

---

[← 為何需要 assertion](01-why-assertions.md) · [目錄](../README.md) · [下一章：assertion kinds →](03-assertion-kinds.md)
