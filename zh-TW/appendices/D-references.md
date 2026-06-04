# 附錄 D · 參考文獻

[← 詞彙表](C-glossary.md) · [回到目錄](../README.md)

本附錄是一份帶注釋的書目，把本指南三個部分的內容對應到各自的規範來源與重要補充文獻。

## 如何使用本附錄

參考文獻是本指南技術主張的後盾。語言規則以標準為準，設計實務、範例與詮釋則可參考書籍或論文。隨著各章內容寫得愈來愈詳細，對應的佐證來源也應該在本附錄裡一併呈現出來。

---

## 規範標準

**IEEE Std 1364-2005 — IEEE Standard for Verilog Hardware Description Language.**
Institute of Electrical and Electronics Engineers, 2006.
*第一部的規範依據。本指南所有 Verilog 的語法、語意與 simulation 行為，都以此標準為準。*

**IEEE Std 1800-2023 — IEEE Standard for SystemVerilog — Unified Hardware Design,
Specification, and Verification Language.**
Institute of Electrical and Electronics Engineers, 2023.
*第二部與第三部的規範依據，取代 IEEE 1800-2017。assertion 語意、sampled value 模型、sequence 與 property 代數、clocking block 以及 checker，都由此標準規定。*

---

## SVA 深度參考

**Cohen, Ben; Venkataramanan, Srinivasan; Kumari, Ajeetha 著。**
*SystemVerilog Assertions Handbook.* 第 4 版。Createspace, 2015。
*目前最完整的 SVA 實務著作。以大量實例涵蓋整套 assertion language，並給出方法論指引以及 simulation 與 formal tool 的使用方式。想在本指南範圍之外更深入鑽研的設計者，推薦從這本入手。*

**Cohen, Ben; Venkataramanan, Srinivasan; Kumari, Ajeetha; Piper, Lisa 著。**
*A Practical Guide to Adopting the Universal Verification Methodology (UVM).*
說明 SVA 如何整合進驗證環境，可補充第三部的 assertion methodology。

**《SystemVerilog Assertions 应用指南》**
*中文的 SVA 實務參考書，涵蓋各種 assertion 編碼樣式。偏好以中文為主要資料來源的讀者，可搭配第三部一起閱讀。*

---

## 可合成的 SystemVerilog

**Sutherland, Stuart。**
"Synthesizable SystemVerilog: Taming the Beast."
*SNUG（Synopsys Users Group）研討會論文，2013。*
*以工具為導向，簡明扼要地說明哪些 SystemVerilog 語法可合成、哪些不行。在實際生產環境中使用第二部的功能之前，這是一份必讀文獻。*

**Sutherland, Stuart; Mills, Don。**
"Verilog and SystemVerilog Gotchas: 101 Common Coding Errors and How to Avoid Them."
*SNUG 研討會論文。*
*整理設計者從 Verilog 轉到 SystemVerilog 時最常犯的錯誤，直接對應第二部各章的陷阱小節。*

---

## 設計意圖與 ABV 方法論

**Bening, Lionel; Foster, Harry D. 著。**
*Principles of Verifiable RTL Design: A Functional Coding Style Supporting
Verification Processes in Verilog.* 第 2 版。Kluwer Academic, 2001。
*以可驗證性為核心來撰寫 RTL 的奠基著作。書中提出的設計意圖（design intent）原則，正是第三部所採用的 Assertion-Based Verification（ABV）方法論的思想基礎。*

---

## 驗證面向（本指南範圍外）

**Spear, Chris; Tumbush, Greg 著。**
*SystemVerilog for Verification: A Guide to Learning the Testbench Language Features.*
第 3 版。Springer, 2012。
*涵蓋受約束隨機驗證（constrained-random verification）、coverage 驅動驗證，以及 SystemVerilog 以類別為基礎的物件導向功能。本指南刻意略去語言的驗證面向，對需要撰寫 testbench 的設計者來說，Spear & Tumbush 是推薦的下一步讀物。*

---

## 延伸閱讀

- **Accellera** 官網（accellera.org）保存了早期的 SystemVerilog 語言參考手冊與原始捐獻文件，有助於了解語言的演進脈絡。
- **SNUG**（snug-universal.org）與 **DVCon** 的論文集收錄了大量實務論文，主題涵蓋 SVA 方法論、formal verification 流程與可合成的撰寫風格，註冊後大多可免費取得。
- 各家工具廠商（Synopsys、Cadence、Siemens EDA、Aldec）都會針對自家的 simulator 與 formal engine 發布應用注釋。當標準語意與工具特定行為出現差異時，應查閱這些文件。

---

[← 詞彙表](C-glossary.md) · [回到目錄](../README.md)
