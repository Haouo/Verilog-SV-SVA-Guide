# 第三部 · 6. sequence operation

[← sequence basics](05-sequences-basics.md) · [目錄](../README.md) · [下一章：property →](07-properties.md)

## 學習目標

- 以 `and`、`or`、`intersect` 組合 sequence。
- 以 `throughout` 與 `within` 約束 sequence 的持續時間。
- 以 `first_match` 把多個匹配收斂為最早者。
- 以 `.triggered` 與 `.ended` 把 sequence 當作布林事件使用。

## 設計者的心智模型

sequence operation 描述的是各個時序樣式之間的關係。`and`、`or`、`intersect` 不只是名字比較長的邏輯運算子，它們各自用不同的起點與終點規則來組合匹配。`throughout` 和 `within` 則讓一個條件或樣式去約束另一個樣式的存活期間。

實務上，問題永遠要回到規格書會怎麼描述。某個事件是否在另一個訊號保持為真時發生？ack 是否出現在 busy 窗口之內？兩個行為是否必須同時結束？哪一句話貼近你的意圖，就選對應的那個運算子。

## 從問題開始

第 5 章的 sequence 能描述「A 後面接 B」這種單一路徑，但真實協定常常不是一條線。你可能要說：「資料路徑和控制路徑都要完成」、「`valid` 保持期間資料不能變」、「`ack` 必須落在 `busy` 的窗口內」。這些句子都不是單純多接幾個 `##` 就能乾淨表達。

sequence operation 的作用，是把多個時間形狀放在同一張時間線上比較：同起點、同終點、包含、持續、或多個可能匹配中選第一個。讀這章時，先把規格句子中的關係找出來，再對應到 `and`、`intersect`、`throughout`、`within` 或 `first_match`。

## 組合 sequence

第 5 章建構的是單一 sequence。但真實的意圖往往要組合多個樣式：兩件都必須發生的事，或是必須在另一者整段期間都成立的條件。sequence operation 就是用來表達這些組合的。

### and

`seq1 and seq2` 在*兩個* sequence 都匹配、且各自從同一週期起始時才匹配。兩者不必同時結束；組合後的匹配在兩個端點中較晚的那個結束：

```systemverilog
// From start, both a 2-cycle data path and a 3-cycle control path complete
sequence both_paths;
    (start ##2 data_ok) and (start ##3 ctrl_ok);
endsequence
```

當兩件獨立的事必須從共同起點同時開始、且不要求耗用相同週期數時，就用 `and`。

### or

`seq1 or seq2` 在*任一個* sequence 匹配時就匹配。它是選擇運算子：

```systemverilog
// A response is either an ack next cycle or a nak two cycles later
sequence resp;
    (req ##1 ack) or (req ##2 nak);
endsequence
```

### intersect

`intersect` 類似 `and`,但更嚴格：兩個 sequence 必須都匹配，*而且*要有**相同的長度**。它們同時起始、同時結束：

```systemverilog
// Two patterns that must both hold over exactly the same window
sequence locked_window;
    (busy[*1:$]) intersect (req ##[1:$] done);
endsequence
```

當兩個行為必須佔據完全相同的跨度，也就是同起點、同終點時，就用 `intersect`。若只在意兩者是否從共同起點都發生，則用 `and`。

## throughout：跨一段跨度的條件

`expr throughout seq` 要求布林 `expr` 在 sequence `seq` 的*每一個*週期都為真。它用來陳述「某個條件在另一段過程的整段期間都保持為真」：

```systemverilog
// Enable must stay high for the entire 4-cycle burst
sequence held_burst;
    en throughout (start ##1 d1 ##1 d2 ##1 d3);
endsequence
```

只要 `en` 在叢發期間任一週期掉落，sequence 就失敗。要表達一個綁在另一個 sequence 存活期間的保持條件，`throughout` 是標準寫法：例如必須在整個傳輸期間都保持有效的晶片選擇，或必須在操作期間都維持設定的旗標。

## within：包含

`seq1 within seq2` 要求 `seq1` 在 `seq2` 跨度*之內*的某處匹配：`seq1` 不早於 `seq2` 起始，也不晚於 `seq2` 結束：

