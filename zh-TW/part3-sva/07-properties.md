# 第三部 · 7. property

[← sequence operation](06-sequence-operations.md) · [目錄](../README.md) · [下一章：clock 與 reset →](08-clocking-and-reset.md)

## 學習目標

- 區分 property 與 sequence。
- 使用重疊 `|->` 與非重疊 `|=>` implication。
- 辨識 antecedent 與 consequent，並理解 vacuity（vacuous pass）。
- 以 `not`、`and`、`or`、`if/else` 組合 property。
- 使用時序運算子 `nexttime`、`until`、`eventually` 及其強形式。
- 命名與參數化 property。

## 設計者 mental model

property 把 pattern 變成 obligation。antecedent 命名 trigger；consequent 命名 design 在 trigger
發生時必須做什麼。因此 implication 是一種 contract 形狀：如果左邊發生，右邊必須在指定 timing
成立。

大多數 property bug 都是 contract bug。antecedent 可能太寬、太少見、或意外 impossible；consequent
可能早一個 cycle 或晚一個 cycle；property 也可能因 trigger 從未發生而 vacuous pass。請把每個
implication 讀成一句話，並檢查左右兩半。

## property 與 sequence

**sequence**描述一個*匹配*或不匹配的樣式。**property**是一個*成立*或*失敗*的陳述——它是 `assert`、`assume` 或 `cover` 所評估的對象。property 由 sequence、布林與本章的運算子建構。其中最重要的運算子是 implication。

## implication

implication 把觸發樣式連結到所要求的回應。左側是**antecedent**；右側是**consequent**。該 property 說：*每當 antecedent 匹配，consequent 就必須成立。*

有兩種形式，差別只在 consequent 何時開始。

### 重疊：|->

`|->` 是**重疊**implication。consequent 從 antecedent 完成的*同一*週期開始檢查：

```systemverilog
// In the same cycle req is high, gnt must already be high
assert property (@(posedge clk) req |-> gnt);
```

把 `a |-> b` 讀作「當 `a`，則*現在* `b`」。

### 非重疊：|=>

`|=>` 是**非重疊**implication。consequent 從 antecedent 完成的*下一*週期開始檢查：

```systemverilog
// One cycle after req, gnt must be high
assert property (@(posedge clk) req |=> gnt);
```

把 `a |=> b` 讀作「當 `a`，則*下一週期* `b`」。它完全等同於 `a |-> ##1 b`。在 `|->` 與 `|=>` 之間選擇，就是選擇回應是同時的還是延後一個週期——這個區別直接對應到握手是組合的還是被暫存的。

## antecedent、consequent 與 vacuity

當 antecedent 在某個起始點*不*匹配時，該 implication 在那個起始點被視為已滿足——本就沒有義務需要達成。這就是**vacuity**（vacuous pass）。

```systemverilog
// If req is never high, this passes vacuously every cycle —
// the consequent gnt is never required
assert property (@(posedge clk) req |=> gnt);
```

vacuity 是正確且必要的：「每個請求都被授權」不應只因為沒有請求發生而失敗。但它有一個陷阱。一個*只會*vacuous pass 的 property 什麼也沒檢查，並給予虛假的信心。補救之道是對 antecedent 下一個 `cover`，以確認它確實發生：

```systemverilog
// Confirm the antecedent is real, not just vacuously satisfied
cover property (@(posedge clk) req);
```

把 implication 與其 antecedent 的 `cover` 配對是標準的紀律：`assert` 證明回應，`cover` 證明觸發確實發生。

## property operator：not、and、or、if/else

property 以自身的邏輯運算子組合：

- **`not p`**——當 property `p` 失敗時成立。用它陳述某行為*絕不能*發生。
- **`p1 and p2`**——兩者都必須成立。
- **`p1 or p2`**——至少一者必須成立。
- **`if (cond) p1 else p2`**——依布林條件選擇 property。

```systemverilog
// An overflow must never follow a write to a full FIFO
assert property (@(posedge clk) not (wr_en && full ##1 overflow));

// Different latency depending on mode
assert property (@(posedge clk)
    start |=> if (fast_mode) done else ##1 done);
```

`not` 是**safety property**——「某種壞事絕不發生」——的自然形式。`if/else` 形式讓一個 assertion 涵蓋多種組態而不必複製 antecedent。

## 時序 property operator

