# 第三部 · 16. 除錯與反樣式

[← checker 與 library](15-checkers-and-libraries.md) · [目錄](../README.md) · [下一章：附錄 A — Verilog 與 SystemVerilog 對照 →](../appendices/A-verilog-vs-sv.md)

## 學習目標

- 解讀失敗的 assertion：找出嘗試（attempt）的起點，而非僅是失敗週期。
- 將失敗回溯穿過 antecedent，找到該負責的週期。
- 辨識常見的 SVA 錯誤，以及它們背後的反樣式。
- 套用使 assertion 保持可信的良好實務準則。

這是第三部的結尾章節。它假設此前的一切——sampling（第 2 章）、implication 與 vacuity（第 7、13 章）、clock 與 reset（第 8 章），以及第 10 章的各種樣式——並轉向探討出了什麼錯、又該如何修正。

## 設計者 mental model

failed assertion 是 debugging instrument。它應該告訴你哪個 intent 被 violated、violating attempt
何時開始、以及什麼 evidence 讓 consequent fail。如果 property 太大、clock edge 錯、或允許 vacuous
pass，它就不再提供線索，而會變成干擾訊息。

debug SVA 因此同時是在 debug design，也是在 debug specification。assertion fail 時兩邊都要檢查：
RTL 可能錯，property 也可能 encode 了錯的 rule。anti-pattern list 的價值，就是幫你快速辨認第二種情況。

## 解讀失敗的 assertion

當一條 concurrent assertion 失敗時，工具回報義務被違反的週期。那個週期是故事的*終點*，而非起點。property 每當其 antecedent 可能匹配時，便開啟一次新的**嘗試**；你所見的失敗，屬於某次在數個週期前開始的特定嘗試。除錯就是找出*那次*嘗試的起點。

```systemverilog
// Reported failure is at the cycle gnt should be high but isn't;
// the attempt started 1..N cycles earlier, when req rose
assert property ($rose(req) |-> ##[1:N] gnt);
```

步驟如下：

1. **記下工具回報的失敗週期**——consequent（consequent）的期限。
2. **回溯到開啟此次嘗試的 antecedent 匹配。** 對 `$rose(req) |-> ##[1:N] gnt` 而言，那是最近 *N* 個週期內的 `$rose(req)` 週期。
3. **檢視兩者之間的視窗。** bug 就是在那段跨距上使 consequent 未能達成其義務的原因——遺失的 `gnt`、被丟棄的請求，或視窗中途出錯的某個狀態。

多數 assertion 除錯器會在波形上畫出這段嘗試跨距，標示起點、各步驟，以及失敗週期。請閱讀整段跨距，而非那個單一的紅色標記：成因幾乎總在失敗被標示之處的上游。

## 回溯穿過 antecedent

一種微妙的失敗，是*antecedent*本身才是真正的 bug。若 assertion「出乎意料地」失敗，請檢查 antecedent 是否在不該匹配時匹配了：

```systemverilog
// If this fails, ask first: did 'start' really rise here,
// or is the antecedent firing on a glitch the design didn't intend?
assert property ($rose(start) |=> busy);
```

一次失敗可能意味著 consequent 錯了，*也可能*意味著 antecedent 在設計者從未打算約束的情境中觸發。閱讀嘗試起點處 antecedent 的 sampled value 便能區辨兩者：真實的觸發配上壞掉的回應，是設計 bug；虛假的觸發，則是一條太過寬泛的 assertion。

## 常見錯誤與反樣式

### 錯誤的 clock 或錯誤的邊緣

在不符合邏輯的 clock 或邊緣上 sampling，會產生看似隨機的失敗，因為 assertion 看到的值偏了半個週期（第 8 章）。

```systemverilog
// ANTI-PATTERN: design captures on posedge, assertion samples negedge
assert property (@(negedge clk) load |=> q == $past(d));
// FIX: match the capture edge
assert property (@(posedge clk) load |=> q == $past(d));
```

### 缺少 disable iff

沒有 reset 防護的 assertion，會在未知的啟動視窗期間觸發，回報的失敗其實只是 reset 行為。

```systemverilog
// ANTI-PATTERN: no reset guard — fires during reset
assert property (@(posedge clk) req |=> gnt);
// FIX: disable during reset
assert property (@(posedge clk) disable iff (!rst_n) req |=> gnt);
```

### vacuity 掩蓋 bug

antecedent 從不觸發的 implication 會 vacuous pass，什麼都不驗證（第 13 章）。綠燈報告於是掩蓋了一條未測路徑。

```systemverilog
// ANTI-PATTERN: trusting this pass without checking the trigger ever occurred
assert property (mode_x && start |=> done);
// FIX: cover the antecedent so a zero count exposes the vacuity
cover property (mode_x && start);
```

