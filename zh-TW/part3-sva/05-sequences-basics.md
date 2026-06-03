# 第三部 · 5. 序列：基礎

[← 布林層](04-boolean-layer.md) · [目錄](../README.md) · [下一章：序列運算 →](06-sequence-operations.md)

## 學習目標

- 把序列（sequence）描述為跨時脈週期的布林樣式。
- 使用固定與範圍的週期延遲 `##n` 與 `##[m:n]`。
- 使用無界延遲 `##[*]` 與 `##[+]`。
- 以連續 `[*n]`、goto `[->n]` 與非連續 `[=n]` 進行重複。
- 以 `sequence` 構造命名可重用的序列。

## 序列是什麼

**序列**（sequence，序列）描述跨時脈週期的事件：一連串布林條件必須在連續取樣點上成立的樣式。布林層（第 4 章）談論一個邊緣，序列則談論一連串邊緣。序列是性質（第 7 章）的構件。

最簡單的序列是單一布林——它在一個週期匹配。序列的威力來自把布林跨時間串接的*週期延遲*。

## 週期延遲：##n

週期延遲運算子 `##n` 推進斷言時脈的 `n` 個時脈。把 `a ##1 b` 讀作「本週期 `a`，然後下一週期 `b`」：

```systemverilog
// req this cycle, gnt the very next cycle
sequence req_then_gnt;
    req ##1 gnt;
endsequence
```

`##0` 意指「同一週期」——兩個布林在同一邊緣取樣，因此 `a ##0 b` 等同於 `a && b`。較大的數字會跳過週期：

```systemverilog
// start, then exactly two cycles later, done
sequence start_done;
    start ##2 done;        // start at cycle k, done at cycle k+2
endsequence
```

中間的週期不受 `##2` 約束——只檢查端點。若你需要約束間隔，請使用重複（見下）或序列運算（第 6 章）。

## 範圍延遲：##[m:n]

延遲可以是*範圍*，意指「在 `m` 到 `n` 個週期之後的某處」：

```systemverilog
// done arrives 1 to 3 cycles after start
sequence start_done_window;
    start ##[1:3] done;
endsequence
```

若 `done` 在窗口內*任一*週期為真，便匹配。這是表達有餘裕的延遲——「結果在三個週期內回來」——的自然方式，而非固定的管線深度。範圍延遲可能產生同一序列的多個匹配；第 6 章的 `first_match` 將其修剪為最早者。

## 無界延遲：##[*] 與 ##[+]

兩個簡寫涵蓋開放式等待：

- **`##[*]`** 是 `##[0:$]`——零個或多個週期，無界。
- **`##[+]`** 是 `##[1:$]`——一個或多個週期，無界。

```systemverilog
// After req, gnt happens eventually (some cycle, 1 or more later)
sequence req_eventually_gnt;
    req ##[+] gnt;
endsequence
```

`$` 意指「無上界」。對沒有固定期限的「最終會」樣式使用無界延遲。請注意：在純模擬中，無界等待可能在測試內永不完成；當你需要真正的期限時，請搭配強性質（第 7 章）或有界窗口。

## 連續重複：[*n] 與 [*m:n]

`b[*n]` 意指布林 `b` 在 `n` 個連續週期上成立。它是 `b ##1 b ##1 …` 的簡寫：

```systemverilog
// stall held high for exactly 4 consecutive cycles
sequence stall4;
    stall[*4];
endsequence

// busy held high for 2 to 5 consecutive cycles
sequence busy_run;
    busy[*2:5];
endsequence
```

連續重複是你陳述「保持 N 個週期」的方式——保持時間、固定停滯、最小脈衝寬度。序列本身也可被重複，不只布林：`(a ##1 b)[*3]` 把這兩週期的樣式背靠背重複三次。

## goto 重複：[->n]

`b[->n]` 是 **goto** 重複：它在 `b` 第 `n` 次出現的週期匹配，且各次出現不必連續。匹配點恰好是計數達到 `n` 之時：

```systemverilog
// From req, wait until the 3rd ack (acks may be spread out), then ready
sequence three_acks;
    req ##1 ack[->3] ##1 ready;
endsequence
```

此處 `ack[->3]` 推進各週期直到 `ack` 已為真三次，匹配落在那第三次 `ack` 上。`##1 ready` 接著檢查第三次 `ack` 之後緊接的那個週期。使用 goto 重複來計數不規則抵達的事件。

## 非連續重複：[=n]

`b[=n]` 是**非連續**重複。如同 goto，它計數 `b` 的 `n` 次（不必連續）出現，但匹配點*不*釘在最後一次出現——它可延伸超過之，允許在第 `n` 次匹配之後出現 `b` 為假的週期：

```systemverilog
// Exactly two writes occur, then (later) a flush
sequence two_writes_then_flush;
    wr[=2] ##1 flush;
endsequence
```

它與 goto 的差別微妙但真實：

- `b[->n] ##1 c` 要求在第 `n` 次 `b` 之後緊接的週期 `c`。
- `b[=n] ##1 c` 允許在第 `n` 次 `b` 與 `c` 之間有閒置週期（`b` 為假）。

當下一個事件必須緊接被計數的事件時用 `[->n]`，當之間可能有間隔時用 `[=n]`。

## 命名序列

行內撰寫的序列在單次使用時無妨。當樣式被重用，或複雜到值得命名時，以 `sequence` 構造宣告它，該構造可接受引數：

```systemverilog
// Parameterized, reusable handshake sequence
sequence ack_within(int n);
    req ##[1:n] ack;
endsequence

assert property (@(posedge clk) $rose(req) |-> ack_within(4));
```

命名序列可記錄意圖，並讓同一樣式在整個設計中被斷言、覆蓋與重用。引數使一個宣告服務於多種延遲或寬度。

> **設計意圖。** 序列捕捉一個預期行為的*隨時間的形狀*：請求然後授權、四週期停滯、第三次確認。
> 週期延遲與重複讓你精確地畫出那個形狀——以 `##n` 表固定深度、以 `##[m:n]` 表延遲窗口、
> 以 `[*n]` 表保持時間、以 `[->n]` 表被計數的事件。序列是設計者的時序圖，以工具可檢查的方式寫下。

## 常見陷阱

- **把 `##2` 讀作「兩個週期內」。** 它意指*恰好*兩個週期之後。要表窗口請用 `##[1:2]`。
- **混淆 `[*n]` 與 `[->n]`。** `[*n]` 要求 `n` 個*連續*週期；`[->n]` 計數可分散的 `n` 次*出現*。
- **混淆 `[->n]` 與 `[=n]`。** goto 把匹配釘在最後一次出現；非連續允許後續的閒置週期再接下一項。
- **純模擬中的無界延遲。** `##[+]` 在有限測試內可能永不完成。需要期限時請用有界窗口或強性質。
- **到處內嵌複雜序列。** 以 `sequence` 命名它，使意圖只記錄一次並被重用，且修正只落在一處。

## 小結

- 序列是跨時脈週期的布林樣式，建構於布林層之上。
- `##n` 是確切延遲，`##[m:n]` 是窗口，`##[*]`／`##[+]` 是無界等待。
- `[*n]` 連續重複；`[->n]` 計數出現並把匹配釘在最後一次；`[=n]` 計數出現但允許後續閒置週期。
- 以 `sequence` 命名可重用或複雜的序列，並可參數化。

---

[← 布林層](04-boolean-layer.md) · [目錄](../README.md) · [下一章：序列運算 →](06-sequence-operations.md)
