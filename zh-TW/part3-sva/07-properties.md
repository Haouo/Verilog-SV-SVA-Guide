# 第三部 · 7. property

[← sequence operation](06-sequence-operations.md) · [目錄](../README.md) · [下一章：clock 與 reset →](08-clocking-and-reset.md)

## 學習目標

- 區分 property 與 sequence。
- 使用重疊 `|->` 與非重疊 `|=>` implication。
- 辨識 antecedent 與 consequent，並理解 vacuity（vacuous pass）。
- 以 `not`、`and`、`or`、`if/else` 組合 property。
- 使用時序運算子 `nexttime`、`until`、`eventually` 及其強形式。
- 命名與參數化 property。

## 設計者的心智模型

property 把樣式變成義務。antecedent 指出觸發的條件，consequent 則指出設計在觸發發生時必須做什麼。因此 implication 是一種契約的形狀：左邊一旦發生，右邊就必須在指定的時間點成立。

大多數 property 的錯誤其實都是契約的錯誤。antecedent 可能太寬、太少見，或意外地永遠不成立；consequent 可能早一個週期或晚一個週期；property 也可能因為觸發從未發生而 vacuous pass。請把每個 implication 都讀成一句話，左右兩半都檢查。

## 從問題開始

sequence 只回答「這個時間形狀有沒有出現」。但設計規則通常更進一步：「如果請求出現，回應就必須在期限內出現」、「如果 FIFO 已滿，就絕不能再寫」。這些句子都有一個觸發條件，以及觸發後的義務。

property 就是把形狀變成義務的地方。左邊的 antecedent 問「什麼情況開啟檢查」，右邊的 consequent 問「開啟後設計欠我們什麼」。本章的 `|->`、`|=>`、vacuity 與強弱時序運算子，都是在精準化這份契約：何時開始欠、欠到什麼時候、沒有觸發時又該怎麼解讀。

## property 與 sequence

**sequence** 描述的是一個會*匹配*或不匹配的樣式。**property** 則是一個會*成立*或*失敗*的陳述，也就是 `assert`、`assume` 或 `cover` 所評估的對象。property 由 sequence、布林與本章的運算子建構而成，其中最重要的運算子是 implication。

## implication

implication 把觸發樣式連到所要求的回應。左側是 **antecedent**(前件),右側是 **consequent**(後件)。這個 property 的意思是：*每當 antecedent 匹配，consequent 就必須成立。*

它有兩種形式，差別只在 consequent 從何時開始。

### 重疊：|->

`|->` 是**重疊** implication。consequent 從 antecedent 完成的*同一*個週期開始檢查：

```systemverilog
// In the same cycle req is high, gnt must already be high
assert property (@(posedge clk) req |-> gnt);
```

把 `a |-> b` 讀成「`a` 成立時，`b` *此刻*就要成立」。

### 非重疊：|=>

`|=>` 是**非重疊** implication。consequent 從 antecedent 完成的*下一*個週期開始檢查：

```systemverilog
// One cycle after req, gnt must be high
assert property (@(posedge clk) req |=> gnt);
```

把 `a |=> b` 讀成「`a` 成立時，`b` 要在*下一個週期*成立」。它完全等同於 `a |-> ##1 b`。在 `|->` 與 `|=>` 之間做選擇，就是在決定回應要同時發生還是延後一個週期，而這個區別正好對應到握手是組合的還是被暫存的。

## antecedent、consequent 與 vacuity

當 antecedent 在某個起始點*不*匹配時，該 implication 在那個起始點就視為已滿足，因為本來就沒有義務要達成。這就是**空真**(vacuous pass)。

```systemverilog
// If req is never high, this passes vacuously every cycle —
// the consequent gnt is never required
assert property (@(posedge clk) req |=> gnt);
```

空真是正確且必要的：「每個請求都會被授權」不該只因為沒有請求發生就判為失敗。但它藏著一個陷阱：一個*只會*空真通過的 property 其實什麼都沒檢查，卻給人一種虛假的信心。補救之道是對 antecedent 下一個 `cover`,確認它確實發生過：

```systemverilog
// Confirm the antecedent is real, not just vacuously satisfied
cover property (@(posedge clk) req);
```

把 implication 跟它 antecedent 的 `cover` 配成一對，是一種標準做法：`assert` 證明回應，`cover` 證明觸發確實發生過。

## property operator：not、and、or、if/else

property 也有自己的邏輯運算子可供組合：

- **`not p`**:當 property `p` 失敗時成立。用它來陳述某個行為*絕不能*發生。
- **`p1 and p2`**:兩者都必須成立。
- **`p1 or p2`**:至少一者必須成立。
- **`if (cond) p1 else p2`**:依布林條件選擇 property。

```systemverilog
// An overflow must never follow a write to a full FIFO
assert property (@(posedge clk) not (wr_en && full ##1 overflow));

// Different latency depending on mode
assert property (@(posedge clk)
    start |=> if (fast_mode) done else ##1 done);
```

