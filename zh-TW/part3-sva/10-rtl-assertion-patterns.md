# 第三部 · 10. RTL assertion pattern

[← bind 與放置](09-binding-and-placement.md) · [目錄](../README.md) · [下一章：區域變數 →](11-local-variables.md)

## 學習目標

- 辨識真實 RTL 檢查反覆出現的形態。
- 為 handshake、stable-until-accept 與仲裁撰寫 assertion。
- 將 one-hot 與 gray-code 不變式直接編碼為 property。
- 陳述 FIFO 的安全性：不溢位、不下溢、空時不讀。
- 以 assertion 防止資料出現 `X`，並了解 SVA 在 CDC 檢查上的侷限。

本章是一座樣式庫。每個樣式將一段實作好的 SVA 片段，與它所捕捉的設計意圖配對，讓你能將它搬進真實區塊並調整訊號名稱。所有片段都假設範圍內已有 `default clocking @(posedge clk)` 與 `default disable iff (!rst_n)`，因此為求聚焦，省略 clock 與 reset。

## 設計者 mental model

assertion pattern 是把常見 RTL contract 翻成 SVA 的 reusable translation。handshake、FIFO
boundary、one-hot state、no-unknown rule 會在很多 design 出現；每次都會回到同樣問題：什麼
trigger rule？什麼必須 stable？允許多少 latency？failure 應該代表什麼？

請把 pattern 當成 starting point，而不是萬用 macro。copy property 前，先用文字命名 protocol
rule，並選擇符合 block 的 clock、reset、latency、vacuity check。pattern 給 structure；design
context 才給 truth。

## Request / acknowledge handshake（請求／應答握手）

最常見的協定形態：請求必須在有界的視窗內得到回應。

```systemverilog
// Every request is acknowledged within 1..N cycles
property req_ack;
    $rose(req) |-> ##[1:N] ack;
endproperty
assert property (req_ack);
```

> **設計意圖。** 一個*終將*被回應的請求是活性（liveness）概念；給它一個真實的期限（`##[1:N]`），就把它變成 simulation 實際能讓它失敗的安全性檢查。請以協定的最差延遲為視窗界限。

## Request 在 acknowledge 前保持穩定

請求在被接受之前，不得被撤回或更改：

```systemverilog
// req holds steady from assertion until ack arrives
assert property ($rose(req) |-> req s_until ack);

// If a payload travels with the request, it must hold too
assert property ($rose(req) |-> $stable(addr) until ack);
```

「保持到被接受」正是讓接收方能依*自己*的步調 sampling 請求與其酬載的條件。少了它，發送方就可能在交易中途改動資料。

## Valid / ready 在被接受前保持穩定（stream 風格）

AXI-stream 風格的通道在 `valid && ready` 的週期完成傳輸。在那個接受週期之前，`valid` 必須維持高態，且資料不得改變：

```systemverilog
// Once valid is asserted without ready, it stays asserted and data holds
property vr_stable;
    (valid && !ready) |=> (valid && $stable(data));
endproperty
assert property (vr_stable);
```

> **設計意圖。** 這是 ready/valid stream 的核心契約：生產者在消費者取走前，不得撤回或變動已提供的一拍。一條 assertion 便編碼了整個握手的穩定性規則。

## One-hot 與 one-hot-zero 狀態

one-hot 訊號恰好帶有一個設定位元；one-hot-zero 則額外允許全零。這些是不變式，每個週期檢查，無需 antecedent：

```systemverilog
// FSM state register is strictly one-hot
assert property ($onehot(state));

// Grant bus is one-hot, or all-zero when idle
assert property ($onehot0(gnt));
```

錯誤的編碼——兩個狀態同時作用，或被破壞的 grant——會在它發生的那個週期失敗。每當「無任何作用」是合法的閒置條件時，`$onehot0` 就是正確的選擇。

## FIFO 安全性

FIFO 有三個經典的 safety property。各以「絕不能發生」的形式陳述。

```systemverilog
// No write into a full FIFO (would overflow)
assert property (wr_en |-> !full);

// No read from an empty FIFO (would underflow)
assert property (rd_en |-> !empty);

// Count never wraps past its bounds (depth = DEPTH)
assert property (count <= DEPTH);
assert property (!(full && empty));   // cannot be both at once
```

> **設計意圖。** 溢位與下溢會無聲地破壞資料，且在波形上難以察覺。化為 assertion 後，它們會在規則被打破的確切週期成為響亮、即時的失敗——這是 FIFO 上最有價值的單一檢查。

若推入與彈出在已滿或已空的 FIFO 上同時發生，count 必須維持在範圍內；界限 `count <= DEPTH` 加上各操作的防護，便涵蓋了這些角落情形。

