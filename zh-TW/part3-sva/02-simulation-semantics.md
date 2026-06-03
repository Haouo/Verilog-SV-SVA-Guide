# 第三部 · 2. 模擬語意

[← 為何需要斷言](01-why-assertions.md) · [目錄](../README.md) · [下一章：斷言種類 →](03-assertion-kinds.md)

## 學習目標

- 命名與斷言相關的 SystemVerilog 事件區域（event region）。
- 定義取樣值（sampled value）並說明它於何時被取得。
- 解釋並行斷言為何在 Preponed 區域取樣。
- 以時脈作為斷言時序的單一參考。
- 預測並行斷言所見的值與程序式程式碼所見的值有何不同。

## 取樣所要解決的問題

在單一個模擬時間步（time step）內，許多事情同時發生：時脈緣觸發、正反器更新、組合邏輯穩定、各項指定爭相完成。若斷言在這片混亂中的某個任意時刻讀取訊號，它可能讀到更新到一半的值——有時是舊值、有時是新值，取決於排程順序。其結果將是非確定性的。

SystemVerilog 透過在每個時間步內定義*區域的順序*，並給予並行斷言一個固定、定義明確的值來讀取——即**取樣值**（sampled value，取樣值）——來消除這種模糊性。你不需要完整的排程模型才能寫出好斷言，但你確實需要下列這幾個區域。

## 重要的事件區域

一個模擬時間步被劃分為若干有序區域。對斷言而言，有四個重要：

- **Preponed。** 時間步的最前一個區域，在任何設計程式碼執行之前。此處的值是穩定的——本步尚未有任何更新發生。並行斷言在此取得其**取樣值**。
- **Active。** 正常設計程式碼執行之處：`always` 區塊執行、阻塞式指定生效、組合邏輯穩定。
- **Observed。** 在 Active 區域穩定之後，並行斷言的*性質*使用稍早在 Preponed 取得的取樣值進行評估。
- **Reactive。** 測試平台端程式碼與斷言的**動作區塊**（附在斷言上的 pass/fail 程式碼）執行之處。

順序是固定的：Preponed → Active → … → Observed → Reactive。關鍵要點是：取樣*先*發生（Preponed），而評估在設計穩定*之後*發生（Observed）。

## 取樣值

一個訊號的**取樣值**是它在當前時間步 Preponed 區域中的值——也就是驅動該斷言的時脈緣*之前*的值。並行斷言絕不讀取訊號於時間步中途的活值；它讀取其取樣值。

這帶來一個精確且重要的後果。在某個時脈緣，正反器的輸出與斷言皆指向*同一個*取樣值：訊號在進入該邊緣時所持有的值，亦即本次邊緣的更新生效之前的值。

```systemverilog
logic clk, a, b;

// On the posedge, this assertion sees the values a and b held
// *before* this edge, not the new values being computed now.
assert property (@(posedge clk) a |-> b);
```

因此並行斷言觀察設計的方式如同一個同步元件：它看到的是邊緣處有效的穩態值，而非邊緣期間正在被指定的暫態值。

## 並行斷言為何在 Preponed 取樣

在 Preponed 取樣使斷言結果獨立於排程順序。兩個在同一時間步更新的訊號，可能在 Active 區域中發生競態——哪個 `always` 區塊先執行並無保證。若斷言在它們更新*之後*讀取，其結果可能取決於該競態。

改為讀取 Preponed 的值——本步更新*之前*的值——斷言便看到一張乾淨、已穩定的快照。它不會被半完成的非阻塞式更新或兩個 `always` 區塊的執行順序所欺騙。這正是設計者所要的行為：斷言對正反器所取樣的相同穩定值進行推理。

```systemverilog
// Both blocks update q and r in the same step. The assertion is not
// affected by which block the simulator runs first, because it samples
// q and r in Preponed, before either update.
always_ff @(posedge clk) q <= d;
always_ff @(posedge clk) r <= q;

assert property (@(posedge clk) r == $past(q));
```

此處 `$past(q)` 回傳 `q` 在前一個時脈所持有的值——它本身也是一個取樣值——這正是第二個正反器所擷取的值。

## 時脈是參考

並行斷言沒有時脈便毫無意義。時脈同時定義兩件事：

1. **取樣何時發生**——值在 Preponed 取樣，相對於所指定的時脈緣。
2. **「一個週期之後」代表什麼**——序列或性質中的每一個時序步驟（`##1`、`|=>` 等）都依該時脈的一個跳動前進。

```systemverilog
// @(posedge clk) is the sampling and stepping reference for the whole property
assert property (@(posedge clk) start |=> ##2 done);
```

此處 `start`、`done` 與 `##2` 延遲全部相對於 `posedge clk` 衡量。斷言不在意牆鐘時間或 delta 週期；它計算其時脈的邊緣數。第 8 章介紹如何以 default clocking 區塊一次設定此時脈，以及 `disable iff` 如何處理重置。

## 取樣值與程序式值

由於程序式程式碼（在 `always` 區塊中）在 Active 區域執行，而並行斷言在 Preponed 取樣，兩者在同一時間步可能看到不同的值。這是刻意的，值得牢記：

- `always` 區塊中的即時斷言看到**當前**、執行中途的值，如同任何程序式語句。
- 並行斷言看到**取樣**（Preponed）的值。

```systemverilog
always_comb begin
    x = a + b;            // x updates here, in the Active region
    assert (x < LIMIT);   // immediate: sees the new x right now
end

// concurrent: would sample x in Preponed — its value before this step
assert property (@(posedge clk) x < LIMIT);
```

若混用兩者，務必釐清區別：即時看*現在*，並行看*邊緣處的值*。

> **設計意圖。** 取樣值讓斷言以正反器的方式對設計推理——針對時脈緣處存在的穩定值，
> 而非單一時間步的暫態翻動。正是這份穩定性，使並行斷言成為可靠的意圖陳述，
> 而非排程順序的人質。

## 常見陷阱

- **期望並行斷言看到剛被指定的值。** 它在 Preponed 取樣，因此看到的是邊緣前的值，而非某個 `always` 區塊本步正在寫入的值。
- **混淆即時與並行的時序。** 程序式程式碼中的即時 `assert` 看當前值；並行的 `assert property` 看取樣值。兩者在同一步內可能不同。
- **寫一個無時脈的並行斷言並期望它「自動運作」。** 沒有時脈（明確或預設），就沒有取樣參考。第 8 章介紹 default clocking。
- **對 delta 週期推理。** 斷言計算時脈邊緣，而非 delta。請以斷言時脈的週期思考，而非以模擬器排程步驟思考。

## 小結

- 一個時間步被劃分為有序區域；Preponed、Active、Observed 與 Reactive 是對斷言重要的幾個。
- 並行斷言在 Preponed 區域取得**取樣值**——時脈緣之前的值。
- 在 Preponed 取樣使結果獨立於排程競態。
- 時脈是取樣與時序推進的單一參考。
- 即時斷言看當前的程序式值；並行斷言看取樣值，兩者在同一步內可能不同。

---

[← 為何需要斷言](01-why-assertions.md) · [目錄](../README.md) · [下一章：斷言種類 →](03-assertion-kinds.md)
