# 導論

[← 目錄](README.md) · [下一章：模組與階層 →](part1-verilog/01-modules-and-hierarchy.md)

## 學習目標

- 了解本指南的讀者對象，以及它假設你已具備的知識。
- 理解為何寫 assertion 是設計者的職責，而不只是驗證工程師的工作。
- 認識三個部分如何銜接，以及該如何閱讀。

## 設計者的心智模型

把這本指南看成你身為設計者平時就在做的三件事之間的橋樑：描述硬體結構、挑選工具能正確
解讀的寫法，以及寫下硬體必須遵守的承諾。前兩者由 Verilog 與 SystemVerilog 負責，第三者
則交給 SVA。讀到每個語法構件時，最該養成的習慣就是問自己：「我現在正在把哪一條硬體事實
講清楚？」

這些章節刻意不走鑽研語法條文的路線，而是帶你從 RTL 語法一路走到設計意圖。像位元寬度規則
或取樣值規則這類細節看似微不足道，其實都是日後除錯的分界線：現在把心智模型理清楚，之後
讀波形時就不必靠猜。

## 本指南的讀者對象

本指南寫給數位設計工程師：撰寫 RTL（Register-Transfer Level，暫存器轉移層級）程式碼、
並交由合成工具轉成邏輯閘的人。它假設你已了解數位邏輯，包括組合與循序電路、clock、
reset，以及基本的合成流程，不會從零教起邏輯設計。它教的是設計者用來描述邏輯的語言，
以及設計者用來陳述「邏輯該做什麼」的 assertion 語言。

本指南分為三個部分：

1. **Verilog 設計** — Verilog 中可合成的核心。
2. **SystemVerilog 設計** — 讓 RTL 更清晰、更安全的 SystemVerilog 功能。
3. **SystemVerilog Assertions（SVA）** — 本指南的核心，深入探討。

## 為何設計者要寫 assertion

設計者掌握著 RTL 本身看不出來的知識。你知道每個 request 最終都必須收到 acknowledge、
某個狀態暫存器是 one-hot、某個 FIFO 永遠不可溢位（overflow）。這些事實就是
*設計意圖（design intent）*。它們存在你的腦中、規格書裡，或一句註解中，而這些都是
工具無法檢查的地方。

assertion 把設計意圖搬進程式碼，化為 simulator 或 formal tool 每個週期都能檢查的形式。
日後設計一旦違反了這個意圖，無論是在你自己的 simulation、同事的 simulation，或區塊層級的
回歸測試中，assertion 都會在失效的當下、當地觸發，而不是等到三個模組之外、症狀才浮現的地方。

這正是 SVA 屬於設計者的原因。你才是知道意圖的人。在撰寫 RTL 的同時把意圖寫下來，
能趁記憶最清晰時把它記錄下來，並轉為永久、可被機器檢查的契約。

> **設計意圖。** RTL 描述硬體*如何*行為；assertion 描述對該行為而言*什麼必須為真*。
> 兩者並用遠比單獨使用任一者更強：RTL 可能出錯，而 assertion 會指出這個錯誤。

## 本指南不涵蓋的內容

這是一本設計指南，不是驗證課程。建構測試平台（testbench）、UVM、基於類別的隨機化
（randomization），以及 coverage 方法論都是各自有完整文獻的大主題。我們只在
設計者需要辨識它們時順帶提及，例如知道在 formal flow 中 `assume` 該放在哪裡。唯一深入
探討的驗證相關主題是 SVA，因為它就是設計意圖。

## 如何閱讀本指南

若這些語言對你是全新的，請依序閱讀。第一部建立 Verilog 基礎，第二部加入 SystemVerilog
的設計功能，第三部則運用兩者以 assertion 表達意圖。

若你已能撰寫 RTL，可略讀第一、二部以查找你會用到的特定語法，再把時間花在第三部。

每一章遵循相同結構：學習目標、概念說明、簡短的示意程式碼、設計意圖提示、常見陷阱，
以及小結。程式碼僅為示意，目的是凸顯重點，而非構成可執行的專案。

## 慣例

- Verilog 程式碼以 `verilog` 標示；SystemVerilog 以 `systemverilog` 標示。
- 技術名詞保留英文，首次出現時連結至[詞彙表](../GLOSSARY.md)。
- 參考標準列於[附錄 D](appendices/D-references.md)：Verilog 依據 IEEE 1364-2005，
  SystemVerilog 與 SVA 依據 IEEE 1800-2023。

## 小結

- 本指南寫給已具備數位邏輯基礎的 RTL 設計者。
- 內容涵蓋 Verilog、SystemVerilog 設計子集，並深入 SVA。
- assertion 是設計者的工具，因為設計者掌握意圖。
- 測試平台與驗證方法論刻意不在範圍內。

---

[← 目錄](README.md) · [下一章：模組與階層 →](part1-verilog/01-modules-and-hierarchy.md)
