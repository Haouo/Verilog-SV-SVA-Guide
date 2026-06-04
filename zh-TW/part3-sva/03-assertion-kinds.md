# 第三部 · 3. assertion kinds

[← simulation semantics](02-simulation-semantics.md) · [目錄](../README.md) · [下一章：布林層 →](04-boolean-layer.md)

## 學習目標

- 區分 immediate assertion、deferred assertion 與 concurrent assertion。
- 在 `assert`、`assume`、`cover` 與 `restrict` 之間做出取捨。
- 為 assertion 的 pass 與 fail 分支寫出動作區塊（action block）。
- 選對嚴重性任務：`$error`、`$fatal`、`$warning`、`$info`。

## 設計者的心智模型

同一個 Boolean 或 temporal 運算式，會隨著外層的 assertion kind 與關鍵字而改變意思。immediate assertion 檢查程序流某一點的條件，concurrent assertion 檢查帶 clock 時間上的行為。`assert`、`assume`、`cover`、`restrict` 則說明這個運算式是設計保證、對環境的承諾，還是一個可達性問題。

這個差異在 simulation 與 formal 之間切換時最關鍵。在 simulation 裡，`assume` 會視工具而定，行為可能像 check，也可能像 constraint；在 formal 裡，錯誤的 `assume` 可能把你本來要找的行為整個移除。請把關鍵字當成意圖的一部分，而不是 property 外面的一層包裝。

## immediate assertion

**immediate assertion**是一條程序式語句。它和 `if` 一樣，在控制流抵達它的當下評估運算式，並使用運算元的當前值。它身處程序式程式碼之內：`always` 區塊、`initial` 區塊或任務（task）。

```systemverilog
always_comb begin
    next_state = decode(opcode);
    // Checked right here, with the value next_state just got
    assert (next_state != INVALID);
end
```

運算式為真（或為非零、非 x 的值）時，assertion 通過；為假時則失敗，並依預設回報錯誤。immediate assertion 適合用來檢查必須在程序流某一點成立的條件，例如一個解碼後的值、一個函式前置條件，或一個永遠不該落入 default 的 case 選擇。

## deferred assertion

單純的 immediate assertion 可能被*毛刺*（glitch）觸發：一個組合訊號可能在穩定之前的時間步中途，短暫取到錯誤的值，而 immediate assertion 就會把這個暫態回報出來。**deferred assertion** 把回報延到時間步結束、設計穩定之後才做，藉此避開這個問題。如果到那時條件又變回真，就什麼都不回報。

有兩種形式：

```systemverilog
// Observed-deferred: report at the end of the current time step
always_comb
    assert #0 (a == b);

// Final-deferred: report in the Reactive region, after #0 deferred checks
always_comb
    assert final (a == b);
```

`assert #0` 把回報延到同一步的 Observed 區域，`assert final` 則延得更遠，到 Reactive 區域。兩者都會壓掉由中間毛刺引起的回報，因此 deferred assertion 成了檢查組合不變式的首選形式：既能查，又不會被暫態值誤報。

## concurrent assertion

**concurrent assertion**帶有 clock，並隨時間推理。它在 clock edge 取樣訊號（第 2 章），檢查一個可能跨越多個週期的 temporal property，寫法是 `assert property`。

```systemverilog
// Over clocked time: every request is granted on the next cycle
assert property (@(posedge clk) req |=> gnt);
```

concurrent assertion 可以出現在模組、interface、program 或 `checker` 中，而且持續執行，每個 clock edge 都會展開一次新的評估嘗試。protocol、handshake 與 FSM 行為都用這種形式，它也是本部接下來的重點。

## assert、assume、cover、restrict

一個 property 可以擔任四種角色，由關鍵字決定。

- **`assert`**：該 property *必須成立*，違反就是失敗。這是陳述設計意圖的預設方式。
- **`assume`**：該 property *被視為已知*。在 simulation 中，`assume` 會像 `assert` 一樣被檢查；在 formal verification 中，它約束環境，告訴工具哪些輸入是合法的。用它來描述設計對外界所期望的契約。
- **`cover`**：它不是檢查，而是*量測*。它記錄某個行為是否真的發生，讓你能確認某情境曾被執行到。`cover` 永遠不會失敗，只有命中與沒命中兩種結果。
- **`restrict`**：類似 `assume`，但只用於 formal，用來*修剪*狀態空間（例如把某個組態輸入約束成單一值）。它在 simulation 中沒有作用。

