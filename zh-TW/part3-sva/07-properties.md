# 第三部 · 7. 性質（property）

[← 序列運算](06-sequence-operations.md) · [目錄](../README.md) · [下一章：時脈與重置 →](08-clocking-and-reset.md)

## 學習目標

- 區分性質與序列。
- 使用重疊 `|->` 與非重疊 `|=>` 蘊涵。
- 辨識前提與後件，並理解空真（vacuous pass）。
- 以 `not`、`and`、`or`、`if/else` 組合性質。
- 使用時序運算子 `nexttime`、`until`、`eventually` 及其強形式。
- 命名與參數化性質。

## 性質與序列

**序列**（sequence，序列）描述一個*匹配*或不匹配的樣式。**性質**（property，性質）是一個*成立*或*失敗*的陳述——它是 `assert`、`assume` 或 `cover` 所評估的對象。性質由序列、布林與本章的運算子建構。其中最重要的運算子是蘊涵。

## 蘊涵

蘊涵把觸發樣式連結到所要求的回應。左側是**前提**（antecedent，前提）；右側是**後件**（consequent，後件）。該性質說：*每當前提匹配，後件就必須成立。*

有兩種形式，差別只在後件何時開始。

### 重疊：|->

`|->` 是**重疊**蘊涵。後件從前提完成的*同一*週期開始檢查：

```systemverilog
// In the same cycle req is high, gnt must already be high
assert property (@(posedge clk) req |-> gnt);
```

把 `a |-> b` 讀作「當 `a`，則*現在* `b`」。

### 非重疊：|=>

`|=>` 是**非重疊**蘊涵。後件從前提完成的*下一*週期開始檢查：

```systemverilog
// One cycle after req, gnt must be high
assert property (@(posedge clk) req |=> gnt);
```

把 `a |=> b` 讀作「當 `a`，則*下一週期* `b`」。它完全等同於 `a |-> ##1 b`。在 `|->` 與 `|=>` 之間選擇，就是選擇回應是同時的還是延後一個週期——這個區別直接對應到握手是組合的還是被暫存的。

## 前提、後件與空真

當前提在某個起始點*不*匹配時，該蘊涵在那個起始點被視為已滿足——本就沒有義務需要達成。這就是**空真**（vacuous pass，空真／空泛成立）。

```systemverilog
// If req is never high, this passes vacuously every cycle —
// the consequent gnt is never required
assert property (@(posedge clk) req |=> gnt);
```

空真是正確且必要的：「每個請求都被授權」不應只因為沒有請求發生而失敗。但它有一個陷阱。一個*只會*空真通過的性質什麼也沒檢查，並給予虛假的信心。補救之道是對前提下一個 `cover`，以確認它確實發生：

```systemverilog
// Confirm the antecedent is real, not just vacuously satisfied
cover property (@(posedge clk) req);
```

把蘊涵與其前提的 `cover` 配對是標準的紀律：`assert` 證明回應，`cover` 證明觸發確實發生。

## 性質運算子：not、and、or、if/else

性質以自身的邏輯運算子組合：

- **`not p`**——當性質 `p` 失敗時成立。用它陳述某行為*絕不能*發生。
- **`p1 and p2`**——兩者都必須成立。
- **`p1 or p2`**——至少一者必須成立。
- **`if (cond) p1 else p2`**——依布林條件選擇性質。

```systemverilog
// An overflow must never follow a write to a full FIFO
assert property (@(posedge clk) not (wr_en && full ##1 overflow));

// Different latency depending on mode
assert property (@(posedge clk)
    start |=> if (fast_mode) done else ##1 done);
```

`not` 是**安全性性質**（safety property，安全性性質）——「某種壞事絕不發生」——的自然形式。`if/else` 形式讓一個斷言涵蓋多種組態而不必複製前提。

## 時序性質運算子

除蘊涵外，性質還有借自時序邏輯的時序運算子。每個都有*弱*與*強*形式；強形式額外要求所等待的事件確實在軌跡中發生。

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

- **`s_eventually p`**——`p` 必須在某個未來週期成立（強，可為無界）。這是**活性性質**（liveness property，活性性質）——「某種好事最終發生」——的形式。
- **`eventually [m:n] p`**——弱、*有界*形式：`p` 必須在給定的週期窗口內成立。

```systemverilog
// After request, a grant must eventually be issued (liveness)
assert property (@(posedge clk) req |-> s_eventually gnt);
```

活性性質無法被任何有限模擬軌跡證偽——總是還有「更多時間」——因此 `s_eventually` 主要是形式化驗證的工具。在模擬中，請優先採用施加真實期限的有界形式（`##[1:N]` 或 `eventually [1:N]`）。

## 命名性質

如同序列，以 `property` 宣告可重用或複雜的性質，並給它引數以服務多個實例：

```systemverilog
// Reusable request/acknowledge property
property req_ack(req, ack, int n);
    @(posedge clk) $rose(req) |-> ##[1:n] ack;
endproperty

assert property (req_ack(rd_req, rd_ack, 4));
assert property (req_ack(wr_req, wr_ack, 8));
```

命名性質把意圖記錄一次，並套用於該樣式重複出現的每一處，使一整批相似的檢查保持一致且易於維護。

> **設計意圖。** 性質是意圖的完整陳述：*這個觸發要求這個回應。* 蘊涵命名觸發（前提）
> 與義務（後件）；`not` 陳述什麼絕不能發生；時序運算子陳述什麼必須在某事件之前保持、
> 或在某事件之前發生。空真使陳述對「觸發從未發生」的情況保持誠實——把它與 `cover` 配對，
> 以確知觸發確實發生過。

## 常見陷阱

- **混淆 `|->` 與 `|=>`。** 重疊在同一週期檢查後件；非重疊在下一週期檢查。請依回應是組合的還是被暫存的來選形式。
- **忽略空真。** 一個只會空真通過的蘊涵什麼也沒檢查。請覆蓋前提以確認它發生。
- **在模擬中使用 `s_eventually`。** 活性性質沒有有限的反例。模擬中請用有界窗口設定真實期限；把 `s_eventually` 保留給形式化。
- **以 `until` 忘記端點。** 單純的 `until` 排除 `q` 成立的那個週期；當 `p` 也必須在該週期成立時請用 `until_with`。
- **在事件受保證時選了弱形式。** 若釋放事件必須發生，請用強 `s_` 形式，使其缺席成為失敗，而非無聲的通過。

## 小結

- 序列匹配；性質成立或失敗，是 `assert`／`cover` 所評估的對象。
- `|->` 在同一週期檢查後件；`|=>` 在下一週期檢查。
- 前提從不匹配時發生空真通過；覆蓋前提以使檢查保持有意義。
- `not`、`and`、`or`、`if/else` 組合性質；`not` 表達安全性。
- `nexttime`、`until`／`until_with` 與 `eventually` 有弱與強形式；強形式要求所等待的事件發生且適合形式化，有界形式則適合模擬。

---

[← 序列運算](06-sequence-operations.md) · [目錄](../README.md) · [下一章：時脈與重置 →](08-clocking-and-reset.md)
