# 附錄 D · 參考文獻

[← 詞彙表](C-glossary.md) · [回到目錄](../README.md)

本附錄是一份帶注釋的書目，將本指南三個部分的內容對應至其規範來源與重要補充文獻。

---

## 規範標準

**IEEE Std 1364-2005 — IEEE Standard for Verilog Hardware Description Language.**
Institute of Electrical and Electronics Engineers, 2006.
*第一部的規範性依據。本指南所有 Verilog 的語法、語意與模擬行為，均依此標準定義。*

**IEEE Std 1800-2023 — IEEE Standard for SystemVerilog — Unified Hardware Design,
Specification, and Verification Language.**
Institute of Electrical and Electronics Engineers, 2023.
*第二部與第三部的規範性依據；取代 IEEE 1800-2017。斷言語意、取樣值模型、序列與性質代數、時脈區塊（clocking block）以及 checker，均在此標準中規定。*

---

## SVA 深度參考

**Cohen, Ben; Venkataramanan, Srinivasan; Kumari, Ajeetha 著。**
*SystemVerilog Assertions Handbook.* 第 4 版。Createspace, 2015。
*目前最完整的 SVA 實務著作。以大量實例涵蓋完整斷言語言，並提供方法論指引與模擬/形式化工具使用方式。推薦給想在本指南範圍之外更深入學習的設計者。*

**Cohen, Ben; Venkataramanan, Srinivasan; Kumari, Ajeetha; Piper, Lisa 著。**
*A Practical Guide to Adopting the Universal Verification Methodology (UVM).*
涵蓋 SVA 在驗證環境中的整合方式，可補充第三部的斷言方法論。

**《SystemVerilog Assertions 应用指南》**
*中文實務 SVA 參考書，涵蓋各種斷言編碼樣式。對偏好以中文為主要資料來源的讀者，可搭配第三部一起使用。*

---

## 可合成的 SystemVerilog

**Sutherland, Stuart。**
"Synthesizable SystemVerilog: Taming the Beast."
*SNUG（Synopsys Users Group）研討會論文，2013。*
*簡明扼要地說明哪些 SystemVerilog 語法可合成、哪些不行，以工具為導向 — 在實際生產環境中使用第二部功能之前的必讀文獻。*

**Sutherland, Stuart; Mills, Don。**
"Verilog and SystemVerilog Gotchas: 101 Common Coding Errors and How to Avoid Them."
*SNUG 研討會論文。*
*涵蓋設計者從 Verilog 移轉至 SystemVerilog 時最常犯的錯誤，直接對應第二部各章的陷阱小節。*

---

## 設計意圖與 ABV 方法論

**Bening, Lionel; Foster, Harry D. 著。**
*Principles of Verifiable RTL Design: A Functional Coding Style Supporting
Verification Processes in Verilog.* 第 2 版。Kluwer Academic, 2001。
*以可驗證性為核心的 RTL 撰寫方式的奠基著作。書中介紹的設計意圖（design intent）原則，正是第三部所採用的基於斷言的驗證（ABV）方法論的思想基礎。*

---

## 驗證面向（本指南範圍外）

**Spear, Chris; Tumbush, Greg 著。**
*SystemVerilog for Verification: A Guide to Learning the Testbench Language Features.*
第 3 版。Springer, 2012。
*涵蓋受約束隨機驗證（constrained-random verification）、覆蓋率驅動驗證以及 SystemVerilog 的類別型物件導向功能。本指南刻意省略語言的驗證面向；對需要撰寫 testbench 的設計者而言，Spear & Tumbush 是推薦的下一步讀物。*

---

## 延伸閱讀

- **Accellera** 官網（accellera.org）保存了早期的 SystemVerilog 語言參考手冊及原始捐獻文件，有助於了解語言的演進脈絡。
- **SNUG**（snug-universal.org）與 **DVCon** 的論文集收錄了大量關於 SVA 方法論、形式化驗證流程和可合成撰寫風格的實務論文，註冊後大多可免費取得。
- 各工具廠商（Synopsys、Cadence、Siemens EDA、Aldec）均發布針對其模擬器與形式化引擎的應用注釋；當標準語意與工具特定行為有差異時，應查閱這些文件。

---

[← 詞彙表](C-glossary.md) · [回到目錄](../README.md)
