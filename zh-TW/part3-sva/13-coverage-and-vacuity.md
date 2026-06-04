# 第三部 · 13. coverage 與 vacuity

[← recursive property](12-recursive-properties.md) · [目錄](../README.md) · [下一章：formal verification 入門 →](14-formal-verification-primer.md)

## 學習目標

- 使用 `cover property` 與 `cover sequence` 來度量某行為是否發生。
- 將設計意圖轉化為來自 assertion 的功能 cover（functional coverage）。
- 理解**vacuity**（vacuity / vacuous pass）以及 vacuous pass 為何可能掩蓋 bug。
- 確認 implication 的 antecedent 確實觸發。
- 建立 assertion 驗證收斂的框架：每個檢查都被執行、每個觸發都被見到。

## 設計者的心智模型

一條通過的 assertion 只回答一個問題：觀察到的嘗試沒有違反這條規則。它不能證明真正關鍵的那次嘗試曾經發生。coverage 與 vacuity 檢查回答的正是這個缺漏的問題：觸發條件有沒有出現？視窗有沒有打開？設計有沒有真的執行到 assertion 想保護的那段行為？

對每條重要的 implication，都該問：什麼證據能讓你相信這個檢查是有意義的？這份證據通常就是放在 antecedent 上的 `cover property`，或某個相關情境的 cover。assertion 收斂不只是看到綠燈，還要確認這些檢查確實被執行過。

## Cover：它真的發生了嗎？

`assert` 證明某行為是*正確的*。`cover`（覆蓋）證明某行為*曾經*發生。兩者互補：一條從不失敗的 assertion，若它所守護的情境從未出現，就什麼都告訴不了你。`cover` 會回報某 sequence 或 property 匹配了幾次，補上這道缺口。

```systemverilog
// Count how often a back-to-back write burst occurs
cover property (@(posedge clk) wr_en ##1 wr_en ##1 wr_en);
```

這段執行時，工具會回報匹配次數。零次匹配是個警訊：刺激（stimulus）從未產生該情境，因此任何針對它的 assertion 其實都不曾真正受測。

## cover property 與 cover sequence

兩種形式都度量發生次數；差別在於它們接受什麼、回報什麼。

- **`cover sequence`** 接受一個 sequence，並回報每次匹配，包括重疊或多條執行緒的每次匹配。它是「計數此時序樣式出現次數」的精準工具。
- **`cover property`** 接受一個 property。對單純 sequence 而言，其行為等同於 sequence cover；對 implication 而言，它回報的是該 implication*被評估*的次數，這通常不是你度量某情境時想要的。

```systemverilog
// Sequence coverage: every occurrence of the three-cycle pattern
cover sequence (@(posedge clk) req ##1 stall ##1 ack);

// Property coverage of a simple scenario
cover property (@(posedge clk) $rose(start) ##[1:4] done);
```

對於功能情境 cover，請將情境寫成 sequence 並 cover 該 sequence（或非 implication 的 property）。將 implication 形狀的 cover 保留給對 implication 本身的刻意分析。

## 由意圖而來的功能 cover

驅動 assertion 的同一份設計意圖，也驅動 cover。對每一條「這必須成立」的 assertion，都該問一句「那個觸發情境發生了嗎？」，然後 cover 它。一小組 cover 就記錄下測試實際執行到了哪些角落：

```systemverilog
// Intent: the FIFO is exercised at both extremes
cover property (@(posedge clk) full);    // did we ever fill it?
cover property (@(posedge clk) empty);   // did we ever drain it?

// Intent: a write and read collide on the same cycle
cover property (@(posedge clk) wr_en && rd_en);
```

由意圖寫成的 cover 回答了 assertion 本身無法回答的問題：*意圖曾經被付諸測試嗎？* 它們把「沒有失敗」變成「沒有失敗，而且這就是我們執行過的部分」。

## vacuity

