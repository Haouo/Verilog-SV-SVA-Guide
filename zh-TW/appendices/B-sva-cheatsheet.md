# 附錄 B · SVA 速查表

[← Verilog 與 SystemVerilog 對照](A-verilog-vs-sv.md) · [目錄](../README.md) · [下一篇：詞彙表 →](C-glossary.md)

本速查表是第三部所涵蓋 SVA 語法的密集參考卡。每一節都連結到深入說明該語法的章節。

## 如何使用本附錄

請在已經理解某個語法背後的設計意圖之後，再來查這份速查表。它是為了喚起記憶而設計的，不是初學的入口。如果某一列讓你覺得意外，先沿著章節連結回去重建 timing model，再把該語法用在實際的 RTL 或 formal environment 上。

最安全的工作流程是「先寫句子，再選運算子」：先用文字把 protocol 規則說清楚，接著選出要用的 sampled value 或 sequence 形狀，最後才用本附錄確認確切寫法。SVA 語法很精簡，先寫清楚這句設計敘述，才能避免語法看似正確、意圖卻已經偏掉。

---

## sampled value 函式

用在 concurrent assertion 內部。所有值都取自 assertion clock 的 **Preponed** 區。
→ [第三部 · 第 4 章](../part3-sva/04-boolean-layer.md)

| 函式 | 含義 | 簡短範例 |
|---|---|---|
| `$rose(e)` | 本週期 `e` 的 LSB 從 0 變為 1 | `$rose(req)` — req 剛被拉高 |
| `$fell(e)` | 本週期 `e` 的 LSB 從 1 變為 0 | `$fell(ack)` — ack 剛被拉低 |
| `$stable(e)` | `e` 與前一週期相比未改變 | `busy \|-> $stable(cfg)` |
| `$changed(e)` | `e` 與前一週期不同（`$stable` 的否定） | `!$changed(addr)` |
| `$past(e)` | `e` 在前一個週期的 sampled value | `q == $past(d)` |
| `$past(e, n)` | `e` 在恰好 `n` 個週期前的 sampled value | `out == $past(in, 3)` |
| `$onehot(e)` | `e` 恰好有一個位元為 1 | `$onehot(state)` |
| `$onehot0(e)` | `e` 最多有一個位元為 1 | `$onehot0(grant)` |
| `$countones(e)` | `e` 中為 1 的位元數量 | `$countones(active) == 2` |
| `$isunknown(e)` | `e` 的任意位元為 `x` 或 `z` | `!$isunknown(ctrl)` |

---

## sequence operator

sequence 描述橫跨多個 clock 週期的事件樣式。
→ [第三部 · 第 5 章](../part3-sva/05-sequences-basics.md)、[第 6 章](../part3-sva/06-sequence-operations.md)

### 延遲運算子

| 語法 | 含義 | 範例 |
|---|---|---|
| `s1 ##n s2` | `s1` 之後恰好過 `n` 個週期出現 `s2` | `req ##1 gnt` |
| `s1 ##[m:n] s2` | `s1` 之後過 `m` 到 `n` 個週期出現 `s2` | `req ##[1:4] gnt` |
| `s1 ##[*] s2` | `s1` 之後過 0 個或更多週期出現 `s2`（等同 `##[0:$]`） | `start ##[*] done` |
| `s1 ##[+] s2` | `s1` 之後過 1 個或更多週期出現 `s2`（等同 `##[1:$]`） | `req ##[+] ack` |

### 重複運算子

| 語法 | 含義 | 範例 |
|---|---|---|
| `e [*n]` | `e` 連續為真恰好 `n` 個週期 | `valid [*3]` |
| `e [*m:n]` | `e` 連續為真 `m` 至 `n` 個週期 | `busy [*1:8]` |
| `e [*]` | `e` 連續為真 0 個或更多週期 | `stall [*]` |
| `e [+]` | `e` 連續為真 1 個或更多週期 | `hold [+]` |
| `e [->n]` | `e` 非連續地出現恰好 `n` 次（goto 重複） | `ack [->1]` |
| `e [=n]` | `e` 恰好出現 `n` 次，無連續要求（非連續重複） | `err [=2]` |

### 組合運算子

| 語法 | 含義 | 範例 |
|---|---|---|
| `s1 and s2` | 兩個 sequence 從同一點起算，且都必須完成 | `req_a and req_b` |
| `s1 or s2` | 任一個 sequence 成立即可 | `(a ##1 b) or (c ##2 d)` |
| `s1 intersect s2` | 兩個 sequence 都成立，且在同一個週期結束 | `s1 intersect s2` |
| `e throughout s` | `s` 橫跨的每個週期 `e` 都為真 | `valid throughout (a ##1 b)` |
| `s1 within s2` | `s1` 整段都落在 `s2` 之內 | `pulse within window` |
| `first_match(s)` | 只取 `s` 最早的那一次匹配 | `first_match(a ##[1:5] b)` |

