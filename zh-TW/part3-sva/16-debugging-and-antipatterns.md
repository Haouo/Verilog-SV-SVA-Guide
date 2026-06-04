# 第三部 · 16. 除錯與反樣式

[← checker 與 library](15-checkers-and-libraries.md) · [目錄](../README.md) · [下一章：附錄 A — Verilog 與 SystemVerilog 對照 →](../appendices/A-verilog-vs-sv.md)

## 學習目標

- 解讀失敗的 assertion：找出嘗試（attempt）的起點，而非僅是失敗週期。
- 將失敗回溯穿過 antecedent，找到該負責的週期。
- 辨識常見的 SVA 錯誤，以及它們背後的反樣式。
- 套用使 assertion 保持可信的良好實務準則。

這是第三部的結尾章節。它建立在此前的一切之上，包括 sampling（第 2 章）、implication 與 vacuity（第 7、13 章）、clock 與 reset（第 8 章），以及第 10 章的各種樣式，接著轉向探討哪裡會出錯、又該如何修正。

## 設計者的心智模型

一條失敗的 assertion 是一件除錯工具。它應該告訴你：哪一項意圖被違反、那次違反的嘗試何時開始、以及什麼證據讓 consequent 失敗。如果 property 太大、clock 邊緣設錯、或被允許 vacuous pass，它就不再提供線索，反而變成干擾。

因此，除錯 SVA 既是在除錯設計，也是在除錯規格。assertion 失敗時兩邊都得查：RTL 可能錯了，property 也可能把規則寫錯了。反樣式清單的價值，就在於訓練你迅速認出第二種情況。

## 解讀失敗的 assertion

一條 concurrent assertion 失敗時，工具會回報義務被違反的那個週期。那個週期是整段故事的*終點*，不是起點。property 每當其 antecedent 有可能匹配時，就開啟一次新的**嘗試**；你看到的失敗，屬於某次在數個週期前就已開始的特定嘗試。除錯就是要找出*那一次*嘗試的起點。

```systemverilog
// Reported failure is at the cycle gnt should be high but isn't;
// the attempt started 1..N cycles earlier, when req rose
assert property ($rose(req) |-> ##[1:N] gnt);
```

步驟如下：

1. **記下工具回報的失敗週期**,也就是 consequent 的期限。
2. **回溯到開啟這次嘗試的那個 antecedent 匹配。** 對 `$rose(req) |-> ##[1:N] gnt` 來說，那是最近 *N* 個週期內的 `$rose(req)` 週期。
3. **檢視兩者之間的視窗。** bug 就是在那段跨距上讓 consequent 未能履行義務的原因：遺失的 `gnt`、被丟棄的請求，或視窗中途出錯的某個狀態。

多數 assertion 除錯器會在波形上畫出這段嘗試跨距，標出起點、中間各步驟，以及失敗週期。請讀整段跨距，而不是只看那個單一的紅色標記：成因幾乎總在失敗被標出之處的上游。

## 回溯穿過 antecedent

有一種微妙的失敗，問題其實出在*antecedent*本身。若 assertion「出乎意料地」失敗，請先檢查 antecedent 是不是在不該匹配的時候匹配了：

```systemverilog
// If this fails, ask first: did 'start' really rise here,
// or is the antecedent firing on a glitch the design didn't intend?
assert property ($rose(start) |=> busy);
```

一次失敗可能代表 consequent 錯了，*也可能*代表 antecedent 在設計者從未打算約束的情境裡觸發了。讀一下嘗試起點處 antecedent 的取樣值，就能分辨這兩者：真實的觸發配上壞掉的回應，是設計 bug；虛假的觸發，則是一條太過寬泛的 assertion。

## 常見錯誤與反樣式

### 錯誤的 clock 或錯誤的邊緣

在與邏輯不符的 clock 或邊緣上取樣，會產生看似隨機的失敗，因為 assertion 看到的值偏了半個週期（第 8 章）。

```systemverilog
// ANTI-PATTERN: design captures on posedge, assertion samples negedge
assert property (@(negedge clk) load |=> q == $past(d));
// FIX: match the capture edge
assert property (@(posedge clk) load |=> q == $past(d));
```

### 缺少 disable iff

沒有 reset 防護的 assertion，會在未知的啟動視窗期間觸發，回報出來的失敗其實只是 reset 行為。

```systemverilog
// ANTI-PATTERN: no reset guard — fires during reset
assert property (@(posedge clk) req |=> gnt);
// FIX: disable during reset
assert property (@(posedge clk) disable iff (!rst_n) req |=> gnt);
```

### vacuity 掩蓋 bug

antecedent 從不觸發的 implication 會 vacuous pass，什麼都沒驗證（第 13 章）。綠燈報告於是掩蓋了一條未測路徑。

```systemverilog
// ANTI-PATTERN: trusting this pass without checking the trigger ever occurred
assert property (mode_x && start |=> done);
// FIX: cover the antecedent so a zero count exposes the vacuity
cover property (mode_x && start);
```

### 運算子太強或太弱

