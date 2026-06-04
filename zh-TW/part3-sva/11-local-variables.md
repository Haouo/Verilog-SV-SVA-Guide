# 第三部 · 11. 區域變數

[← RTL assertion pattern](10-rtl-assertion-patterns.md) · [目錄](../README.md) · [下一章：recursive property →](12-recursive-properties.md)

## 學習目標

- 在 sequence 或 property 內宣告**區域變數**（local variable）。
- 在 sequence 匹配時對它指定，並在稍後讀取。
- 用區域變數跨週期檢查管線化（pipelined）的資料。
- 理解每次嘗試（attempt）各自的作用域，以及區域變數值的流動方式。
- 避開那些讓區域變數行為出人意料的取樣與流動陷阱。

## 設計者的心智模型

區域變數讓一條 assertion 記住與某一次嘗試（attempt）相關的值。這正是「攜帶資料的意圖」的關鍵：它要表達的不只是「發生了某個回應」，而是「這個請求的回應，必須與這個請求開始時取樣到的資料相符」。每一個並行的嘗試，都有自己一份變數儲存空間。

這讓區域變數既強大，也容易被誤解。指定發生在取樣後的 assertion 世界裡，並不是一次 RTL 的程序式更新。當一條 property 有重疊的嘗試時，請把每個嘗試分開來畫，追蹤哪一個取樣值屬於哪一個 consequent。

## 區域變數為何存在

implication 將觸發與回應關聯起來，但回應往往必須*對照在觸發時捕捉的值*來檢查。一次讀取要回傳當初寫入的資料；一個回應要帶有其請求的標籤。單純的布林 property 無法跨週期記住所捕捉的值。**區域變數**可以：它是某一次 assertion 評估嘗試所私有的儲存空間，在某個 sequence 元素匹配時寫入，並在稍後的元素中讀取。

```systemverilog
// Capture the address at request, check the response uses the same one
property addr_matches;
    logic [7:0] a;
    (req, a = addr) |=> ##[1:3] (resp && rsp_addr == a);
endproperty
assert property (addr_matches);
```

宣告 `logic [7:0] a;` 引入了區域變數。動作區塊 `(req, a = addr)` 表示：當 `req` 匹配時，將 `addr` 指定給 `a`。後面的項讀取 `a`，將它與回應的位址比較。每次嘗試各有自己的 `a`，因此重疊的請求不會互相覆寫。

## sequence 中的指定

區域變數的指定寫在括號內、以逗號接在布林條件之後，和布林匹配同時發生：

```systemverilog
// On the matching cycle, also perform the assignment
(boolean_expr, var = expr)
```

指定發生在*該布林匹配時*，使用該週期的 sampled value。可串接多個指定：

```systemverilog
(start, cnt = 0, base = addr)
```

指定也可以在 sequence 推進的過程中更新區域變數，例如在重複（repetition）的每次迭代上把一個計數器加一。沿著匹配執行緒（thread）往前傳的值，永遠是該執行緒上最近一次的指定。

## sampling：區域變數使用 sampled value

區域變數的指定捕捉的是其右側的**取樣值（sampled value）**，也就是 Preponed 區域中的值，與 assertion 其餘部分所見的是同一個值（第 2 章）。它不會捕捉週期中途或帶毛刺的值。正是這一點，讓所捕捉的資料能與設計自身的取樣逐週期對齊。

```systemverilog
// 'a' holds the value of addr as sampled on the req cycle,
// not whatever addr becomes later
(req, a = addr) |=> ... (rsp_addr == a)
```

由於捕捉的是取樣值，稍後拿它去和另一個取樣值比較，就是同類對同類的比較，這正是管線化檢查所需要的語意。

## 管線化的資料檢查

區域變數的招牌用途，是驗證一條管線：在某一級進入的資料，必須在固定週期數之後，依規格轉換後浮現。

```systemverilog
// A 3-stage pipe: output equals input + 1, three cycles later
property pipe_add1;
    logic [15:0] d;
    (in_valid, d = in_data) |-> ##3 (out_valid && out_data == d + 1);
endproperty
assert property (pipe_add1);
```

