# 第三部 · 13. 覆蓋率與空真（vacuity）

[← 遞迴性質](12-recursive-properties.md) · [目錄](../README.md) · [下一章：形式化驗證入門 →](14-formal-verification-primer.md)

## 學習目標

- 使用 `cover property` 與 `cover sequence` 來度量某行為是否發生。
- 將設計意圖轉化為來自斷言的功能覆蓋（functional coverage）。
- 理解**空真**（vacuity / 空泛成立）以及空真通過為何可能掩蓋 bug。
- 確認蘊涵（implication）的前提（antecedent）確實觸發。
- 建立斷言驗證收斂的框架：每個檢查都被執行、每個觸發都被見到。

## Cover：它真的發生了嗎？

`assert` 證明某行為是*正確的*。`cover`（覆蓋）證明某行為*曾經*發生。兩者互補：一條從不失敗的斷言，若它所守護的情境從未出現，就什麼都告訴不了你。`cover` 透過回報某序列或性質匹配了幾次來彌補這道缺口。

```systemverilog
// Count how often a back-to-back write burst occurs
cover property (@(posedge clk) wr_en ##1 wr_en ##1 wr_en);
```

當這段執行時，工具回報匹配次數。零次匹配是個警訊：刺激（stimulus）從未產生該情境，因此任何關於它的斷言其實從未真正被測試。

## cover property 與 cover sequence

兩種形式都度量發生次數；差別在於它們接受什麼、回報什麼。

- **`cover sequence`** 接受一個序列，並回報每次匹配，包括重疊或多條執行緒的每次匹配。它是「計數此時序樣式出現次數」的精準工具。
- **`cover property`** 接受一個性質。對單純序列而言，其行為如同序列覆蓋；對蘊涵而言，它回報的是該蘊涵*被評估*的覆蓋，這通常不是你度量某情境時想要的。

```systemverilog
// Sequence coverage: every occurrence of the three-cycle pattern
cover sequence (@(posedge clk) req ##1 stall ##1 ack);

// Property coverage of a simple scenario
cover property (@(posedge clk) $rose(start) ##[1:4] done);
```

對於功能情境覆蓋，請將情境寫成序列並覆蓋該序列（或非蘊涵的性質）。將蘊涵形狀的覆蓋保留給對蘊涵本身的刻意分析。

## 由意圖而來的功能覆蓋

驅動斷言的同一份設計意圖，也驅動覆蓋。對每一條「這必須成立」的斷言，請問「那觸發情境發生了嗎？」——並覆蓋它。一小組覆蓋便記錄了測試實際執行了哪些角落：

```systemverilog
// Intent: the FIFO is exercised at both extremes
cover property (@(posedge clk) full);    // did we ever fill it?
cover property (@(posedge clk) empty);   // did we ever drain it?

// Intent: a write and read collide on the same cycle
cover property (@(posedge clk) wr_en && rd_en);
```

由意圖撰寫的覆蓋回答了斷言本身無法回答的問題：*意圖曾經被付諸測試嗎？* 它們把「沒有失敗」變成「沒有失敗，而且這是我們執行過的部分」。

## 空真

回顧第 7 章：當蘊涵的前提從未匹配時，它**空泛地**（vacuously）通過：沒有義務，因此性質被瑣碎地滿足。空真通過在邏輯上是正確的，但它也是*空的*——它對後件什麼都沒證明。

```systemverilog
// If 'req' never rises, this passes every cycle without ever checking 'gnt'
assert property (@(posedge clk) $rose(req) |=> gnt);
```

危險是無聲的：報告顯示一條通過的斷言，工程師把「通過」讀成「已驗證」，而後件從未被執行。grant 邏輯中的真實 bug 永遠不會被抓到，因為 grant 邏輯從未被觸及。空真，就是綠燈報告如何掩蓋一條未測路徑的方式。

## 確認前提觸發

補救之道是以對前提的 `cover` 驗證前提確實發生。將每條蘊涵與其觸發的覆蓋配對，是一項標準的紀律：

```systemverilog
assert property (@(posedge clk) $rose(req) |=> gnt);
cover  property (@(posedge clk) $rose(req));   // proves the trigger was real
```

現在報告攜帶兩項事實：grant 規則成立（assert），*且*確實有一個請求發生來測試它（cover）。若覆蓋計數為零，那條通過的 assert 就是空真的，不可信賴。許多工具也會直接標示空真通過；請把這類標示當作「尚未驗證」，而非「已驗證」。

> **設計意圖。** 斷言與覆蓋陳述了「已驗證」的兩個半邊。斷言捕捉*什麼必須為真*；覆蓋捕捉*那情境確實被觸及*。空真就是兩者之間的缺口——一個檢查可能僅僅因為觸發從未發生而通過。覆蓋前提便彌合了這道缺口，使一份通過的報告意味著「正確*且*被執行」，這正是設計者真正想知道的。

## 斷言驗證收斂

一組斷言的收斂（closure）意味著兩個條件同時成立：

1. **沒有斷言失敗。** 每項陳述的義務在每次嘗試上都被滿足。
2. **沒有斷言僅以空真通過。** 每個前提都被覆蓋——每個觸發情境至少被觸及一次。

一套通過卻不滿足第二個條件的測試並未收斂；它是偽裝過的未測。因此務實的收斂會在斷言結果之外一併追蹤覆蓋計數，並把未覆蓋的前提視同缺失的測試。形式化工具以空真分析使此事顯式化；在模擬中，「覆蓋前提」這項紀律提供同樣的效果。

## 常見陷阱

- **把「通過」讀成「已驗證」。** 通過可能是空真的。若沒有對前提的覆蓋，一條綠燈斷言可能什麼都沒檢查。
- **從不查看覆蓋計數。** 匹配零次的覆蓋意味著該情境從未發生；相關的斷言並未被執行。
- **為計數情境而覆蓋蘊涵。** 當你的意思是「計數出現次數」時，請覆蓋*序列*（或非蘊涵的性質）；蘊涵覆蓋度量的是別的東西。
- **忽略工具的空真標示。** 空真警告標記了一項未測的義務。請把它當作未完成，而非雜訊。
- **止步於「所有斷言通過」。** 收斂還要求每個前提都被覆蓋。請同時追蹤兩者。

## 小結

- `cover` 度量某行為是否發生；`assert` 證明它是否正確——兩者互補。
- 使用 `cover sequence`（或非蘊涵的 `cover property`）來計數某時序情境的出現次數。
- 空真通過發生於前提從未匹配時；它什麼都沒證明，且可能在綠燈報告背後掩蓋 bug。
- 覆蓋每條蘊涵的前提以確認觸發為真；計數為零意味著該斷言從未被真正測試。
- 驗證收斂要求沒有失敗*且*沒有純粹的空真通過——每項義務被滿足、每個觸發被執行。

---

[← 遞迴性質](12-recursive-properties.md) · [目錄](../README.md) · [下一章：形式化驗證入門 →](14-formal-verification-primer.md)
