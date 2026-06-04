# 第三部 · 4. 布林層

[← assertion kinds](03-assertion-kinds.md) · [目錄](../README.md) · [下一章：sequence basics →](05-sequences-basics.md)

## 學習目標

- 寫出對 sampled value 運算的布林運算式。
- 用 `$rose`、`$fell`、`$stable`、`$changed` 偵測邊緣與變化。
- 用 `$past` 回溯過去。
- 用 `$onehot`、`$onehot0`、`$countones`、`$isunknown` 檢查 one-hot、計數與未知條件。

## 設計者的心智模型

布林層是 SVA 用來陳述「sampled clock edge 上的事實」的地方。在描述時序行為之前，你需要幾個可靠的單週期判斷：訊號有沒有上升？向量有沒有保持穩定？狀態是不是 one-hot？有沒有哪個位元變成未知？這些判斷就是大型 property 的最小組成單元。

因為它們使用 sampled value，這些函式談的通常是 flip-flop 所看到的設計，而不是暫態的程序式更新。這正是 `$rose`、`$past`、`$stable` 有價值的地方：它們讓 property 以帶 clock 的事實發言，而不是靠波形去猜。

## 布林層

SVA 是分層建構的。最底層是**布林層**（boolean layer）：在單一取樣點評估為真或假的一般運算式。sequence（第 5 章）與 property（第 7 章）都建構在這些布林之上。把布林層做對，是上面一切的基礎。

concurrent assertion 中的布林運算式，用的是與 RTL 相同的運算子（`&`、`|`、`==`、`<`、`&&` 等），但它運算的對象是 **sampled value**（第 2 章），而不是活值。因此 assertion 中的 `a && b` 指的是「取樣到的 `a` 與取樣到的 `b`，在這個 clock edge 之前於 Preponed 取得」。

```systemverilog
// Sampled values: a, b, and c as of this clock edge
assert property (@(posedge clk) (a && b) |-> c);
```

## sampled value 函式

布林常常需要把本週期的值和前一週期的值相比。sampled value 函式做的正是這件事，全都以 assertion clock 為基準。

### $rose、$fell、$stable、$changed

這些函式把現在的 sampled value 和一個 clock 之前的 sampled value 相比：

- **`$rose(e)`**：`e` 從上一週期由 0 變為 1 時為真（sampled value 的上升緣）。
- **`$fell(e)`**：`e` 由 1 變為 0 時為真。
- **`$stable(e)`**：`e` 相對於上一週期沒有變化時為真。
- **`$changed(e)`**：`e` 與上一週期不同時為真（`$stable` 的否定）。

```systemverilog
// A handshake: when req rises, gnt must follow on the next cycle
assert property (@(posedge clk) $rose(req) |=> gnt);

// Configuration must not change while the core is busy
assert property (@(posedge clk) busy |-> $stable(cfg));
```

`$rose` 與 `$fell` 測試的是單一位元（向量則取最低有效位）。`$stable` 與 `$changed` 則對整個運算式運作，包含向量。由於它們是和前一個*取樣*值相比，因此就是 assertion 層談論邊緣的正規方式，別自己拿手動延遲的副本去做 `==` 比較來重建邊緣。

### $past

`$past(e)` 回傳 `e` 在若干週期前所持有的 sampled value：

```systemverilog
// $past(e) — e one cycle earlier
// $past(e, n) — e n cycles earlier
assert property (@(posedge clk) load |=> (q == $past(d)));
```

這表示：`load` 之後一個週期，`q` 等於 `d` *在 load 當下*所持有的值，也就是經典的暫存器擷取檢查。第二個引數是選用的，可以回溯得更遠：

```systemverilog
// data_out is the input delayed by exactly 3 cycles
assert property (@(posedge clk) data_out == $past(data_in, 3));
```