回顧第 7 章：當 implication 的 antecedent 從未匹配時，它會**空真地**（vacuously）通過，因為沒有任何義務需要滿足，property 也就被瑣碎地滿足了。vacuous pass 在邏輯上正確，卻也是*空的*,它對 consequent 什麼都沒證明。

```systemverilog
// If 'req' never rises, this passes every cycle without ever checking 'gnt'
assert property (@(posedge clk) $rose(req) |=> gnt);
```

危險之處在於它無聲無息：報告顯示一條通過的 assertion，工程師把「通過」讀成「已驗證」，而 consequent 從未被執行。grant 邏輯裡的真實 bug 永遠不會被抓到，因為根本沒走到 grant 邏輯。綠燈報告之所以能掩蓋一條未測路徑，靠的就是 vacuity。

## 確認 antecedent 觸發

補救之道是以對 antecedent 的 `cover` 驗證 antecedent 確實發生。將每條 implication 與其觸發的 cover 配對，是一項標準的紀律：

```systemverilog
assert property (@(posedge clk) $rose(req) |=> gnt);
cover  property (@(posedge clk) $rose(req));   // proves the trigger was real
```

這時報告就帶有兩項事實：grant 規則成立（assert），*而且*確實有一個請求發生來測試它（cover）。若 cover 計數為零，那條通過的 assert 就是空真的，不可信賴。許多工具也會直接標示 vacuous pass；請把這類標示當作「尚未驗證」，而非「已驗證」。

> **設計意圖。** assertion 與 cover 各說出「已驗證」的一半。assertion 捕捉*什麼必須為真*；cover 捕捉*那個情境確實被觸及*。vacuity 就是兩者之間的缺口，一個檢查可能僅僅因為觸發從未發生而通過。cover 住 antecedent 就補上了這道缺口，讓一份通過的報告代表「正確*而且*被執行過」，這正是設計者真正想知道的。

## assertion 驗證收斂

一組 assertion 要算收斂（closure），得同時滿足兩個條件：

1. **沒有 assertion 失敗。** 每項宣告的義務在每次嘗試上都被滿足。
2. **沒有 assertion 只靠 vacuous pass 通過。** 每個 antecedent 都被 cover 過，每個觸發情境至少被觸及一次。

一套通過卻不滿足第二個條件的測試並未收斂，它只是偽裝過的未測。因此務實的收斂會在 assertion 結果之外一併追蹤 cover 計數，並把未 cover 的 antecedent 當成缺失的測試。formal 工具用 vacuity 分析把這件事攤開來；在 simulation 裡，「cover 住 antecedent」這項紀律提供同樣的效果。

## 常見陷阱

- **把「通過」讀成「已驗證」。** 通過可能是空真的。少了 antecedent 上的 cover，一條綠燈 assertion 可能什麼都沒檢查。
- **從不查看 cover 計數。** 匹配零次的 cover 代表該情境從未發生，相關的 assertion 並未被執行。
- **為了計數情境而 cover implication。** 當你想說的是「計數出現次數」時，請 cover *sequence*（或非 implication 的 property）；implication cover 量的是別的東西。
- **忽略工具的 vacuity 標示。** vacuity 警告標出了一項未測的義務。請把它當成未完成，而非雜訊。
- **停在「所有 assertion 通過」就滿足。** 收斂還要求每個 antecedent 都被 cover。兩者都要追蹤。

## 小結

- `cover` 度量某行為是否發生；`assert` 證明它是否正確，兩者互補。
- 用 `cover sequence`（或非 implication 的 `cover property`）來計數某時序情境的出現次數。
- 當 antecedent 從未匹配時就會出現 vacuous pass；它什麼都沒證明，還可能在綠燈報告背後掩蓋 bug。
- cover 每條 implication 的 antecedent，確認觸發是真的；計數為零代表該 assertion 從未被真正測試。
- 驗證收斂要求沒有失敗*而且*沒有純粹的 vacuous pass,每項義務都被滿足、每個觸發都被執行。

---

[← recursive property](12-recursive-properties.md) · [目錄](../README.md) · [下一章：formal verification 入門 →](14-formal-verification-primer.md)
