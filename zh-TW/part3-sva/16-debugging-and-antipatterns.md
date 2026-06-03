# 第三部 · 16. 除錯與反樣式

[← checker 與函式庫](15-checkers-and-libraries.md) · [目錄](../README.md) · [下一章：附錄 A — Verilog 與 SystemVerilog 對照 →](../appendices/A-verilog-vs-sv.md)

## 學習目標

- 解讀失敗的斷言：找出嘗試（attempt）的起點，而非僅是失敗週期。
- 將失敗回溯穿過前提（antecedent），找到該負責的週期。
- 辨識常見的 SVA 錯誤，以及它們背後的反樣式。
- 套用使斷言保持可信的良好實務準則。

這是第三部的結尾章節。它假設此前的一切——取樣（第 2 章）、蘊涵與空真（第 7、13 章）、時脈與重置（第 8 章），以及第 10 章的各種樣式——並轉向探討出了什麼錯、又該如何修正。

## 解讀失敗的斷言

當一條並行斷言失敗時，工具回報義務被違反的週期。那個週期是故事的*終點*，而非起點。性質每當其前提可能匹配時，便開啟一次新的**嘗試**；你所見的失敗，屬於某次在數個週期前開始的特定嘗試。除錯就是找出*那次*嘗試的起點。

```systemverilog
// Reported failure is at the cycle gnt should be high but isn't;
// the attempt started 1..N cycles earlier, when req rose
assert property ($rose(req) |-> ##[1:N] gnt);
```

步驟如下：

1. **記下工具回報的失敗週期**——後件（consequent）的期限。
2. **回溯到開啟此次嘗試的前提匹配。** 對 `$rose(req) |-> ##[1:N] gnt` 而言，那是最近 *N* 個週期內的 `$rose(req)` 週期。
3. **檢視兩者之間的視窗。** bug 就是在那段跨距上使後件未能達成其義務的原因——遺失的 `gnt`、被丟棄的請求，或視窗中途出錯的某個狀態。

多數斷言除錯器會在波形上畫出這段嘗試跨距，標示起點、各步驟，以及失敗週期。請閱讀整段跨距，而非那個單一的紅色標記：成因幾乎總在失敗被標示之處的上游。

## 回溯穿過前提

一種微妙的失敗，是*前提*本身才是真正的 bug。若斷言「出乎意料地」失敗，請檢查前提是否在不該匹配時匹配了：

```systemverilog
// If this fails, ask first: did 'start' really rise here,
// or is the antecedent firing on a glitch the design didn't intend?
assert property ($rose(start) |=> busy);
```

一次失敗可能意味著後件錯了，*也可能*意味著前提在設計者從未打算約束的情境中觸發。閱讀嘗試起點處前提的取樣值便能區辨兩者：真實的觸發配上壞掉的回應，是設計 bug；虛假的觸發，則是一條太過寬泛的斷言。

## 常見錯誤與反樣式

### 錯誤的時脈或錯誤的邊緣

在不符合邏輯的時脈或邊緣上取樣，會產生看似隨機的失敗，因為斷言看到的值偏了半個週期（第 8 章）。

```systemverilog
// ANTI-PATTERN: design captures on posedge, assertion samples negedge
assert property (@(negedge clk) load |=> q == $past(d));
// FIX: match the capture edge
assert property (@(posedge clk) load |=> q == $past(d));
```

### 缺少 disable iff

沒有重置防護的斷言，會在未知的啟動視窗期間觸發，回報的失敗其實只是重置行為。

```systemverilog
// ANTI-PATTERN: no reset guard — fires during reset
assert property (@(posedge clk) req |=> gnt);
// FIX: disable during reset
assert property (@(posedge clk) disable iff (!rst_n) req |=> gnt);
```

### 空真掩蓋 bug

前提從不觸發的蘊涵會空真通過，什麼都不驗證（第 13 章）。綠燈報告於是掩蓋了一條未測路徑。

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

### 從不觸發的前提

過於特定的前提——太多合取項，或一個不可能的組合——從不匹配，於是斷言永久空真。覆蓋計數為零便是徵兆（第 13 章）。請簡化前提，直到它捕捉到真實的觸發。