### 運算子太強或太弱

在事件並無保證之處使用強運算子，會把一個合法情形變成失敗；在事件*確有*保證之處使用弱運算子，則讓一次真實的遺漏無聲通過（第 7 章）。

```systemverilog
// Too strong: forces ack to occur even when the protocol allows abort
assert property ($rose(req) |-> req s_until ack);
// Right strength when ack may legitimately never come:
assert property ($rose(req) |-> req until ack);
```

對盡力而為（best-effort）的條件選用弱形式，唯有當解除事件由契約保證時才用強形式。

### 從不觸發的 antecedent

過於特定的 antecedent——太多合取項，或一個不可能的組合——從不匹配，於是 assertion 永久 vacuity。cover 計數為零便是徵兆（第 13 章）。請簡化 antecedent，直到它捕捉到真實的觸發。

### 一條 assertion 做太多事

把多項義務、區域變數記帳與巢狀運算子塞進單一 property，難讀、難除錯，且失敗時不說明*哪一*部分壞了。

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

數條小而具名的 assertion 各自精確指出自己的失敗，且各記錄一項意圖。請偏好它們勝過單一龐然大物。

## 良好實務準則

- **一條 assertion 一項意圖。** 小而具名的檢查能隔離失敗，並讀來如同文件。為它們命名，使報告指向意圖。
- **clock 與 reset 只設一次。** 使用 `default clocking` 與 `default disable iff`，使沒有 assertion 漂移到錯誤的邊緣或在 reset 期間觸發（第 8 章）。
- **cover 每個 antecedent。** 將每條 implication 與其觸發的 cover 配對，使 vacuity 無法躲在綠燈報告之後（第 13 章）。
- **使運算子強度符合契約。** 唯有事件有保證時才用強形式；盡力而為的條件用弱形式。
- **以區域變數捕捉資料，而非臨時邏輯。** 對管線化檢查，區域變數能乾淨地將回應 bind 到其特定觸發（第 11 章）。
- **bind 獨立的 assertion；保持 RTL 乾淨。** 可重用的檢查住在 checker 與被 bind 的模組中，而非被編輯進設計（第 9、15 章）。
- **閱讀嘗試跨距，而非標記。** 失敗時，回溯到 antecedent 起點並檢視整個視窗。

> **設計意圖。** 一條 assertion 唯有在可除錯且誠實時才值得信賴。一次失敗應清楚指向一項壞掉的意圖；一次通過應意味著意圖確實被執行。這些反樣式全都模糊了其中之一：錯誤的 clock 使失敗說謊，vacuity 使通過說謊，而過載的 property 使失敗無法閱讀。良好實務讓每條 assertion 保持為一個小巧、帶 clock、被 cover、單一的意圖陳述——如此當它發聲時，設計者便能相信它。

## 常見陷阱

- **僅從失敗週期除錯。** 成因在更早開始的嘗試視窗中。請回溯到 antecedent。
- **錯誤的 clock 或邊緣。** 產生看似隨機的失敗。請符合設計的擷取邊緣。
- **缺少 `disable iff`。** reset 期間的活動被回報為失敗。請以 `disable iff` 或 `default disable iff` 防護。
- **信賴 vacuous pass。** 從不觸發的 antecedent 什麼都不驗證。請 cover antecedent 並留意計數為零。
- **運算子強度不符。** 太強使合法情形失敗；太弱掩蓋真實遺漏。請符合契約。
- **單體式 assertion。** 難除錯且失敗時不透明。請拆成小而具名的檢查。

## 小結

- 失敗的 assertion 回報違反週期；成因在更早開始的嘗試中——請回溯到 antecedent 並閱讀整個視窗。
- 反覆出現的反樣式包括：錯誤的 clock 或邊緣、缺少 `disable iff`、vacuity 掩蓋 bug、運算子強度不符、從不觸發的 antecedent，以及一條 assertion 做太多事。
- 良好實務：一條具名 assertion 一項意圖、clock 與 reset 只設一次、cover 每個 antecedent、運算子強度符合契約、以區域變數捕捉資料，以及可重用檢查用 bind 而非編輯進設計。
- 唯有當 assertion 的失敗可閱讀、且其通過非 vacuity 時，它才值得信賴。

至此第三部結束。接下來的附錄收錄各項速查參考——首先是 Verilog 與 SystemVerilog 的對照。

---

[← checker 與 library](15-checkers-and-libraries.md) · [目錄](../README.md) · [下一章：附錄 A — Verilog 與 SystemVerilog 對照 →](../appendices/A-verilog-vs-sv.md)
