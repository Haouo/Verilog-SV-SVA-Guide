# 第三部 · 5. sequence basics

[← 布林層](04-boolean-layer.md) · [目錄](../README.md) · [下一章：sequence operation →](06-sequence-operations.md)

## 學習目標

- 把 sequence 描述為跨 clock 週期的布林樣式。
- 使用固定與範圍的週期延遲 `##n` 與 `##[m:n]`。
- 使用無界延遲 `##[*]` 與 `##[+]`。
- 用連續 `[*n]`、goto `[->n]` 與非連續 `[=n]` 三種方式表達重複。
- 以 `sequence` 構造命名可重用的 sequence。

## 設計者的心智模型

sequence 是行為隨時間呈現的形狀。它還沒有規定這個行為是否非發生不可，只是描述什麼樣的事件樣式才算匹配。這種拆分很有用：先定義樣式，再用 property 規定這個樣式何時必須發生、何時不可發生。

請用時間軸來思考。`##1` 代表下一個取樣的 clock,範圍代表一個窗口，重複則代表同一個條件佔據好幾個可能的週期。當某個 sequence 的行為出乎你的意料，就把起點、終點，以及每個可能參與匹配的週期都畫出來。

## sequence 是什麼

**sequence** 描述跨 clock 週期的事件，也就是一連串布林條件必須在連續取樣點上成立的樣式。布林層(第 4 章)談的是單一邊緣，sequence 談的則是一連串邊緣。sequence 是 property(第 7 章)的構件。

最簡單的 sequence 是單一布林，它在一個週期就匹配。sequence 的威力來自*週期延遲*,把布林跨時間串接起來。

## 週期延遲：##n

週期延遲運算子 `##n` 推進 assertion clock 的 `n` 個 clock。把 `a ##1 b` 讀作「本週期 `a`，然後下一週期 `b`」：

```systemverilog
// req this cycle, gnt the very next cycle
sequence req_then_gnt;
    req ##1 gnt;
endsequence
```

`##0` 代表「同一週期」，兩個布林在同一邊緣取樣，因此 `a ##0 b` 等同於 `a && b`。數字較大時會跳過中間的週期：

```systemverilog
// start, then exactly two cycles later, done
sequence start_done;
    start ##2 done;        // start at cycle k, done at cycle k+2
endsequence
```

中間的週期不受 `##2` 約束，只檢查兩個端點。若要約束中間的間隔，請使用重複(見下)或 sequence operation(第 6 章)。

## 範圍延遲：##[m:n]

延遲可以是一個*範圍*,代表「在 `m` 到 `n` 個週期之後的某一刻」：

```systemverilog
// done arrives 1 to 3 cycles after start
sequence start_done_window;
    start ##[1:3] done;
endsequence
```

只要 `done` 在窗口內任一週期為真，就算匹配。要表達有餘裕的延遲(例如「結果在三個週期內回來」)而非固定的管線深度，這是最自然的寫法。範圍延遲可能讓同一個 sequence 產生多個匹配，第 6 章的 `first_match` 會把這些匹配收斂為最早的一個。

## 無界延遲：##[*] 與 ##[+]

兩個簡寫涵蓋開放式等待：

- **`##[*]`** 即 `##[0:$]`,代表零個或多個週期，無上界。
- **`##[+]`** 即 `##[1:$]`,代表一個或多個週期，無上界。

```systemverilog
// After req, gnt happens eventually (some cycle, 1 or more later)
sequence req_eventually_gnt;
    req ##[+] gnt;
endsequence
```

`$` 代表「沒有上界」。對於沒有固定期限的「最終會發生」樣式，就用無界延遲。但要留意：在純 simulation 中，無界等待可能在整個測試裡都等不到結果；若需要真正的期限，請搭配強 property(第 7 章)或有界窗口。

## 連續重複：[*n] 與 [*m:n]

`b[*n]` 代表布林 `b` 在 `n` 個連續週期上都成立，是 `b ##1 b ##1 …` 的簡寫：

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

連續重複用來陳述「保持 N 個週期」這類條件，例如保持時間、固定停滯、最小脈衝寬度。可重複的不只是布林，sequence 本身也可以：`(a ##1 b)[*3]` 把這個兩週期的樣式接連重複三次。

