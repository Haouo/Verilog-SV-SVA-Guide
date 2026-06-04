# 附錄 C · 詞彙表

[← SVA 速查表](B-sva-cheatsheet.md) · [目錄](../README.md) · [下一篇：參考文獻 →](D-references.md)

完整的雙語術語表位於儲存庫根目錄：
**[../../GLOSSARY.md](../../GLOSSARY.md)**

該檔案是英文版與繁體中文版所有術語譯名的唯一來源。在任何章節引入新譯名之前，請先在那裡登錄。

## 如何使用本附錄

本附錄只是指回那份共用的雙語詞彙表。請把詞彙表當成一份風格約定：當某個術語需要中文譯名時，就一律使用同一個譯名；當某個英文術語本來就是 RTL 裡自然會用的說法時，就在行文中保留英文。

---

## 快速參考 — 八個核心術語

以下八個術語幾乎每一章都會出現。這裡的譯注只是為了方便查閱，正式條目請見 GLOSSARY.md。

| 術語 | 繁體中文 | 簡要定義 |
|---|---|---|
| design intent | 設計意圖 | 硬體*應該*做什麼，也就是設計者腦中的模型，以明確的方式陳述出來。 |
| RTL (Register-Transfer Level) | 暫存器轉移層級 | 描述可合成硬體的抽象層級：每個 clock 週期對暫存器執行運算，並傳遞資料。 |
| assertion | 斷言 | 對預期行為的可驗證陳述，違反時由 simulator 或 formal tool 回報。 |
| property | 性質 | 橫跨一個或多個 clock 週期的時序陳述，在特定時間點可能成立或失敗。 |
| sequence | 序列 | 描述橫跨一個或多個 clock 週期的訊號事件樣式，是組成 property 的建構單元。 |
| implication | 蘊涵 | `\|->`（重疊）或 `\|=>`（非重疊）運算子：「若 antecedent 匹配，consequent 就必須成立。」 |
| vacuity / vacuous pass | 空真 / 空泛成立 | 當 assertion 的 antecedent 從未為真時，assertion 沒做任何實質檢查就通過了。用 cover property 可以診斷出這種情況。 |
| formal verification | 形式化驗證 | 不靠 simulation，而以數學方法證明 property 在所有合法輸入與所有可達狀態下都成立。 |

---

[← SVA 速查表](B-sva-cheatsheet.md) · [目錄](../README.md) · [下一篇：參考文獻 →](D-references.md)
