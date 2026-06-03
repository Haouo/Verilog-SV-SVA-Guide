# 第三部 · 6. 序列運算

[← 序列：基礎](05-sequences-basics.md) · [目錄](../README.md) · [下一章：性質（property） →](07-properties.md)

## 學習目標

- 以 `and`、`or`、`intersect` 組合序列。
- 以 `throughout` 與 `within` 約束序列的持續時間。
- 以 `first_match` 把多個匹配收斂為最早者。
- 以 `.triggered` 與 `.ended` 把序列當作布林事件使用。

## 組合序列

第 5 章建構了單一序列。真實意圖常組合多個樣式——兩件都必須發生的事，或必須在另一者整段期間都成立的條件。序列運算表達這些組合。

### and

`seq1 and seq2` 在*兩個*序列都匹配、且各自從同一週期起始時匹配。它們不必同時結束；組合匹配在兩者端點較晚者結束：

```systemverilog
// From start, both a 2-cycle data path and a 3-cycle control path complete
sequence both_paths;
    (start ##2 data_ok) and (start ##3 ctrl_ok);
endsequence
```

當兩件獨立的事必須從共同起點都發生、且不要求它們耗用相同週期數時，使用 `and`。

### or

`seq1 or seq2` 在*任一*序列匹配時匹配。它是選擇運算子：

```systemverilog
// A response is either an ack next cycle or a nak two cycles later
sequence resp;
    (req ##1 ack) or (req ##2 nak);
endsequence
```

### intersect

`intersect` 類似 `and`，但更嚴格：兩個序列必須都匹配*且*具有**相同長度**。它們同時起始、同時結束：

```systemverilog
// Two patterns that must both hold over exactly the same window
sequence locked_window;
    (busy[*1:$]) intersect (req ##[1:$] done);
endsequence
```

當兩個行為必須佔據完全相同的跨度——同起點、同終點——時使用 `intersect`。若你只在意兩者從共同起點都發生，請用 `and`。

## throughout：跨一段跨度的條件

`expr throughout seq` 要求布林 `expr` 在序列 `seq` 的*每一個*週期都為真。它是陳述「這個在那個的整段期間都保持為真」的方式：

```systemverilog
// Enable must stay high for the entire 4-cycle burst
sequence held_burst;
    en throughout (start ##1 d1 ##1 d2 ##1 d3);
endsequence
```

若 `en` 在叢發期間任一週期掉落，序列便失敗。`throughout` 是表達綁定於另一序列生命週期的保持條件的標準方式——一個必須在整個傳輸期間保持有效的晶片選擇、一個必須在操作期間維持設定的旗標。

## within：包含

`seq1 within seq2` 要求 `seq1` 在 `seq2` 的跨度*之內*某處匹配：`seq1` 在 `seq2` 起始當下或之後起始，並在 `seq2` 結束當下或之前結束：

```systemverilog
// A single ack pulse must occur somewhere within the busy window
sequence ack_in_busy;
    (ack[*1]) within (busy[*1:$]);
endsequence
```

`within` 是包含：內層樣式被外層樣式所夾。當事件必須在已知窗口期間發生、但其在窗口內的確切位置不固定時使用它。

## first_match：取最早者

帶有範圍或無界延遲的序列可能以多種方式匹配——`req ##[1:3] gnt` 在 `gnt` 於 +1、+2 或 +3 週期抵達時皆匹配。`first_match` 只保留*最早*的匹配並捨棄其餘：

```systemverilog
// Once gnt arrives, stop looking; commit to the first match
sequence first_gnt;
    first_match(req ##[1:3] gnt);
endsequence
```

當後續項目依賴匹配點，或當你想對每個請求恰好附加一次動作（而非對每個可能匹配各一次）時，這很重要。`first_match` 是使窗口序列表現得像單一、明確事件的常用方式。

## 序列作為事件：.triggered 與 .ended

序列可被當作一個布林使用，它在序列*完成*的週期為真。兩個方法揭露此特性，主要用於關聯不同時脈上的序列，或把一個序列的完成當作另一個的起始條件。

- **`seq.triggered`**——在 `seq` 達成匹配的週期為真。它以端點測試的方式評估，是從序列外部偵測其完成的常用形式，包含跨時脈域。
- **`seq.ended`**——也在 `seq` 匹配其結尾時為真，匹配點定義於序列的結尾。

```systemverilog
sequence s_req;
    $rose(req) ##1 hold;
endsequence

// When s_req completes, the grant logic must respond next cycle
assert property (@(posedge clk) s_req.triggered |=> gnt);
```

兩者皆讓序列的完成充當單一週期的布林事件，使你能串接或交叉參考序列。對多數單時脈意圖，你會直接撰寫蘊涵（第 7 章）；`.triggered` 與 `.ended` 在多時脈與模組化斷言結構中才真正發揮所長。

> **設計意圖。** 序列運算讓設計者陳述各個帶時序的行為如何彼此關聯：兩者都須發生（`and`）、
> 任一者可發生（`or`）、它們必須完全重合（`intersect`）、一者須在另一者整段期間都保持（`throughout`）、
> 一者須位於另一者之內（`within`）。這些對應你對協定早已使用的措辭——「忙碌時保持 enable」、
> 「在窗口內 ack」——並把它們化為可檢查的形式。

## 常見陷阱

- **在該用 `intersect` 之處用了 `and`。** `and` 允許兩序列長度不同；`intersect` 強制長度相等。請選符合意圖者。
- **混淆 `throughout` 與 `within`。** `throughout` 把*布林*跨一個序列的整段跨度保持；`within` 把一個*序列*置於另一者的跨度之內。
- **忘記對窗口序列使用 `first_match`。** 若無它，`##[m:n]` 延遲可能產生多個匹配，使動作倍增或令後續項目混亂。
- **在單時脈上不必要地動用 `.triggered`。** 對同時脈意圖，直接蘊涵更清晰；把 `.triggered`／`.ended` 保留給多時脈或把完成重用為事件之用。

## 小結

- `and` 要求兩序列（長度不拘）；`or` 要求任一者；`intersect` 要求兩者且長度相等。
- `throughout` 把布林跨一個序列的整段持續時間保持；`within` 把一個序列包含於另一者之內。
- `first_match` 把多匹配序列收斂為其最早的匹配。
- `.triggered` 與 `.ended` 把序列的完成揭露為單一週期事件，適用於串接與多時脈斷言。

---

[← 序列：基礎](05-sequences-basics.md) · [目錄](../README.md) · [下一章：性質（property） →](07-properties.md)
