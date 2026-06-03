# 第三部 · 3. 斷言種類

[← 模擬語意](02-simulation-semantics.md) · [目錄](../README.md) · [下一章：布林層 →](04-boolean-layer.md)

## 學習目標

- 區分即時斷言、延遲斷言與並行斷言。
- 在 `assert`、`assume`、`cover` 與 `restrict` 之間做選擇。
- 為斷言的 pass 與 fail 分支撰寫動作區塊（action block）。
- 選擇正確的嚴重性任務：`$error`、`$fatal`、`$warning`、`$info`。

## 即時斷言

**即時斷言**（immediate assertion，即時斷言）是一條程序式語句。它在控制流抵達它的當下評估其運算式，如同 `if`，並使用其運算元的當前值。它屬於程序式程式碼之內——`always` 區塊、`initial` 區塊或任務（task）。

```systemverilog
always_comb begin
    next_state = decode(opcode);
    // Checked right here, with the value next_state just got
    assert (next_state != INVALID);
end
```

若運算式為真（或為非零、非 x 的值），斷言通過。若為假，斷言失敗，並依預設回報錯誤。即時斷言適用於必須在程序流某一點成立的條件——一個解碼後的值、一個函式前置條件、一個永不該進入 default 的 case 選擇。

## 延遲斷言

單純的即時斷言可能因*毛刺*（glitch）而觸發：一個組合訊號可能在穩定前的時間步中途短暫取得錯誤的值，而即時斷言會回報該暫態。**延遲斷言**（deferred assertion，延遲斷言）藉由把回報推遲到時間步結束、設計穩定之後來避免此問題。若屆時條件再次為真，便不回報任何事。

有兩種形式：

```systemverilog
// Observed-deferred: report at the end of the current time step
always_comb
    assert #0 (a == b);

// Final-deferred: report in the Final region (end of simulation step set)
always_comb
    assert final (a == b);
```

`assert #0` 把回報推遲到同一步的 Observed 區域；`assert final` 推得更遠。兩者皆抑制由中間毛刺引起的回報，這使延遲斷言成為檢查組合不變式而不被暫態值誤報的首選形式。

## 並行斷言

**並行斷言**（concurrent assertion，並行斷言）帶有時脈，並隨時間推理。它在時脈緣取樣其訊號（第 2 章），並檢查一個可能跨越多個週期的時序性質。它以 `assert property` 撰寫。

```systemverilog
// Over clocked time: every request is granted on the next cycle
assert property (@(posedge clk) req |=> gnt);
```

並行斷言可出現於模組、介面、program 或 `checker` 中，並持續執行，在每個時脈緣展開一次新的評估嘗試。這是用於協定、握手與 FSM 行為的形式，也是本部其餘內容的焦點。

## assert、assume、cover、restrict

一個性質可用於四種角色。關鍵字決定角色。

- **`assert`**——該性質*必須成立*。違反即為失敗。這是陳述設計意圖的預設方式。
- **`assume`**——該性質*被視為已知*。在模擬中 `assume` 如同 `assert` 般被檢查；在形式化驗證中它約束環境，告訴工具哪些輸入是合法的。用它來建模設計對外部所期望的契約。
- **`cover`**——不是檢查，而是*量測*。它記錄某行為是否確實發生，使你能確認某情境曾被執行。`cover` 永不失敗；它要嘛被命中，要嘛沒有。
- **`restrict`**——類似 `assume`，但僅用於形式化以*修剪*狀態空間（例如把某個組態輸入約束為單一值）。它在模擬中沒有作用。

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

`assert` 與 `assume` 的區別對形式化至關重要：斷言是*要證明的義務*，假設是*你被允許使用的前提*。

> **設計意圖。** 相同的性質文字依關鍵字而陳述不同的意圖。`assert` 說「我的設計保證這一點」。
> `assume` 說「環境向我承諾這一點」。`cover` 說「我想看到這件事至少發生一次」。
> 選擇關鍵字，就是選擇該行為由誰負責。

## 動作區塊

每個斷言都可附帶一個**動作區塊**：在 pass、fail 或兩者時執行的程式碼。它跟在斷言後面，如同 `if` 的分支。

```systemverilog
assert property (@(posedge clk) req |=> gnt)
    else $error("grant did not follow request at %0t", $time);
```

一般形態具有一個 pass 分支與一個 fail 分支：

```systemverilog
assert property (p)
    pass_count++;            // pass action (optional)
else
    $error("property p failed");   // fail action
```

pass 動作為選用，常被省略。fail 動作是你回報失敗之處；若省略它，模擬器仍會發出預設錯誤，但帶有情境（週期、訊號值）的自訂訊息在除錯時有用得多。動作區塊在 Reactive 區域執行，於性質評估之後。

## 嚴重性任務

fail 動作通常呼叫一個嚴重性系統任務。它們在工具如何反應上有所不同：

- **`$info`**——資訊性；無錯誤狀態。適用於 `cover` 內或追蹤訊息。
- **`$warning`**——警告；模擬繼續。
- **`$error`**——錯誤；模擬繼續，但該次執行被標記為失敗。這是被違反的 `assert` 的常態選擇。
- **`$fatal`**——致命錯誤；模擬立即停止。保留給壞到繼續已無意義的情況。

```systemverilog
assert property (@(posedge clk) wr_ptr < DEPTH)
    else $fatal(1, "FIFO pointer overflow — design is corrupt");
```

一般意圖違反選 `$error`，使回歸測試持續執行並回報每一個失敗；只有在繼續模擬已無意義時才選 `$fatal`。

## 常見陷阱

- **對有毛刺的組合訊號使用單純的即時斷言。** 它可能因暫態值而觸發。對組合不變式請使用延遲斷言（`assert #0` 或 `assert final`）。
- **混淆 `assume` 與 `assert`。** 在形式化中，過於寬鬆的 `assume` 可能因排除了會暴露錯誤的輸入而掩蓋真正的錯誤。只假設環境確實保證的事。
- **期望 `cover` 失敗。** `cover` 是量測；它永不失敗。若你要的是檢查，請用 `assert`。
- **預設使用 `$fatal`。** 在第一個違反時就停止執行，會掩蓋之後每一個失敗。請用 `$error`，使回歸測試回報所有失敗。
- **省略失敗訊息。** 預設回報缺乏情境。帶有時間與關鍵訊號的自訂 `$error` 可節省除錯工夫。

## 小結

- 即時斷言檢查程序式程式碼中某一點的條件；延遲斷言推遲回報以避免毛刺造成的誤報。
- 並行斷言帶有時脈，以 `assert property` 隨時間推理。
- 關鍵字設定角色：`assert`（必須成立）、`assume`（已知）、`cover`（量測）、`restrict`（形式化修剪）。
- 動作區塊在 pass 或 fail 時執行；fail 分支回報違反。
- 一般失敗用 `$error` 使執行繼續；保留 `$fatal` 給無法復原的情況。

---

[← 模擬語意](02-simulation-semantics.md) · [目錄](../README.md) · [下一章：布林層 →](04-boolean-layer.md)