### 一條斷言做太多事

把多項義務、區域變數記帳與巢狀運算子塞進單一性質，難讀、難除錯，且失敗時不說明*哪一*部分壞了。

```systemverilog
// ANTI-PATTERN: one giant property, opaque on failure
assert property (
    $rose(req) |-> (gnt && !err) ##1 (data_ok throughout (busy until done))
                   and ##[1:8] resp
);
// BETTER: split into focused, independently reported checks
a_gnt:  assert property ($rose(req) |-> gnt && !err);
a_data: assert property ($rose(req) ##1 busy |-> data_ok throughout (busy until done));
a_resp: assert property ($rose(req) |-> ##[1:8] resp);
```

數條小而具名的斷言各自精確指出自己的失敗，且各記錄一項意圖。請偏好它們勝過單一龐然大物。

## 良好實務準則

- **一條斷言一項意圖。** 小而具名的檢查能隔離失敗，並讀來如同文件。為它們命名，使報告指向意圖。
- **時脈與重置只設一次。** 使用 `default clocking` 與 `default disable iff`，使沒有斷言漂移到錯誤的邊緣或在重置期間觸發（第 8 章）。
- **覆蓋每個前提。** 將每條蘊涵與其觸發的覆蓋配對，使空真無法躲在綠燈報告之後（第 13 章）。
- **使運算子強度符合契約。** 唯有事件有保證時才用強形式；盡力而為的條件用弱形式。
- **以區域變數捕捉資料，而非臨時邏輯。** 對管線化檢查，區域變數能乾淨地將回應綁定到其特定觸發（第 11 章）。
- **綁定獨立的斷言；保持 RTL 乾淨。** 可重用的檢查住在 checker 與被綁定的模組中，而非被編輯進設計（第 9、15 章）。
- **閱讀嘗試跨距，而非標記。** 失敗時，回溯到前提起點並檢視整個視窗。

> **設計意圖。** 一條斷言唯有在可除錯且誠實時才值得信賴。一次失敗應清楚指向一項壞掉的意圖；一次通過應意味著意圖確實被執行。這些反樣式全都模糊了其中之一：錯誤的時脈使失敗說謊，空真使通過說謊，而過載的性質使失敗無法閱讀。良好實務讓每條斷言保持為一個小巧、帶時脈、被覆蓋、單一的意圖陳述——如此當它發聲時，設計者便能相信它。

## 常見陷阱

- **僅從失敗週期除錯。** 成因在更早開始的嘗試視窗中。請回溯到前提。
- **錯誤的時脈或邊緣。** 產生看似隨機的失敗。請符合設計的擷取邊緣。
- **缺少 `disable iff`。** 重置期間的活動被回報為失敗。請以 `disable iff` 或 `default disable iff` 防護。
- **信賴空真通過。** 從不觸發的前提什麼都不驗證。請覆蓋前提並留意計數為零。
- **運算子強度不符。** 太強使合法情形失敗；太弱掩蓋真實遺漏。請符合契約。
- **單體式斷言。** 難除錯且失敗時不透明。請拆成小而具名的檢查。

## 小結

- 失敗的斷言回報違反週期；成因在更早開始的嘗試中——請回溯到前提並閱讀整個視窗。
- 反覆出現的反樣式包括：錯誤的時脈或邊緣、缺少 `disable iff`、空真掩蓋 bug、運算子強度不符、從不觸發的前提，以及一條斷言做太多事。
- 良好實務：一條具名斷言一項意圖、時脈與重置只設一次、覆蓋每個前提、運算子強度符合契約、以區域變數捕捉資料，以及可重用檢查用綁定而非編輯進設計。
- 唯有當斷言的失敗可閱讀、且其通過非空真時，它才值得信賴。

至此第三部結束。接下來的附錄收錄各項速查參考——首先是 Verilog 與 SystemVerilog 的對照。

---

[← checker 與函式庫](15-checkers-and-libraries.md) · [目錄](../README.md) · [下一章：附錄 A — Verilog 與 SystemVerilog 對照 →](../appendices/A-verilog-vs-sv.md)