要表達 **safety property**(安全性性質),也就是「某種壞事絕不會發生」，`not` 是最自然的形式。`if/else` 形式則讓一個 assertion 涵蓋多種組態，而不必複製 antecedent。

## 時序 property operator

除了 implication,property 還有一組借自時序邏輯的時序運算子。每個都有*弱*與*強*兩種形式；強形式額外要求所等待的事件確實在軌跡中發生。

### nexttime 與 s_nexttime

- **`nexttime p`**:`p` 必須在下一週期成立(弱)。
- **`s_nexttime p`**:`p` 必須在下一週期成立，而且該下一週期必須存在(強)。

```systemverilog
assert property (@(posedge clk) start |-> nexttime busy);
```

### until、s_until、until_with、s_until_with

- **`p until q`**:在 `q` 變為真的那個週期之前(不含該週期),`p` 每個週期都成立；這是弱形式，所以 `q` 不一定要發生。
- **`s_until`**:強形式，`q` *必須*最終變為真。
- **`until_with` / `s_until_with`**:意義相同，但 `p` 還必須在 `q` 變為真的那個週期*當下*也成立(含端點)。

```systemverilog
// req must stay asserted until ack, and ack must eventually arrive
assert property (@(posedge clk) $rose(req) |-> req s_until ack);
```

弱與強之間的取捨，回答的是「釋放事件到底必不必須發生？」這個問題。對於 `ack` 有保證的握手，用強形式，讓缺少 `ack` 直接判為失敗；對於盡力而為的條件，弱形式才合適。

### eventually 與 s_eventually

- **`s_eventually p`**:`p` 必須在某個未來週期成立(強形式，可為無界)。要表達 **liveness property**(活性性質),也就是「某種好事最終會發生」，用的就是這個形式。
- **`eventually [m:n] p`**:弱、*有界*的形式，`p` 必須在給定的週期窗口內成立。

```systemverilog
// After request, a grant must eventually be issued (liveness)
assert property (@(posedge clk) req |-> s_eventually gnt);
```

任何有限的 simulation 軌跡都無法證偽 liveness property,因為時間永遠「還沒走完」，所以 `s_eventually` 主要是 formal verification 的工具。在 simulation 中，請優先採用能施加真實期限的有界形式(`##[1:N]` 或 `eventually [1:N]`)。

## 命名 property

就像 sequence 一樣，可重用或複雜的 property 也用 `property` 來宣告，並加上引數以服務多個實例：

```systemverilog
// Reusable request/acknowledge property
property req_ack(req, ack, int n);
    @(posedge clk) $rose(req) |-> ##[1:n] ack;
endproperty

assert property (req_ack(rd_req, rd_ack, 4));
assert property (req_ack(wr_req, wr_ack, 8));
```

為 property 命名，意圖只記錄一次，卻能套用到該樣式重複出現的每一處，讓一整批相似的檢查保持一致、也好維護。

> **設計意圖。** property 是意圖的完整陳述：*這個觸發要求這個回應。* implication 指出觸發(antecedent)
> 與義務(consequent);`not` 陳述什麼絕不能發生；時序運算子陳述什麼必須保持到某事件、
> 或必須在某事件之前發生。空真讓陳述對「觸發從未發生」的情況保持誠實，把它與 `cover` 配對，
> 你就能確知觸發確實發生過。

## 常見陷阱

- **混淆 `|->` 與 `|=>`。** 重疊在同一個週期檢查 consequent;非重疊在下一個週期才檢查。請依回應是組合的還是被暫存的來選形式。
- **忽略空真。** 一個只會空真通過的 implication 其實什麼都沒檢查。請 cover antecedent,確認它確實發生。
- **在 simulation 中使用 `s_eventually`。** liveness property 沒有有限的反例。simulation 中請用有界窗口設定真實期限，`s_eventually` 留給 formal。
- **用 `until` 卻漏掉端點。** 單純的 `until` 不含 `q` 成立的那個週期；當 `p` 在該週期也必須成立時，請改用 `until_with`。
- **事件有保證時卻選了弱形式。** 若釋放事件必定發生，請用強的 `s_` 形式，讓它的缺席判為失敗，而不是無聲通過。

## 小結

- sequence 會匹配；property 會成立或失敗，是 `assert`／`cover` 所評估的對象。
- `|->` 在同一個週期檢查 consequent;`|=>` 在下一個週期才檢查。
- antecedent 從不匹配時就發生空真；cover antecedent 才能讓檢查保持有意義。
- `not`、`and`、`or`、`if/else` 可組合 property;`not` 用來表達安全性。
- `nexttime`、`until`／`until_with` 與 `eventually` 都有弱與強形式；強形式要求所等待的事件確實發生、適合 formal,有界形式則適合 simulation。

---

[← sequence operation](06-sequence-operations.md) · [目錄](../README.md) · [下一章：clock 與 reset →](08-clocking-and-reset.md)
