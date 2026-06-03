# 第三部 · 12. 遞迴性質

[← 區域變數](11-local-variables.md) · [目錄](../README.md) · [下一章：覆蓋率與空真（vacuity） →](13-coverage-and-vacuity.md)

## 學習目標

- 定義引用自身的**遞迴性質**（recursive property）。
- 緊湊地陳述一個無界的時序需求。
- 套用使遞迴性質保持良構（well-formed）的規則。
- 辨識遞迴何時比冗長的運算子串鏈更清楚地表達意圖。

## 什麼是遞迴性質

具名性質可以在自己的本體中提及自己。每次引用都將同一性質往後套用一個週期，因此一個有限的定義便能描述一項延伸到無界時間的義務。這就是**遞迴性質**。

最典型的例子是「觸發後永遠保持」。若無遞迴，你會需要一個無界運算子；有了遞迴，定義便是一行，每週期重新喚起自己：

```systemverilog
// Once 'lock' is set, 'busy' must stay high for every following cycle
property stays_busy;
    busy and nexttime stays_busy;
endproperty

assert property ($rose(lock) |-> stays_busy);
```

將 `stays_busy` 讀作：「`busy` 現在成立，*且* `stays_busy` 從下一週期起成立。」展開後得到永無止境的 `busy ##1 busy ##1 busy ...`——這是陳述一個須無限期持續之不變式的緊湊方式。

## 帶出口的遞迴

永不停止的遞迴陳述的是純粹的「永遠」需求。更常見的是該義務持續*直到*某條件解除為止。`if/else`（或蘊涵）為遞迴提供一個基底情形（base case）：

```systemverilog
// After 'grant', 'hold' must remain high every cycle until 'done',
// and 'done' ends the obligation
property hold_until_done;
    hold and (done or nexttime hold_until_done);
endproperty

assert property ($rose(grant) |-> hold_until_done);
```

每個週期該性質都要求 `hold`，接著要嘛 `done` 抵達（遞迴停止，獲得滿足），要嘛該性質於下一週期重新套用。當每週期的義務不只是單純的布林時，遞迴形式能將「每週期直到解除」的意圖明確化，這是單一運算子有時做不到的。

## 良構遞迴的規則

SVA 中的遞迴受到限制，以使每個實例可判定（decidable）。關鍵規則：

- **隨時間推進。** 遞迴實例只能在一個正向時間步之後被觸及——也就是在 `nexttime`、`##1` 或等效延遲之後。在*同一*週期重新喚起自己的性質沒有時間上的基底，是不合法的。
- **遞迴周圍不得有否定。** 遞迴性質不得出現在 `not` 之下，不得位於蘊涵的左側，也不得出現在任何其真值必須以「否定」方式得知之處。遞迴只允許在正向位置（positive position）。
- **允許相互遞迴**，受同樣的約束：兩個性質可各自引用對方，前提是迴圈的每個週期都推進時間且保持正向。
- **沒有區域變數的危害。** 遞迴性質一般不得以需要無界個相異儲存空間的方式讓區域變數穿過遞迴；請將每週期的狀態保留在設計中，或以有界形式呈現。

這些規則保證遞迴要嘛在基底情形終止，要嘛每週期都有確定的進展，使工具能評估它。

## 何時動用遞迴

多數日常檢查不需遞迴：有界視窗（`##[1:N]`）、`until` 與 `throughout` 已涵蓋常見情形且讀來清楚。遞迴在以下情況才值得使用：

- 每週期的義務是比單一布林更豐富的性質，使單純的 `until` 無法承載；或
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

> **設計意圖。** 遞迴性質陳述的是一項*在時間上自相似*的意圖：「此規則現在成立，且同樣的規則對接下來的部分也成立。」它讓設計者能將一個無界或歸納的需求寫成一條清楚而有限的定義，而非一串笨拙的運算子。審慎使用時，它恰如協定本意地捕捉「持續這樣行為直到解除」。

## 常見陷阱

- **零延遲遞迴。** 沒有時間步的自我引用不合法，且沒有時間上的基底。請務必透過 `nexttime` 或 `##1` 推進。
- **否定之下的遞迴。** 將遞迴性質置於 `not` 之下或前提側會違反正向性規則。請讓遞迴保持在正向位置。
- **忘記基底情形。** 沒有出口的遞迴陳述的是嚴格的「永遠」規則。若義務應結束，請加上解除條件（`done`、`last`）。
- **在有界運算子適用處使用遞迴。** 對於固定視窗或單純的「保持直到」，`##[1:N]`、`until` 或 `throughout` 更清楚。請將遞迴保留給無界或歸納的意圖。

## 小結

- 遞迴性質引用自身、往後套用一個週期，以有限的定義描述一項無界或歸納的義務。
- 每個週期都必須推進時間並保持在正向位置；同週期或否定的遞迴不合法。
- `if/else` 或蘊涵的基底情形讓義務能在解除條件處結束。
- 當每週期的義務比布林更豐富，或需求在時間上天然自相似時，才動用遞迴；否則偏好有界運算子。

---

[← 區域變數](11-local-variables.md) · [目錄](../README.md) · [下一章：覆蓋率與空真（vacuity） →](13-coverage-and-vacuity.md)