除 implication 外，property 還有借自時序邏輯的時序運算子。每個都有*弱*與*強*形式；強形式額外要求所等待的事件確實在軌跡中發生。

### nexttime 與 s_nexttime

- **`nexttime p`**——`p` 必須在下一週期成立（弱）。
- **`s_nexttime p`**——`p` 必須在下一週期成立，且該下一週期必須存在（強）。

```systemverilog
assert property (@(posedge clk) start |-> nexttime busy);
```

### until、s_until、until_with、s_until_with

- **`p until q`**——`p` 在 `q` 變為真的週期之前（不含該週期）的每個週期都成立；弱形式，因此 `q` 不必曾發生。
- **`s_until`**——強：`q` *必須*最終變為真。
- **`until_with` / `s_until_with`**——相同，但 `p` 也必須在 `q` 變為真的週期*當下*成立（含端點）。

```systemverilog
// req must stay asserted until ack, and ack must eventually arrive
assert property (@(posedge clk) $rose(req) |-> req s_until ack);
```

弱／強的選擇回答「釋放事件是否必須確實發生？」對於 `ack` 受保證的握手，使用強形式，使缺少 `ack` 成為失敗；對於盡力而為的條件，弱形式才對。

### eventually 與 s_eventually

- **`s_eventually p`**——`p` 必須在某個未來週期成立（強，可為無界）。這是**liveness property**——「某種好事最終發生」——的形式。
- **`eventually [m:n] p`**——弱、*有界*形式：`p` 必須在給定的週期窗口內成立。

```systemverilog
// After request, a grant must eventually be issued (liveness)
assert property (@(posedge clk) req |-> s_eventually gnt);
```

liveness property 無法被任何有限 simulation 軌跡證偽——總是還有「更多時間」——因此 `s_eventually` 主要是 formal verification 的工具。在 simulation 中，請優先採用施加真實期限的有界形式（`##[1:N]` 或 `eventually [1:N]`）。

## 命名 property

如同 sequence，以 `property` 宣告可重用或複雜的 property，並給它引數以服務多個實例：

```systemverilog
// Reusable request/acknowledge property
property req_ack(req, ack, int n);
    @(posedge clk) $rose(req) |-> ##[1:n] ack;
endproperty

assert property (req_ack(rd_req, rd_ack, 4));
assert property (req_ack(wr_req, wr_ack, 8));
```

命名 property 把意圖記錄一次，並套用於該樣式重複出現的每一處，使一整批相似的檢查保持一致且易於維護。

> **設計意圖。** property 是意圖的完整陳述：*這個觸發要求這個回應。* implication 命名觸發（antecedent）
> 與義務（consequent）；`not` 陳述什麼絕不能發生；時序運算子陳述什麼必須在某事件之前保持、
> 或在某事件之前發生。vacuity 使陳述對「觸發從未發生」的情況保持誠實——把它與 `cover` 配對，
> 以確知觸發確實發生過。

## 常見陷阱

- **混淆 `|->` 與 `|=>`。** 重疊在同一週期檢查 consequent；非重疊在下一週期檢查。請依回應是組合的還是被暫存的來選形式。
- **忽略 vacuity。** 一個只會 vacuous pass 的 implication 什麼也沒檢查。請 cover antecedent 以確認它發生。
- **在 simulation 中使用 `s_eventually`。** liveness property 沒有有限的反例。simulation 中請用有界窗口設定真實期限；把 `s_eventually` 保留給 formal。
- **以 `until` 忘記端點。** 單純的 `until` 排除 `q` 成立的那個週期；當 `p` 也必須在該週期成立時請用 `until_with`。
- **在事件受保證時選了弱形式。** 若釋放事件必須發生，請用強 `s_` 形式，使其缺席成為失敗，而非無聲的通過。

## 小結

- sequence 匹配；property 成立或失敗，是 `assert`／`cover` 所評估的對象。
- `|->` 在同一週期檢查 consequent；`|=>` 在下一週期檢查。
- antecedent 從不匹配時發生 vacuous pass；cover antecedent 以使檢查保持有意義。
- `not`、`and`、`or`、`if/else` 組合 property；`not` 表達安全性。
- `nexttime`、`until`／`until_with` 與 `eventually` 有弱與強形式；強形式要求所等待的事件發生且適合 formal，有界形式則適合 simulation。

---

[← sequence operation](06-sequence-operations.md) · [目錄](../README.md) · [下一章：clock 與 reset →](08-clocking-and-reset.md)
