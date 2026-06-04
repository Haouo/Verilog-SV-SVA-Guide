# 第三部 · 4. 布林層

[← assertion kinds](03-assertion-kinds.md) · [目錄](../README.md) · [下一章：sequence basics →](05-sequences-basics.md)

## 學習目標

- 撰寫對 sampled value 運算的布林運算式。
- 以 `$rose`、`$fell`、`$stable`、`$changed` 偵測邊緣與變化。
- 以 `$past` 回溯過去。
- 以 `$onehot`、`$onehot0`、`$countones`、`$isunknown` 檢查 one-hot、計數與未知條件。

## 設計者 mental model

Boolean layer 是 SVA 用來談 sampled clock edge 上事實的地方。在寫 temporal behavior 之前，
你需要可靠的一個 cycle predicate：signal 有沒有 rise？vector 有沒有 stable？state 是否 one-hot？
有沒有 bit 變成 unknown？這些 predicate 是大型 property 的 atom。

因為它們使用 sampled value，這些 function 通常是在談 flip-flop 看到的 design，而不是 transient
procedural update。這就是 `$rose`、`$past`、`$stable` 有價值的原因：它們讓 property 用 clocked
fact 說話，而不是靠 waveform guess。

## 布林層

SVA 以分層建構。最底層是**布林層**（boolean layer）：在單一 sampling 點評估為真或假的一般運算式。sequence（第 5 章）與 property（第 7 章）建構於這些布林之上。把布林層做對，是其上一切的基礎。

concurrent assertion 中的布林運算式使用與 RTL 相同的運算子——`&`、`|`、`==`、`<`、`&&` 等——但它運算的是**sampled value**（第 2 章），而非活值。因此 assertion 中的 `a && b` 意指「sampling 的 `a` 與 sampling 的 `b`，於此 clock edge 之前在 Preponed 取得」。

```systemverilog
// Sampled values: a, b, and c as of this clock edge
assert property (@(posedge clk) (a && b) |-> c);
```

## sampled value 函式

布林常需把本週期的值與前一週期的值相比。sampled value 函式正是如此運作，全部相對於 assertion clock。

### $rose、$fell、$stable、$changed

這些函式把現在的 sampled value 與一個 clock 之前的 sampled value 相比：

- **`$rose(e)`**——當 `e` 自上一週期由 0 變為 1 時為真（sampled value 的上升緣）。
- **`$fell(e)`**——當 `e` 由 1 變為 0 時為真。
- **`$stable(e)`**——當 `e` 相對於上一週期未變時為真。
- **`$changed(e)`**——當 `e` 與上一週期不同時為真（`$stable` 的否定）。

```systemverilog
// A handshake: when req rises, gnt must follow on the next cycle
assert property (@(posedge clk) $rose(req) |=> gnt);

// Configuration must not change while the core is busy
assert property (@(posedge clk) busy |-> $stable(cfg));
```

`$rose` 與 `$fell` 測試單一位元（向量取最低有效位）。`$stable` 與 `$changed` 對整個運算式運作，包含向量。由於它們相對於前一個*sampling*值比較，它們是 assertion 層談論邊緣的方式——不要試圖用對手動延遲副本的原始 `==` 比較來重建邊緣。

### $past

`$past(e)` 回傳 `e` 在若干週期前所持有的 sampled value：

```systemverilog
// $past(e) — e one cycle earlier
// $past(e, n) — e n cycles earlier
assert property (@(posedge clk) load |=> (q == $past(d)));
```

這表示：`load` 之後一個週期，`q` 等於 `d` *在 load 當下*所持有的值——經典的暫存器擷取檢查。選用的第二個引數可回溯更遠：

```systemverilog
// data_out is the input delayed by exactly 3 cycles
assert property (@(posedge clk) data_out == $past(data_in, 3));
```

