# 第三部 · 12. recursive property

[← 區域變數](11-local-variables.md) · [目錄](../README.md) · [下一章：coverage 與 vacuity →](13-coverage-and-vacuity.md)

## 學習目標

- 定義一個會引用自身的**遞迴性質（recursive property）**。
- 緊湊地陳述一個無界的時序需求。
- 套用那些讓 recursive property 保持良構（well-formed）的規則。
- 辨識在什麼情況下，遞迴會比一長串運算子更清楚地表達意圖。

## 設計者的心智模型

recursive property 描述的是一種會重複自身形態的意圖。大多數 RTL 檢查並不需要它，但對於無界或歸納式的行為，它往往比一長串固定延遲更自然。即便如此，設計者仍必須提供清楚的退出條件，否則整個遞迴會變得無從推理。

只有當協定本身就是自相似的時候，才考慮動用遞迴：持續套用這條規則直到某個終止事件、不斷接受同一種形式的進展，或是以歸納法證明某個結構。如果一個有界視窗就已經足夠，通常一條單純的 sequence 反而更清楚。

## 什麼是 recursive property

一個具名的 property 可以在自己的本體中提及自己。每一次引用，都把同一個 property 往後套用一個週期，於是一個有限的定義就能描述一項延伸到無界時間的義務。這就是 recursive property。

最典型的例子是「觸發後永遠保持」。若無遞迴，你會需要一個無界運算子；有了遞迴，定義便是一行，每週期重新喚起自己：

```systemverilog
// Once 'lock' is set, 'busy' must stay high for every following cycle
property stays_busy;
    busy and nexttime stays_busy;
endproperty

assert property ($rose(lock) |-> stays_busy);
```

把 `stays_busy` 讀作：「`busy` 現在成立，*而且* `stays_busy` 從下一週期起也成立。」把它展開，就會得到永無止境的 `busy ##1 busy ##1 busy ...`，這是陳述一個須無限期持續的不變式的緊湊寫法。

## 帶出口的遞迴

永不停止的遞迴陳述的是純粹的「永遠」需求。更常見的是該義務持續*直到*某條件解除為止。`if/else`（或 implication）為遞迴提供一個基底情形（base case）：

```systemverilog
// After 'grant', 'hold' must remain high every cycle until 'done',
// and 'done' ends the obligation
property hold_until_done;
    hold and (done or nexttime hold_until_done);
endproperty

assert property ($rose(grant) |-> hold_until_done);
```

每個週期該 property 都要求 `hold`，接著要嘛 `done` 抵達（遞迴停止，獲得滿足），要嘛該 property 於下一週期重新套用。當每週期的義務不只是單純的布林時，遞迴形式能將「每週期直到解除」的意圖明確化，這是單一運算子有時做不到的。

## 良構遞迴的規則

SVA 中的遞迴受到限制，以使每個實例可判定（decidable）。關鍵規則：

- **隨時間推進。** 遞迴實例只能在一個正向時間步之後才被觸及，也就是要擺在 `nexttime`、`##1` 或等效的延遲之後。一個在*同一*週期就重新喚起自己的 property，在時間上沒有立足點，是不合法的。
- **遞迴周圍不得有否定。** recursive property 不得出現在 `not` 之下，不得位於 implication 的左側，也不得出現在任何其真值必須以「否定」方式得知之處。遞迴只允許在正向位置（positive position）。
- **允許相互遞迴**，但受同樣的約束：兩個 property 可以各自引用對方，前提是這個迴圈的每一個週期都推進時間，並且保持在正向位置。
- **沒有區域變數的危害。** recursive property 一般不得以需要無界個相異儲存空間的方式讓區域變數穿過遞迴；請將每週期的狀態保留在設計中，或以有界形式呈現。

這些規則保證遞迴要嘛在基底情形終止，要嘛每週期都有確定的進展，使工具能評估它。

## 何時動用遞迴

多數日常檢查不需遞迴：有界視窗（`##[1:N]`）、`until` 與 `throughout` 已涵蓋常見情形且讀來清楚。遞迴在以下情況才值得使用：

- 每週期的義務是比單一布林更豐富的 property，使單純的 `until` 無法承載；或
- 該需求確實無界，而你希望將它陳述為一條自相似（self-similar）的規則，而非強時序運算子；或
- 結構天生具歸納性，例如某協定其每一步都對其餘部分施加同樣的形態。

```systemverilog
// Each transfer in a burst must look the same as the burst contract,
// applied to the remaining beats
property beat_then_rest;
    beat_ok and (last or nexttime beat_then_rest);
endproperty

assert property (burst_start |-> beat_then_rest);
```

> **設計意圖。** recursive property 陳述的是一項*在時間上自相似*的意圖：「這條規則現在成立，而同樣的規則對接下來的部分也成立。」它讓設計者能把一個無界或歸納的需求，寫成一條清楚而有限的定義，而不是一串笨拙的運算子。只要審慎使用，它就能恰如協定本意地捕捉「持續這樣行為，直到被解除為止」。

## 常見陷阱

- **零延遲遞迴。** 沒有時間步的自我引用不合法，且沒有時間上的基底。請務必用 `nexttime` 或 `##1` 推進時間。
- **否定之下的遞迴。** 將 recursive property 置於 `not` 之下或 antecedent 側會違反正向性規則。請讓遞迴保持在正向位置。
- **忘記基底情形。** 沒有出口的遞迴陳述的是嚴格的「永遠」規則。若義務應結束，請加上解除條件（`done`、`last`）。
- **在有界運算子適用處使用遞迴。** 對於固定視窗或單純的「保持直到」，`##[1:N]`、`until` 或 `throughout` 更清楚。請將遞迴保留給無界或歸納的意圖。

## 小結

- recursive property 引用自身、往後套用一個週期，以有限的定義描述一項無界或歸納的義務。
- 每個週期都必須推進時間並保持在正向位置；同週期或否定的遞迴不合法。
- `if/else` 或 implication 的基底情形讓義務能在解除條件處結束。
- 當每週期的義務比布林更豐富，或需求在時間上天然自相似時，才動用遞迴；否則偏好有界運算子。

---

[← 區域變數](11-local-variables.md) · [目錄](../README.md) · [下一章：coverage 與 vacuity →](13-coverage-and-vacuity.md)
