# 附錄 B · SVA 速查表

[← Verilog 與 SystemVerilog 對照](A-verilog-vs-sv.md) · [目錄](../README.md) · [下一篇：詞彙表 →](C-glossary.md)

本速查表是第三部所涵蓋 SVA 語法的密集參考卡。每一節均連結至深入說明該語法的章節。

## 如何使用這個 appendix

請在已經理解 construct 背後 intent 之後，再使用這份 cheat-sheet。它是為 recall 設計的，不是
first learning。如果某一列讓你覺得意外，先沿著 chapter link 回去重建 timing model，再把 syntax
用在 real RTL 或 formal environment。

最安全的 workflow 是 sentence first, operator second：先用文字 state protocol rule，再選 sampled
fact 或 sequence shape，最後用這個 appendix 確認 spelling。SVA syntax 很 compact；design sentence
讓它保持 honest。

---

## sampled value 函式

用於 concurrent assertion內部。所有值均取自 assertion clock 的 **Preponed** 區。
→ [第三部 · 第 4 章](../part3-sva/04-boolean-layer.md)

| 函式 | 含義 | 簡短範例 |
|---|---|---|
| `$rose(e)` | 本週期 `e` 的 LSB 從 0 變為 1 | `$rose(req)` — req 剛被拉高 |
| `$fell(e)` | 本週期 `e` 的 LSB 從 1 變為 0 | `$fell(ack)` — ack 剛被拉低 |
| `$stable(e)` | `e` 與前一週期相比未改變 | `busy \|-> $stable(cfg)` |
| `$changed(e)` | `e` 與前一週期不同（`$stable` 的否定） | `!$changed(addr)` |
| `$past(e)` | `e` 一個週期前的 sampled value | `q == $past(d)` |
| `$past(e, n)` | `e` 恰好 `n` 個週期前的 sampled value | `out == $past(in, 3)` |
| `$onehot(e)` | `e` 恰好有一個位元為 1 | `$onehot(state)` |
| `$onehot0(e)` | `e` 最多有一個位元為 1 | `$onehot0(grant)` |
| `$countones(e)` | `e` 中為 1 的位元數量 | `$countones(active) == 2` |
| `$isunknown(e)` | `e` 的任意位元為 `x` 或 `z` | `!$isunknown(ctrl)` |

---

## sequence operation 子

sequence 描述跨越 clock 週期的事件樣式。
→ [第三部 · 第 5 章](../part3-sva/05-sequences-basics.md)、[第 6 章](../part3-sva/06-sequence-operations.md)

### 延遲運算子

| 語法 | 含義 | 範例 |
|---|---|---|
| `s1 ##n s2` | `s1` 之後恰好 `n` 個週期 `s2` | `req ##1 gnt` |
| `s1 ##[m:n] s2` | `s1` 之後 `m` 至 `n` 個週期 `s2` | `req ##[1:4] gnt` |
| `s1 ##[*] s2` | `s1` 之後 0 個或更多週期 `s2`（等同 `##[0:$]`） | `start ##[*] done` |
| `s1 ##[+] s2` | `s1` 之後 1 個或更多週期 `s2`（等同 `##[1:$]`） | `req ##[+] ack` |

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
| `s1 and s2` | 兩個 sequence 從同一點開始，且都必須完成 | `req_a and req_b` |
| `s1 or s2` | 任一 sequence 成立 | `(a ##1 b) or (c ##2 d)` |
| `s1 intersect s2` | 兩個 sequence 都成立且在同一個週期結束 | `s1 intersect s2` |
| `e throughout s` | 在 `s` 的每個週期 `e` 均為真 | `valid throughout (a ##1 b)` |
| `s1 within s2` | `s1` 被包含（匹配）於 `s2` 之內 | `pulse within window` |
| `first_match(s)` | 只取 `s` 的最早一次匹配 | `first_match(a ##[1:5] b)` |

---

## property operator

property 將 sequence 組合成可檢查的時序陳述。
→ [第三部 · 第 7 章](../part3-sva/07-properties.md)

### implication

| 語法 | 含義 | 備註 |
|---|---|---|
| `s \|-> p` | overlapping implication：`s` 在本週期匹配，即於本週期開始檢查 `p` | 共用端點 |
| `s \|=> p` | 非 overlapping implication：`s` 匹配後，於下一個週期開始檢查 `p` | `\|=>` ≡ `\|-> ##1` |