`$past` 亦接受選用的閘控運算式與 clock；日常使用中，單引數與雙引數形式已能涵蓋多數需求。注意：在 simulation 早期、尚未經過 `n` 個週期之前，`$past` 回傳 reset／初始值——請設計 assertion 使此啟動區間不產生誤報（第 8 章的 `disable iff` 與 implication 的 vacuity 皆有助於此）。

## 位元樣式函式

數個函式表達關於向量位元的不變式——正是設計者對狀態暫存器或選擇線所知的那類事實。

### $onehot 與 $onehot0

- **`$onehot(e)`**——當 `e` 恰有一個位元為 1 時為真。
- **`$onehot0(e)`**——當 `e` 至多有一個位元為 1（零或一）時為真。

```systemverilog
// A one-hot state register: exactly one bit set, every cycle
assert property (@(posedge clk) disable iff (!rst_n) $onehot(state));

// At most one master may be granted at a time
assert property (@(posedge clk) $onehot0(grant));
```

`$onehot` 是陳述 one-hot FSM 或互斥授權向量不變式的自然方式。當「全為零」也是合法狀態時（例如沒有授權的閒置匯流排）使用 `$onehot0`。

### $countones

`$countones(e)` 回傳 `e` 中被設為 1 的位元數。它把 one-hot 檢查推廣到任意確切計數：

```systemverilog
// Exactly two ports may be active in this mode
assert property (@(posedge clk) (mode == DUAL) |-> $countones(active) == 2);
```

### $isunknown

`$isunknown(e)` 在 `e` 的任一位元為 `x` 或 `z` 時為真。它是 assertion 層對未知值抵達不該抵達之處的防護：

```systemverilog
// Control bus must never carry x or z once out of reset
assert property (@(posedge clk) disable iff (!rst_n) !$isunknown(ctrl));
```

這是廉價而高價值的檢查。simulation 中溜過去的未知值，往往在矽中成為真正的錯誤；對關鍵訊號 assertion `!$isunknown` 可在源頭捕捉它們。

> **設計意圖。** 布林層是設計者陳述「必須在單一邊緣成立」之事實之處：這個向量是 one-hot、
> 這個控制字永不未知、這個暫存器擷取了正確的值。這些是你對每個訊號所懷抱的不變式——
> sampled value 函式讓你以 assertion clock 的語彙把它們寫下來。

## 常見陷阱

- **忘記布林使用 sampled value。** assertion 中的 `a && b` 是 sampling 的 `a` 與 `b`，而非其活值。當某 `always` 區塊本步正在更新它們時，這一點很重要。
- **手工撰寫邊緣偵測。** 請用 `$rose`／`$fell`，而非與手動延遲副本相比；sampled value 版本就構造而言是正確的。
- **忽略 `$past` 在啟動時的行為。** 在足夠的週期經過之前，`$past` 回傳初始值。以 `disable iff (reset)` 閘控此類 assertion，或倚賴 implication 的 vacuity，使啟動區間不觸發。
- **在該用 `$onehot0` 之處用了 `$onehot`。** 若「無位元被設」是合法的閒置狀態，`$onehot` 會在其上錯誤地失敗。允許零時請選 `$onehot0`。
- **以 `$rose`／`$fell` 比較向量。** 它們測試單一位元。整向量的變化偵測請用 `$changed` 或 `$stable`。

## 小結

- 布林層是對**sampled value**的一般運算式，是 sequence 與 property 的基礎。
- `$rose`、`$fell`、`$stable`、`$changed` 比較本週期與前一週期；`$past` 回溯選定的週期數。
- `$onehot`、`$onehot0`、`$countones` 陳述位元計數不變式；`$isunknown` 防護 `x`／`z`。
- 優先採用這些函式而非手工等效物；它們就 sampled value 模型而言是構造正確的。

---

[← assertion kinds](03-assertion-kinds.md) · [目錄](../README.md) · [下一章：sequence basics →](05-sequences-basics.md)