```systemverilog
// An ack must occur somewhere within the busy window
sequence ack_in_busy;
    (ack[*1]) within (busy[*1:$]);
endsequence
```

`within` 表達的是包含關係：內層樣式被外層樣式夾住。當事件必須在某個已知窗口期間發生、但確切位置不固定時，就用它。

## first_match：取最早者

帶有範圍或無界延遲的 sequence 可能有多種匹配方式：只要 `gnt` 在 +1、+2 或 +3 週期抵達，`req ##[1:3] gnt` 都會匹配。`first_match` 只保留*最早*的那個匹配，其餘一概捨棄：

```systemverilog
// Once gnt arrives, stop looking; commit to the first match
sequence first_gnt;
    first_match(req ##[1:3] gnt);
endsequence
```

當後續項目依賴匹配點，或當你想對每個請求恰好附加一次動作(而不是對每個可能匹配各附加一次)時，這一點很重要。要讓窗口 sequence 表現得像一個單一、明確的事件，`first_match` 是常用的做法。

## sequence 作為事件：.triggered 與 .ended

sequence 可以當成一個布林來用，它在 sequence *完成*的那個週期為真。有兩個方法可以取得這個值，主要用於關聯不同 clock 上的 sequence,或把一個 sequence 的完成當作另一個的起始條件。

- **`seq.triggered`**:在 `seq` 達成匹配的週期為真。它以端點測試的方式評估，是從 sequence 外部(含跨 clock domain)偵測其完成的常用形式。
- **`seq.ended`**:同樣在 `seq` 匹配其結尾時為真，匹配點定義在 sequence 的結尾。

```systemverilog
sequence s_req;
    $rose(req) ##1 hold;
endsequence

// When s_req completes, the grant logic must respond next cycle
assert property (@(posedge clk) s_req.triggered |=> gnt);
```

兩者都讓 sequence 的完成充當一個單一週期的布林事件，你便能串接或交叉參考 sequence。多數 single-clock 的意圖，直接寫 implication(第 7 章)即可；`.triggered` 與 `.ended` 要到 multiclock 與模組化 assertion 結構裡才真正派上用場。

> **設計意圖。** sequence operation 讓設計者陳述各個帶時序的行為如何彼此關聯：兩者都須發生(`and`)、
> 任一者發生即可(`or`)、兩者必須完全重合(`intersect`)、一者須在另一者整段期間都保持(`throughout`)、
> 一者須位於另一者之內(`within`)。這些正對應你描述協定時早已在用的說法，例如「忙碌時保持 enable」、
> 「在窗口內 ack」，只是把它們化為可檢查的形式。

## 常見陷阱

- **該用 `intersect` 的地方用了 `and`。** `and` 允許兩個 sequence 長度不同；`intersect` 強制長度相等。請選符合意圖的那個。
- **混淆 `throughout` 與 `within`。** `throughout` 讓一個*布林*在某個 sequence 的整段跨度都保持；`within` 則把一個 *sequence* 放進另一者的跨度之內。
- **忘了對窗口 sequence 加 `first_match`。** 少了它，`##[m:n]` 延遲可能產生多個匹配，使動作倍增或令後續項目混亂。
- **在 single-clock 上多此一舉地動用 `.triggered`。** 同 clock 的意圖，直接用 implication 更清楚；`.triggered`／`.ended` 留給 multiclock,或留給把完成重用為事件的場合。

## 小結

- `and` 要求兩個 sequence 都匹配(長度不拘);`or` 要求任一者匹配；`intersect` 要求兩者都匹配且長度相等。
- `throughout` 讓布林在一個 sequence 的整段持續時間都保持；`within` 把一個 sequence 包含在另一者之內。
- `first_match` 把多匹配的 sequence 收斂為最早的那個匹配。
- `.triggered` 與 `.ended` 把 sequence 的完成取為單一週期事件，適用於串接與 multiclock assertion。

---

[← sequence basics](05-sequences-basics.md) · [目錄](../README.md) · [下一章：property →](07-properties.md)