區域變數 `d` 對輸入拍下快照，assertion 等待管線深度，接著將輸出對照已捕捉、已轉換的值來檢查。當資料每週期重疊地流入時，每次嘗試各帶有*自己*的 `d`，因此即使許多筆資料同時在管線中飛行，檢查仍能正確追蹤每一筆穿過管線。

> **設計意圖。** 區域變數讓一條 assertion 能說「*這個*輸出必須對應*那個*輸入」：把回應綁定到觸發它的那個特定值，而不只是綁定到「發生了某個回應」。設計者就是這樣陳述一條資料路徑契約的：進去的那個數，就是（經適當轉換後）出來的那個數，每一次，穿過每一級都成立。

## 每次嘗試的作用域與流動

由「某一次嘗試所私有」可推出區域變數的兩個 property：

- **獨立的副本。** assertion 的每一次起始都取得一組全新的區域變數。並行、重疊的嘗試從不共用儲存空間，因此同時在飛行的多筆交易各自被分開追蹤。
- **沿匹配流動。** 區域變數的值只沿著*匹配中*的執行緒往前流動。若 sequence 分岔（例如遇到 `or` 或有界重複），每條分支各帶自己的副本，且在某分支上指定的值不會在另一分支上可見。

正是這套流動模型，使區域變數能與 sequence operator 乾淨地組合：值隨著實際匹配的執行緒移動，並在該執行緒失敗時消失。

```systemverilog
// Count consecutive 'beat's and require exactly LEN of them before 'last'
property burst_len;
    int n;
    ($rose(start), n = 0)
    ##1 (beat, n = n + 1)[*1:$] ##0 last
    |-> (n == LEN);
endproperty
assert property (burst_len);
```

此處 `n` 沿匹配執行緒在重複中累加，最終的檢查讀取累加的計數。每筆由各自嘗試追蹤的 burst 各有自己的 `n`。

## 在指定前讀取區域變數

在一條從未指定過該變數的執行緒上讀取區域變數，對這條執行緒來說它的值是未定義的，檢查也就失去意義。請務必在每一條稍後會讀取它的路徑上先指定區域變數，通常就放在 antecedent 的觸發處，這樣每條存活下來的執行緒都帶有一個已定義的值。

## 常見陷阱

- **指定前讀取。** 在當前執行緒上未指定的區域變數沒有有意義的值。請在觸發處指定它，使每條存活執行緒都有它。
- **期望單一共用變數。** 每次嘗試各有自己的副本；你無法用區域變數在*不同*嘗試*之間*傳遞狀態。那需要用設計狀態或另一套機制。
- **忘記值是取樣得來的。** 所捕捉的是 Preponed 區域的取樣值，而非即時或帶毛刺的值。這對逐週期對齊的檢查是正確的，卻會讓期待阻塞式指定那種時序的人感到意外。
- **在不匹配的分支上指定。** 在失敗分支上指定的值不會向前流動。請把指定放在必須承載它的執行緒上。
- **把 antecedent 弄得過於複雜。** 在單一條 assertion 裡做太深的區域變數記帳，會很難閱讀也很難除錯。請選用能表達該資料綁定關係的最簡捕捉方式。

## 小結

- 區域變數是某一次 assertion 嘗試所私有的儲存空間，在匹配時寫入、稍後讀取。
- 以 `(boolean, var = expr)` 形式指定；所捕捉的是取樣（Preponed）值。
- 區域變數是管線化資料檢查的工具：對輸入拍快照，等待管線深度，再將輸出對照所捕捉的值比較。
- 每次嘗試各有獨立副本，且值只沿匹配執行緒流動，因此重疊的交易各自被追蹤。
- 在某執行緒上務必先指定再讀取，否則值未定義。

---

[← RTL assertion pattern](10-rtl-assertion-patterns.md) · [目錄](../README.md) · [下一章：recursive property →](12-recursive-properties.md)