---

## property operator

property 把 sequence 組合成可檢查的時序陳述。
→ [第三部 · 第 7 章](../part3-sva/07-properties.md)

### implication

| 語法 | 含義 | 備註 |
|---|---|---|
| `s \|-> p` | overlapping implication：`s` 在本週期結束處匹配，就從本週期開始檢查 `p` | 共用同一個端點 |
| `s \|=> p` | non-overlapping implication：`s` 匹配後，從下一個週期開始檢查 `p` | `\|=>` ≡ `\|-> ##1` |

### 布林與時序連接詞

| 語法 | 含義 | 範例 |
|---|---|---|
| `not p` | property `p` 的否定 | `not ($rose(err))` |
| `p and q` | 兩個 property 都必須成立 | `p1 and p2` |
| `p or q` | 至少一個成立即可 | `p1 or p2` |
| `if (e) p` | `e` 成立時 `p` 必須成立（不成立則 vacuous pass） | `if (mode) p` |
| `if (e) p else q` | `e` 成立時檢查 `p`，否則檢查 `q` | |
| `nexttime p` | `p` 必須從下一個週期起成立 | `nexttime (q == 0)` |
| `nexttime [n] p` | `p` 必須從 `n` 個週期後起成立 | `nexttime [3] p` |
| `s_nexttime p` | 強式：終點一定要到達 | |
| `always p` | `p` 在未來每個時間點都成立 | `always $onehot(state)` |
| `s_always [m:n] p` | 限定有限窗口的強式 always | |
| `eventually [m:n] p` | `p` 在窗口內某處成立（弱式一定要有界） | `eventually [1:8] done` |
| `s_eventually p` | 強式 eventually：`p` 最終一定要成立（可以無界） | |
| `p until q` | `p` 一直成立到 `q` 成立為止（弱式：`q` 不一定會發生） | `busy until idle` |
| `p s_until q` | 強式 until：`q` 最終一定要發生 | `busy s_until idle` |
| `p until_with q` | `p` 一直成立到 `q` 首次成立的那個週期，且包含該週期 | |
| `p implies q` | `p` 在此時間點成立時，`q` 也必須成立 | |
| `p iff q` | 雙向蘊涵 | |

---

## assertion 陳述

→ [第三部 · 第 3 章](../part3-sva/03-assertion-kinds.md)

### concurrent assertion 陳述

每個 clock 節拍都會評估一次，結果由 simulator 或 formal tool 回報。

| 陳述 | 用途 | 典型放置位置 |
|---|---|---|
| `assert property (p)` | 驗證 `p` 成立，失敗即視為錯誤 | RTL 模組、checker、bind |
| `assume property (p)` | 約束輸入，formal tool 將其視為公理 | formal environment |
| `cover property (p)` | 記錄 `p` 至少被觀察到一次 | RTL 模組、checker |
| `restrict property (p)` | 只給 formal tool 用的硬性約束（在 simulation 下無作用） | formal environment |

語法樣式：
```systemverilog
label: assert property (@(posedge clk) disable iff (!rst_n) antecedent |-> consequent)
    else $error("message");
```

### immediate assertion 陳述

屬於程序式語法，執行流程一到就立即評估，和一般陳述一樣。

| 陳述 | 時序區 | 用途 |
|---|---|---|
| `assert (expr)` | Active 區（行內，執行流程一到就評估） | 用在 `always`、`initial`、task 內部 |
| `assert final (expr)` | Reactive 區 | 在 time step 結束時檢查 |
| `assert #0 (expr)` | Observed 區 | deferred assertion：避免讀到瞬變值 |

---

## clock 與 disable

→ [第三部 · 第 8 章](../part3-sva/08-clocking-and-reset.md)

| 語法 | 含義 | 範例 |
|---|---|---|
| `@(posedge clk)` 內嵌 | 替單一 assertion 指定 clock | `assert property (@(posedge clk) p)` |
| `default clocking cb @(posedge clk); endclocking` | 整個模組共用的預設 clock | 每個 assertion 都可省略 clock 宣告 |
| `disable iff (expr)` | `expr` 為真時（通常是 reset 期間）抑制 assertion | `disable iff (!rst_n)` |
| `$inferred_clock` | 從 assertion 所在的上下文推斷 clock（例如 `default clocking` 或外圍的程序區塊） | 很少明確寫出 |

---

## bind

→ [第三部 · 第 9 章](../part3-sva/09-binding-and-placement.md)

```systemverilog
bind target_module assertion_module inst_name (
    .clk   (clk),
    .sig_a (sig_a)
);
```

把 assertion module 掛到 `target_module` 上，不必改動它的原始碼。

---

[← Verilog 與 SystemVerilog 對照](A-verilog-vs-sv.md) · [目錄](../README.md) · [下一篇：詞彙表 →](C-glossary.md)