在事件並無保證的地方用強運算子，會把一個合法情形變成失敗；在事件*確實*有保證的地方用弱運算子，又會讓一次真實的遺漏無聲通過（第 7 章）。

```systemverilog
// Too strong: forces ack to occur even when the protocol allows abort
assert property ($rose(req) |-> req s_until ack);
// Right strength when ack may legitimately never come:
assert property ($rose(req) |-> req until ack);
```

對盡力而為（best-effort）的條件選弱形式，唯有當解除事件由契約保證時才用強形式。

### 從不觸發的 antecedent

過於特定的 antecedent,合取項太多，或湊出一個不可能的組合，就從不匹配，於是 assertion 永遠空真。cover 計數為零就是徵兆（第 13 章）。請簡化 antecedent，直到它捕捉到真實的觸發。

### 一條 assertion 做太多事

把多項義務、區域變數記帳與巢狀運算子全塞進單一 property，既難讀又難除錯，失敗時還不告訴你*哪一*部分壞了。

```systemverilog
// ANTI-PATTERN: one giant property, opaque on failure
assert property (
    $rose(req) |-> (gnt && !err) ##1 (data_ok throughout (busy[*1:$] ##1 done))
                   and ##[1:8] resp
);
// BETTER: split into focused, independently reported checks
a_gnt:  assert property ($rose(req) |-> gnt && !err);
a_data: assert property ($rose(req) ##1 busy |-> data_ok throughout (busy[*1:$] ##1 done));
a_resp: assert property ($rose(req) |-> ##[1:8] resp);
```

數條小而具名的 assertion 各自精確指出自己的失敗，也各記錄一項意圖。請優先用它們，而非一整塊龐然大物。

## 良好實務準則

- **一條 assertion 一項意圖。** 小而具名的檢查能隔離失敗，讀起來也像文件。替它們命名，讓報告直接指向意圖。
- **clock 與 reset 只設一次。** 用 `default clocking` 與 `default disable iff`，讓沒有哪條 assertion 會漂到錯誤的邊緣，或在 reset 期間觸發（第 8 章）。
- **cover 每個 antecedent。** 把每條 implication 與其觸發的 cover 配對，讓 vacuity 躲不到綠燈報告後面（第 13 章）。
- **讓運算子強度符合契約。** 唯有事件有保證時才用強形式；盡力而為的條件用弱形式。
- **用區域變數捕捉資料，別用臨時邏輯。** 對管線化檢查，區域變數能乾淨地把回應 bind 到它特定的觸發（第 11 章）。
- **把獨立的 assertion bind 上去，讓 RTL 保持乾淨。** 可重用的檢查該住在 checker 與被 bind 的模組裡，而非被編輯進設計（第 9、15 章）。
- **讀整段嘗試跨距，別只看那個標記。** 失敗時，回溯到 antecedent 起點，檢視整個視窗。

> **設計意圖。** 一條 assertion 值不值得信賴，取決於它有多好除錯、有多誠實。一次失敗應該清楚指向一項壞掉的意圖；一次通過應該代表那項意圖確實被執行過。這些反樣式都模糊了其中之一：錯誤的 clock 讓失敗說謊，vacuity 讓通過說謊，過載的 property 則讓失敗無從讀起。良好實務讓每條 assertion 保持為一個小巧、帶 clock、被 cover、且單一的意圖陳述，這樣它一開口，設計者就能相信它。

## 常見陷阱

- **只從失敗週期除錯。** 成因在更早開始的那段嘗試視窗裡。請回溯到 antecedent。
- **錯誤的 clock 或邊緣。** 會產生看似隨機的失敗。請對齊設計的擷取邊緣。
- **缺少 `disable iff`。** reset 期間的活動被當成失敗回報。請用 `disable iff` 或 `default disable iff` 防護。
- **信賴 vacuous pass。** 從不觸發的 antecedent 什麼都沒驗證。請 cover antecedent，並留意計數是否為零。
- **運算子強度不符。** 太強讓合法情形失敗；太弱掩蓋真實的遺漏。請對齊契約。
- **單體式 assertion。** 難除錯，失敗時又不透明。請拆成小而具名的檢查。

## 小結

- 失敗的 assertion 回報的是違反週期；成因在更早開始的那次嘗試中，請回溯到 antecedent，讀完整個視窗。
- 反覆出現的反樣式包括：錯誤的 clock 或邊緣、缺少 `disable iff`、vacuity 掩蓋 bug、運算子強度不符、從不觸發的 antecedent，以及一條 assertion 做太多事。
- 良好實務：一條具名 assertion 一項意圖、clock 與 reset 只設一次、cover 每個 antecedent、運算子強度對齊契約、用區域變數捕捉資料，以及可重用的檢查用 bind 而非編輯進設計。
- 唯有當一條 assertion 的失敗讀得懂、通過又非空真時，它才值得信賴。

第三部到此結束。接下來的附錄收錄各項速查參考，首先是 Verilog 與 SystemVerilog 的對照。

---

[← checker 與 library](15-checkers-and-libraries.md) · [目錄](../README.md) · [下一章：附錄 A — Verilog 與 SystemVerilog 對照 →](../appendices/A-verilog-vs-sv.md)
