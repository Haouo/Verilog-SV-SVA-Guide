# 附錄 C · 詞彙表

[← SVA 速查表](B-sva-cheatsheet.md) · [目錄](../README.md) · [下一篇：參考文獻 →](D-references.md)

完整的雙語術語表位於儲存庫根目錄：
**[../../GLOSSARY.md](../../GLOSSARY.md)**

該檔案是英文版與繁體中文版所有術語譯名的唯一來源。在任何章節引入新譯名之前，
請先在該處登錄。

## 如何使用這個 appendix

這個 appendix 指回 shared bilingual glossary。請把 glossary 當成 style contract：當一個 term 需要
中文 gloss 時，就一致使用同一個 gloss；當 English term 才是 RTL 裡自然使用的詞，就在 prose 中
保留英文。

---

## 快速參考 — 八個核心術語

以下八個術語幾乎出現在每一章中。此處的譯注僅為便利查閱；正式條目請見 GLOSSARY.md。

| 術語 | 繁體中文 | 簡要定義 |
|---|---|---|
| design intent | 設計意圖 | 硬體*應該*要做什麼 — 設計者腦中的模型，以明確方式陳述。 |
| RTL (Register-Transfer Level) | 暫存器轉移層級 | 描述可合成硬體的抽象層級：每個 clock 週期對暫存器執行運算並傳遞資料。 |
| assertion | 斷言 | 對預期行為的可驗證陳述。違反時由 simulator 或 formal tool 回報。 |
| property | 性質 | 跨越一個或多個 clock 週期的時序陳述，在特定時間點可成立或失敗。 |
| sequence | 序列 | 描述跨越一個或多個 clock 週期的信號事件樣式，作為 property 的建構單元。 |
| implication | 蘊涵 | `\|->`（重疊）或 `\|=>`（非重疊）運算子：「若 antecedent 匹配，consequent 必須成立。」 |
| vacuity / vacuous pass | 空真 / 空泛成立 | 當 assertion 的 antecedent 從未為真時，assertion 在不進行任何實質檢查的情況下通過。使用 cover property 可診斷此問題。 |
| formal verification | 形式化驗證 | 以數學方法證明 property 在所有合法輸入及所有可達狀態下均成立，無需 simulation。 |

---

[← SVA 速查表](B-sva-cheatsheet.md) · [目錄](../README.md) · [下一篇：參考文獻 →](D-references.md)
