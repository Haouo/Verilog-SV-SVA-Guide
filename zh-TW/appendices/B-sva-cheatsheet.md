# 附錄 B · SVA 速查表

[← Verilog 與 SystemVerilog 對照](A-verilog-vs-sv.md) · [目錄](../README.md) · [下一篇：詞彙表 →](C-glossary.md)

本速查表是第三部所涵蓋 SVA 語法的密集參考卡。每一節均連結至深入說明該語法的章節。

---

## 取樣值函式

用於並行斷言（concurrent assertion）內部。所有值均取自斷言時脈的 **Preponed** 區。
→ [第三部 · 第 4 章](../part3-sva/04-boolean-layer.md)

| 函式 | 含義 | 簡短範例 |
|---|---|---|
| `$rose(e)` | 本週期 `e` 的 LSB 從 0 變為 1 | `$rose(req)` — req 剛被拉高 |
| `$fell(e)` | 本週期 `e` 的 LSB 從 1 變為 0 | `$fell(ack)` — ack 剛被拉低 |
| `$stable(e)` | `e` 與前一週期相比未改變 | `busy \|-> $stable(cfg)` |
| `$changed(e)` | `e` 與前一週期不同（`$stable` 的否定） | `!$changed(addr)` |
| `$past(e)` | `e` 一個週期前的取樣值 | `q == $past(d)` |
| `$past(e, n)` | `e` 恰好 `n` 個週期前的取樣值 | `out == $past(in, 3)` |
| `$onehot(e)` | `e` 恰好有一個位元為 1 | `$onehot(state)` |
| `$onehot0(e)` | `e` 最多有一個位元為 1 | `$onehot0(grant)` |
| `$countones(e)` | `e` 中為 1 的位元數量 | `$countones(active) == 2` |
| `$isunknown(e)` | `e` 的任意位元為 `x` 或 `z` | `!$isunknown(ctrl)` |

---

## 序列運算子

序列（sequence）描述跨越時脈週期的事件樣式。
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
| `s1 and s2` | 兩個序列從同一點開始，且都必須完成 | `req_a and req_b` |
| `s1 or s2` | 任一序列成立 | `(a ##1 b) or (c ##2 d)` |
| `s1 intersect s2` | 兩個序列都成立且在同一個週期結束 | `s1 intersect s2` |
| `e throughout s` | 在 `s` 的每個週期 `e` 均為真 | `valid throughout (a ##1 b)` |
| `s1 within s2` | `s1` 被包含（匹配）於 `s2` 之內 | `pulse within window` |
| `first_match(s)` | 只取 `s` 的最早一次匹配 | `first_match(a ##[1:5] b)` |

---

## 性質運算子

性質（property）將序列組合成可檢查的時序陳述。
→ [第三部 · 第 7 章](../part3-sva/07-properties.md)

### 蘊涵

| 語法 | 含義 | 備註 |
|---|---|---|
| `s \|-> p` | 重疊蘊涵：`s` 在本週期匹配，即於本週期開始檢查 `p` | 共用端點 |
| `s \|=> p` | 非重疊蘊涵：`s` 匹配後，於下一個週期開始檢查 `p` | `\|=>` ≡ `\|-> ##1` |

### 布林與時序連接詞

| 語法 | 含義 | 範例 |
|---|---|---|
| `not p` | 性質 `p` 的否定 | `not ($rose(err))` |
| `p and q` | 兩個性質都必須成立 | `p1 and p2` |
| `p or q` | 至少一個成立 | `p1 or p2` |
| `if (e) p` | 若 `e` 成立則 `p` 必須成立（否則空真通過） | `if (mode) p` |
| `if (e) p else q` | `e` 時檢查 `p`；否則檢查 `q` | |
| `nexttime p` | `p` 必須從下一個週期開始成立 | `nexttime (q == 0)` |
| `nexttime [n] p` | `p` 必須從 `n` 個週期後開始成立 | `nexttime [3] p` |
| `s_nexttime p` | 強式：必須到達終點 | |
| `always p` | `p` 在每個未來時間點均成立 | `always $onehot(state)` |
| `s_always [m:n] p` | 在有限窗口內的強式 always | |
| `eventually p` | `p` 在某個未來時間點成立（活性性質） | `eventually done` |
| `s_eventually p` | 強式 eventually — 保證到達終點 | |
| `p until q` | `p` 成立直到 `q` 成立（弱式 — `q` 不一定發生） | `busy until idle` |
| `p s_until q` | 強式 until — `q` 最終必須發生 | `busy s_until idle` |
| `p until_with q` | `p` 成立直到且包含 `q` 首次成立的那個週期 | |
| `p implies q` | 若 `p` 在此時間點成立，`q` 也必須成立 | |
| `p iff q` | 雙向蘊涵 | |

---

## 斷言陳述

→ [第三部 · 第 3 章](../part3-sva/03-assertion-kinds.md)

### 並行斷言陳述

每個時脈節拍都進行評估；結果由模擬器或形式化工具回報。

| 陳述 | 用途 | 典型放置位置 |
|---|---|---|
| `assert property (p)` | 驗證 `p` 成立；失敗視為錯誤 | RTL 模組、checker、bind |
| `assume property (p)` | 限制輸入；形式化工具視為公理 | 形式化環境 |
| `cover property (p)` | 記錄 `p` 至少被觀察到一次 | RTL 模組、checker |
| `restrict property (p)` | 僅供形式化工具：硬性約束（模擬無效果） | 形式化環境 |

語法樣式：
```systemverilog
label: assert property (@(posedge clk) disable iff (!rst_n) antecedent |-> consequent)
    else $error("message");
```

### 即時斷言陳述

程序式；在執行到達時立即評估，如同一般陳述。

| 陳述 | 時序區 | 用途 |
|---|---|---|
| `assert (expr)` | Observed 區 | 在 `always`、`initial`、task 內部 |
| `assert final (expr)` | Final 區 | 時間步結束時的檢查 |
| `assert #0 (expr)` | Postponed 區 | 延遲斷言：避免讀取瞬變值 |

---

## 時脈與 disable

→ [第三部 · 第 8 章](../part3-sva/08-clocking-and-reset.md)

| 語法 | 含義 | 範例 |
|---|---|---|
| `@(posedge clk)` 內嵌 | 單一斷言的時脈 | `assert property (@(posedge clk) p)` |
| `default clocking cb @(posedge clk); endclocking` | 模組範圍的預設時脈 | 每個斷言可省略時脈宣告 |
| `disable iff (expr)` | 當 `expr` 為真時（通常為重置期間）抑制斷言 | `disable iff (!rst_n)` |
| `$inferred_clock` | 從上下文推斷的時脈（在 `always_ff` 或 clocking block 內） | 鮮少明確撰寫 |

---

## bind

→ [第三部 · 第 9 章](../part3-sva/09-binding-and-placement.md)

```systemverilog
bind target_module assertion_module inst_name (
    .clk   (clk),
    .sig_a (sig_a)
);
```

將斷言模組附加至 `target_module`，無需修改其原始碼。

---

[← Verilog 與 SystemVerilog 對照](A-verilog-vs-sv.md) · [目錄](../README.md) · [下一篇：詞彙表 →](C-glossary.md)