### 布林與時序連接詞

| 語法 | 含義 | 範例 |
|---|---|---|
| `not p` | property `p` 的否定 | `not ($rose(err))` |
| `p and q` | 兩個 property 都必須成立 | `p1 and p2` |
| `p or q` | 至少一個成立 | `p1 or p2` |
| `if (e) p` | 若 `e` 成立則 `p` 必須成立（否則 vacuous pass） | `if (mode) p` |
| `if (e) p else q` | `e` 時檢查 `p`；否則檢查 `q` | |
| `nexttime p` | `p` 必須從下一個週期開始成立 | `nexttime (q == 0)` |
| `nexttime [n] p` | `p` 必須從 `n` 個週期後開始成立 | `nexttime [3] p` |
| `s_nexttime p` | 強式：必須到達終點 | |
| `always p` | `p` 在每個未來時間點均成立 | `always $onehot(state)` |
| `s_always [m:n] p` | 在有限窗口內的強式 always | |
| `eventually p` | `p` 在某個未來時間點成立（liveness property） | `eventually done` |
| `s_eventually p` | 強式 eventually — 保證到達終點 | |
| `p until q` | `p` 成立直到 `q` 成立（弱式 — `q` 不一定發生） | `busy until idle` |
| `p s_until q` | 強式 until — `q` 最終必須發生 | `busy s_until idle` |
| `p until_with q` | `p` 成立直到且包含 `q` 首次成立的那個週期 | |
| `p implies q` | 若 `p` 在此時間點成立，`q` 也必須成立 | |
| `p iff q` | 雙向 implication | |

---

## assertion 陳述

→ [第三部 · 第 3 章](../part3-sva/03-assertion-kinds.md)

### concurrent assertion 陳述

每個 clock 節拍都進行評估；結果由 simulator 或 formal tool 回報。

| 陳述 | 用途 | 典型放置位置 |
|---|---|---|
| `assert property (p)` | 驗證 `p` 成立；失敗視為錯誤 | RTL 模組、checker、bind |
| `assume property (p)` | 限制輸入；formal tool 視為公理 | formal環境 |
| `cover property (p)` | 記錄 `p` 至少被觀察到一次 | RTL 模組、checker |
| `restrict property (p)` | 僅供 formal tool：硬性約束（simulation 無效果） | formal環境 |

語法樣式：
```systemverilog
label: assert property (@(posedge clk) disable iff (!rst_n) antecedent |-> consequent)
    else $error("message");
```

### immediate assertion 陳述

程序式；在執行到達時立即評估，如同一般陳述。

| 陳述 | 時序區 | 用途 |
|---|---|---|
| `assert (expr)` | Observed 區 | 在 `always`、`initial`、task 內部 |
| `assert final (expr)` | Final 區 | 時間步結束時的檢查 |
| `assert #0 (expr)` | Postponed 區 | deferred assertion：避免讀取瞬變值 |

---

## clock 與 disable

→ [第三部 · 第 8 章](../part3-sva/08-clocking-and-reset.md)

| 語法 | 含義 | 範例 |
|---|---|---|
| `@(posedge clk)` 內嵌 | 單一 assertion 的 clock | `assert property (@(posedge clk) p)` |
| `default clocking cb @(posedge clk); endclocking` | 模組範圍的預設 clock | 每個 assertion 可省略 clock 宣告 |
| `disable iff (expr)` | 當 `expr` 為真時（通常為 reset 期間）抑制 assertion | `disable iff (!rst_n)` |
| `$inferred_clock` | 從上下文推斷的 clock（在 `always_ff` 或 clocking block 內） | 鮮少明確撰寫 |

---

## bind

→ [第三部 · 第 9 章](../part3-sva/09-binding-and-placement.md)

```systemverilog
bind target_module assertion_module inst_name (
    .clk   (clk),
    .sig_a (sig_a)
);
```

將 assertion module 附加至 `target_module`，無需修改其原始碼。

---

[← Verilog 與 SystemVerilog 對照](A-verilog-vs-sv.md) · [目錄](../README.md) · [下一篇：詞彙表 →](C-glossary.md)