## Gray-code 單一位元變化

gray 編碼的計數器（常是跨 clock domain 的 FIFO 指標）每步必須恰好改變一個位元。此檢查使用 `$past` 與 `$countones`：

```systemverilog
// At most one bit differs between consecutive gray values
assert property ($countones(gray ^ $past(gray)) <= 1);
```

> **設計意圖。** 將指標 gray 編碼的全部理由，就在於單一位元的變化能安全地跨 clock domainsampling。這條 assertion 驗證了同步器所依賴的 property；多位元的跳變代表編碼器壞了，CDC 不安全。

## 互斥與單一 grant 仲裁

仲裁器一次至多只能授予一個請求者。那就是 grant 向量上的 one-hot-zero，可改述為互斥：

```systemverilog
// At most one grant asserted
assert property ($onehot0(gnt));

// A grant implies a matching request (no spurious grant)
assert property ((gnt != '0) |-> (gnt & req) == gnt);
```

第一行禁止兩個同時的 grant；第二行禁止授予一個未曾請求的 port。兩者合起來釘住了仲裁器的核心契約。

## Pulse 與 level

某些控制訊號必須是單一週期的脈衝（pulse），而非持續的位準（level）。assertion 該訊號在下一週期回到低態：

```systemverilog
// 'start' is a one-cycle strobe, never held high two cycles
assert property (start |=> !start);
```

相反的意圖——必須持續的位準——則改用 `throughout` 或保持檢查。請陳明協定要求的是哪一種；將脈衝當成位準（或反之）是常見的整合錯誤。

## 訊號在 valid 時絕不為 X

當一拍為 valid 時，其酬載必須帶有真實資料，而非 `X` 或 `Z`。`$isunknown` 函式會標出任何未知位元：

```systemverilog
// While valid, data must be fully known (no X/Z)
assert property (valid |-> !$isunknown(data));
```

> **設計意圖。** valid 酬載上的 `X` 通常意味著未初始化的暫存器，或一條未連接的路徑滲入了資料——這是個真實的 bug，而 RTL 的 `X` 值原本可能透過樂觀或悲觀傳播將其掩蓋。這個檢查把無聲的 `X` 變成明確的失敗。

## CDC 意圖：一則說明，而非單一 assertion

跨 clock domain（clock-domain-crossing）的正確性，大多*並非*single-clock 的 SVA property。跨越邊界的資料，依定義相對於接收 clock 是不穩定的，因此對它做天真的同 clockassertion 不是無意義就是錯誤。SVA *能*陳述的，是 CDC 結構所依賴的意圖：

```systemverilog
// Gray pointer changes one bit at a time (sampled in the source domain)
assert property (@(posedge wr_clk) $countones(wptr_gray ^ $past(wptr_gray)) <= 1);
```

至於跨越本身——同步器深度、穩定時間、亞穩態線網上不得有組合邏輯——請使用專門的 CDC 工具，或在 `##` 邊界流動的 multiclock assertion（第 8 章）。將結構性 CDC 簽核視為獨立的工作項；以 SVA 釘住該結構所假設的*編碼*不變式。

## 常見陷阱

- **simulation 中的無界 handshake 檢查。** `req |-> s_eventually ack` 在有限時間內無法失敗。請使用有界視窗 `##[1:N]`。
- **忘記酬載穩定性。** 只檢查 `valid` 維持，卻不檢查 `data` 維持，會讓生產者變動已提供的一拍。請加上 `$stable(data)`。
- **在閒置合法處使用 `$onehot`。** 閒置時全零的 grant 匯流排需要 `$onehot0`，而非 `$onehot`。
- **對 CDC 線網做同 clockassertion。** 對不穩定訊號而言是無意義的。請檢查來源域的編碼不變式，並將穩定交給 CDC 流程。
- **混淆 pulse 與 level 意圖。** 決定協定要的是單一週期的脈衝還是持續的位準，並準確地 assertion 之。

## 小結

- Handshake：界定 acknowledge 的視窗，並要求請求（與酬載）在被接受前保持。
- Stream 通道：一經提供，`valid` 與 `data` 在 `ready` 取走該拍前保持穩定。
- One-hot 與 gray-code 不變式直接對應到 `$onehot`、`$onehot0` 與單一位元變化檢查。
- FIFO 安全性是三個「絕不」property：不溢位、不下溢、count 在範圍內。
- 以 `$isunknown` 防止 valid 酬載出現 `X`;將 CDC 穩定視為獨立流程，SVA 只用於該結構所假設的編碼不變式。

---

[← bind 與放置](09-binding-and-placement.md) · [目錄](../README.md) · [下一章：區域變數 →](11-local-variables.md)