`$past` 還接受選用的閘控運算式與 clock；日常使用上，單引數與雙引數兩種形式已足以涵蓋多數需求。要注意的是：在 simulation 早期、還沒經過 `n` 個週期之前，`$past` 回傳的是 reset 或初始值，因此 assertion 要設計成讓這段啟動區間不會誤報（第 8 章的 `disable iff` 與 implication 的 vacuity 都有幫助）。

## 位元樣式函式

有幾個函式專門表達向量位元的不變式，正是設計者對狀態暫存器或選擇線所掌握的那類事實。

### $onehot 與 $onehot0

- **`$onehot(e)`**：`e` 恰好有一個位元為 1 時為真。
- **`$onehot0(e)`**：`e` 至多有一個位元為 1（零個或一個）時為真。

```systemverilog
// A one-hot state register: exactly one bit set, every cycle
assert property (@(posedge clk) disable iff (!rst_n) $onehot(state));

// At most one master may be granted at a time
assert property (@(posedge clk) $onehot0(grant));
```

要陳述 one-hot FSM 或互斥授權向量的不變式，`$onehot` 是最自然的寫法。當「全為零」也算合法狀態時（例如沒有授權的閒置匯流排），就改用 `$onehot0`。

### $countones

`$countones(e)` 回傳 `e` 中被設為 1 的位元數。它把 one-hot 檢查推廣到任意的確切計數：

```systemverilog
// Exactly two ports may be active in this mode
assert property (@(posedge clk) (mode == DUAL) |-> $countones(active) == 2);
```

### $isunknown

`$isunknown(e)` 在 `e` 的任一位元為 `x` 或 `z` 時為真。它是 assertion 層的防線，用來擋住跑到不該出現之處的未知值：

```systemverilog
// Control bus must never carry x or z once out of reset
assert property (@(posedge clk) disable iff (!rst_n) !$isunknown(ctrl));
```

這是成本低、價值高的檢查。在 simulation 裡溜過去的未知值，往往到了矽中就變成真正的錯誤；對關鍵訊號 assert `!$isunknown`，就能在源頭把它們攔下來。

> **設計意圖。** 布林層是設計者陳述「必須在單一邊緣成立」之事實的地方：這個向量是 one-hot、
> 這個控制字永遠不會是未知、這個暫存器擷取到正確的值。這些都是你對每個訊號心中所抱的不變式，
> sampled value 函式讓你能以 assertion clock 的語彙把它們寫下來。

## 常見陷阱

- **忘了布林用的是 sampled value。** assertion 中的 `a && b` 是取樣到的 `a` 與 `b`，不是它們的活值。當某個 `always` 區塊這一步正在更新它們時，這點就很重要。
- **自己手刻邊緣偵測。** 請用 `$rose`／`$fell`，別拿手動延遲的副本去比；sampled value 版本就構造而言本來就正確。
- **忽略 `$past` 在啟動時的行為。** 在累積足夠週期之前，`$past` 回傳的是初始值。用 `disable iff (reset)` 把這類 assertion 閘控起來，或倚賴 implication 的 vacuity，讓啟動區間不會觸發。
- **該用 `$onehot0` 的地方卻用了 `$onehot`。** 若「沒有任何位元被設」是合法的閒置狀態，`$onehot` 會在這種情況下誤判失敗。允許全零時，請選 `$onehot0`。
- **用 `$rose`／`$fell` 去比較向量。** 它們只測試單一位元。要偵測整個向量的變化，請用 `$changed` 或 `$stable`。

## 小結

- 布林層是對 **sampled value** 運算的一般運算式，是 sequence 與 property 的基礎。
- `$rose`、`$fell`、`$stable`、`$changed` 拿本週期和前一週期相比，`$past` 則回溯指定的週期數。
- `$onehot`、`$onehot0`、`$countones` 陳述位元計數不變式，`$isunknown` 守住 `x`／`z`。
- 優先用這些函式，而不是自己手寫等效物；對照 sampled value 模型，它們就構造而言本來就正確。

---

[← assertion kinds](03-assertion-kinds.md) · [目錄](../README.md) · [下一章：sequence basics →](05-sequences-basics.md)