```systemverilog
// Intent we are checking
assert property (@(posedge clk) wr_en |-> !full);

// Environment contract: the source never writes when full
assume property (@(posedge clk) full |-> !wr_en);

// Did we ever actually fill the FIFO during this test?
cover  property (@(posedge clk) full);

// Formal only: pin the mode input to streaming for this proof
restrict property (@(posedge clk) mode == STREAM);
```

`assert` 與 `assume` 的區別對 formal 至關重要：assertion 是*要證明的義務*，assumption 是*你被允許使用的前提*。

> **設計意圖。** 同一段 property 文字，會因關鍵字不同而陳述不同的意圖。`assert` 說的是「我的設計保證這一點」，
> `assume` 說的是「環境向我承諾這一點」，`cover` 說的是「我想看到這件事至少發生一次」。
> 選哪個關鍵字，就是在選這個行為該由誰負責。

## 動作區塊

每個 assertion 都可以附帶一個**動作區塊**：在 pass、fail 或兩者皆是時執行的程式碼。它跟在 assertion 後面，就像 `if` 的分支。

```systemverilog
assert property (@(posedge clk) req |=> gnt)
    else $error("grant did not follow request at %0t", $time);
```

一般形態是一個 pass 分支加一個 fail 分支：

```systemverilog
assert property (p)
    pass_count++;            // pass action (optional)
else
    $error("property p failed");   // fail action
```

pass 動作是選用的，通常會省略。fail 動作則是你回報失敗的地方；就算省略它，simulator 仍會發出預設錯誤，但帶有情境（週期、訊號值）的自訂訊息在除錯時有用得多。動作區塊在 property 評估之後，於 Reactive 區域執行。

## 嚴重性任務

fail 動作通常會呼叫一個嚴重性系統任務。它們的差別在於工具如何反應：

- **`$info`**：資訊性訊息，不帶錯誤狀態。適合放在 `cover` 內或當追蹤訊息。
- **`$warning`**：警告，simulation 繼續進行。
- **`$error`**：錯誤，simulation 繼續，但該次執行會被標記為失敗。這是 `assert` 被違反時的常態選擇。
- **`$fatal`**：致命錯誤，simulation 立刻停止。保留給壞到再繼續也沒意義的情況。

```systemverilog
assert property (@(posedge clk) wr_ptr < DEPTH)
    else $fatal(1, "FIFO pointer overflow — design is corrupt");
```

一般的意圖違反選 `$error`，讓回歸測試繼續跑、回報每一個失敗；只有在 simulation 再跑下去已無意義時，才選 `$fatal`。

## 常見陷阱

- **對會有毛刺的組合訊號用單純的 immediate assertion。** 它可能被暫態值觸發。檢查組合不變式請改用 deferred assertion（`assert #0` 或 `assert final`）。
- **把 `assume` 和 `assert` 搞混。** 在 formal 中，過於寬鬆的 `assume` 會把能暴露錯誤的輸入排除掉，反而掩蓋真正的錯誤。只假設環境真的保證的事。
- **期望 `cover` 會失敗。** `cover` 是量測，永遠不會失敗。要的是檢查就用 `assert`。
- **預設就用 `$fatal`。** 一遇到第一個違反就停止執行，會掩蓋後面每一個失敗。請用 `$error`，讓回歸測試把所有失敗都回報出來。
- **省略失敗訊息。** 預設回報缺乏情境。帶上時間與關鍵訊號的自訂 `$error`，能省下不少除錯工夫。

## 小結

- immediate assertion 檢查程序式程式碼中某一點的條件；deferred assertion 延後回報，以避免毛刺造成的誤報。
- concurrent assertion 帶有 clock，以 `assert property` 隨時間推理。
- 關鍵字決定角色：`assert`（必須成立）、`assume`（已知）、`cover`（量測）、`restrict`（formal 修剪）。
- 動作區塊在 pass 或 fail 時執行，fail 分支負責回報違反。
- 一般失敗用 `$error` 讓執行繼續，`$fatal` 留給無法復原的情況。

---

[← simulation semantics](02-simulation-semantics.md) · [目錄](../README.md) · [下一章：布林層 →](04-boolean-layer.md)