## goto 重複：[->n]

`b[->n]` 是 **goto** 重複：它在 `b` 第 `n` 次出現的週期匹配，而各次出現不必連續。匹配點恰好落在計數達到 `n` 的那一刻：

```systemverilog
// From req, wait until the 3rd ack (acks may be spread out), then ready
sequence three_acks;
    req ##1 ack[->3] ##1 ready;
endsequence
```

這裡的 `ack[->3]` 會逐週期推進，直到 `ack` 已為真三次，匹配就落在那第三次 `ack` 上。接著 `##1 ready` 檢查第三次 `ack` 之後緊接的那個週期。要計數不規則抵達的事件，就用 goto 重複。

## 非連續重複：[=n]

`b[=n]` 是**非連續**重複。它和 goto 一樣計數 `b` 的 `n` 次出現(不必連續),但匹配點*不*釘在最後一次出現上，而可以再往後延伸，允許在第 `n` 次匹配之後出現 `b` 為假的週期：

```systemverilog
// Exactly two writes occur, then (later) a flush
sequence two_writes_then_flush;
    wr[=2] ##1 flush;
endsequence
```

它和 goto 的差別雖然細微，卻真實存在：

- `b[->n] ##1 c` 要求在第 `n` 次 `b` 之後緊接的週期 `c`。
- `b[=n] ##1 c` 允許在第 `n` 次 `b` 與 `c` 之間有閒置週期（`b` 為假）。

當下一個事件必須緊接被計數的事件時用 `[->n]`，當之間可能有間隔時用 `[=n]`。

## 命名 sequence

只用一次的 sequence,寫在行內就好。當一個樣式要重複使用，或複雜到值得取個名字時，就用 `sequence` 構件來宣告；這個構件還能接受引數：

```systemverilog
// Parameterized, reusable handshake sequence
sequence ack_within(int n);
    req ##[1:n] ack;
endsequence

assert property (@(posedge clk) $rose(req) |-> ack_within(4));
```

為 sequence 命名能記錄設計意圖，也讓同一個樣式可以在整個設計中被 assert、被 cover、被重複使用。有了引數，一個宣告就能服務多種延遲或寬度。

> **設計意圖。** sequence 捕捉的是一個預期行為*隨時間呈現的形狀*:先請求再授權、停滯四個週期、第三次確認。
> 週期延遲與重複讓你把這個形狀精確地畫出來：`##n` 表固定深度、`##[m:n]` 表延遲窗口、
> `[*n]` 表保持時間、`[->n]` 表被計數的事件。sequence 就是設計者的時序圖，只是寫成了工具能檢查的形式。

## 常見陷阱

- **把 `##2` 讀成「兩個週期內」。** 它指的是*恰好*兩個週期之後。要表達窗口請用 `##[1:2]`。
- **混淆 `[*n]` 與 `[->n]`。** `[*n]` 要求 `n` 個*連續*週期；`[->n]` 計數的是可以分散開來的 `n` 次*出現*。
- **混淆 `[->n]` 與 `[=n]`。** goto 把匹配釘在最後一次出現上；非連續則允許後面再接幾個閒置週期才進入下一項。
- **在純 simulation 中使用無界延遲。** `##[+]` 在有限的測試裡可能永遠等不完。需要期限時請改用有界窗口或強 property。
- **到處內嵌複雜的 sequence。** 用 `sequence` 為它命名，意圖只記錄一次就能重複使用，日後要修正也只動一處。

## 小結

- sequence 是建構在布林層之上、跨 clock 週期的布林樣式。
- `##n` 是確切延遲，`##[m:n]` 是窗口，`##[*]`／`##[+]` 是無界等待。
- `[*n]` 連續重複；`[->n]` 計數出現並把匹配釘在最後一次；`[=n]` 計數出現但允許後面接幾個閒置週期。
- 用 `sequence` 為可重用或複雜的 sequence 命名，還可加上參數。

---

[← 布林層](04-boolean-layer.md) · [目錄](../README.md) · [下一章：sequence operation →](06-sequence-operations.md)
