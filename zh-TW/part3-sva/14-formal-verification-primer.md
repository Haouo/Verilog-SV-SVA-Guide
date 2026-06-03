# 第三部 · 14. 形式化驗證入門

[← 覆蓋率與空真（vacuity）](13-coverage-and-vacuity.md) · [目錄](../README.md) · [下一章：checker 與函式庫 →](15-checkers-and-libraries.md)

## 學習目標

- 區分 `assert`、`assume` 與 `cover` 在形式化驗證中的角色。
- 採取形式化的思維方式：對*所有*合法輸入的證明，而非取樣的軌跡（trace）。
- 以 `assume` 約束輸入空間。
- 區分**安全性性質**（safety property）與**活性性質**（liveness property）。
- 分辨有界（bounded）與無界（unbounded）證明，並解讀其結果。
- 判斷設計者何時該動用形式化，而非模擬。

## 形式化做什麼

**形式化驗證**（formal verification）以數學方式，對*每一個*合法的輸入序列證明某性質，而非檢查模擬恰好產生的有限軌跡。模擬回答的是「該性質在我跑過的刺激上成立」，而形式化回答的是「該性質對*所有*刺激皆成立，否則這裡有一個反例」。

同一批 SVA 性質同時驅動兩者。斷言本身毫無改變；改變的是工具。這正是把意圖寫成斷言的實際回報：一條性質同時服務於模擬與證明。

## 形式化中的 assert、assume、cover

在形式化情境中，這三個陳述各自承擔鮮明而相異的角色。

- **`assert`** —— 工具必須*證明*的義務。證明要嘛對所有合法輸入皆成立，要嘛產生一條違反它的反例軌跡。
- **`assume`** —— 工具可以*依賴*的約束。它把輸入空間限制到合法的刺激，因此證明只考慮滿足它的輸入。
- **`cover`** —— 工具設法*觸及*的可達性目標。它要求引擎產生一條該行為發生的軌跡，以證明該情境是可能的。

```systemverilog
// assume: the environment never writes a full FIFO (input constraint)
assume property (@(posedge clk) full |-> !wr_en);

// assert: prove the count never exceeds depth (obligation)
assert property (@(posedge clk) count <= DEPTH);

// cover: show the FIFO can actually fill (reachability)
cover  property (@(posedge clk) full);
```

這套劃分是形式化的核心：`assume` 說環境承諾了什麼，`assert` 說在那些承諾下設計必須保證什麼，而 `cover` 確認證明空間非空。

## 形式化的思維方式

模擬對 bug 是存在性的：若你的刺激恰好命中，它便找到 bug。形式化是全稱性的：它考慮約束所允許的每一個輸入，因此*只要約束內存在 bug*，它就會找到，無需撰寫刺激。

這轉移了工程的著力點。你不再撰寫測試去誘發設計；你為「什麼必須為真」撰寫 `assert`，為「環境可以做什麼」撰寫 `assume`，然後由工具搜尋。風險也隨之轉移：過緊的 `assume` 可能無聲地排除掉恰好能暴露 bug 的那些輸入。在形式化中，約束與斷言同等重要。

## 以 assume 約束

若無約束，形式化會探索*所有*輸入組合，包括真實環境從不產生的那些——非法的協定序列、不可能的重置、保留的 opcode。那些會產生假反例。`assume` 切割出合法的輸入空間：

```systemverilog
// The protocol guarantees req stays high until ack — tell the prover
assume property (@(posedge clk) $rose(req) |-> req s_until ack);

// Reset is asserted for at least the first cycle
assume property (@(posedge clk) $initstate |-> !rst_n);
```

一組好的約束，是排除*非法*輸入所需的最小集合，僅此而已。約束太少，你會被假反例淹沒；太多，則掩蓋真實的 bug。注意此處的對偶性：同一條性質，在某區塊的輸入側是 `assume`，在驅動它的那個區塊的輸出側則是 `assert`——這正是 assume/assert 配對跨邊界驗證一個介面的方式。

## 安全性與活性

形式化以不同方式處理兩類性質。

- **安全性性質**說「壞事絕不發生」。它的違反有一條*有限*的反例——一條有界長度、終止於壞週期的軌跡。FIFO 溢位、兩個同時的 grant、valid 酬載上的 `X`：皆屬安全性。
- **活性性質**說「好事終將發生」。它的違反是一條*無限*軌跡，其中好事件永不到來。「每個請求終將被授予」即屬活性。

```systemverilog
// Safety: a bad state is unreachable
assert property (@(posedge clk) !(grant_a && grant_b));

// Liveness: a request is eventually served (needs unbounded reasoning)
assert property (@(posedge clk) req |-> s_eventually gnt);
```

多數 RTL 簽核屬安全性：不變式與有界回應。活性需要無界的證明方法與一個公平性（fairness）假設（授予機制不會被永遠餓死），因此較為沉重，使用上也較有選擇性。

## 有界與無界證明

形式化引擎有兩種保證的型態。

- **有界**證明（bounded model checking）對自重置起固定週期數 *N* 內的所有輸入驗證該性質。它能找到 *N* 步內可達的任何 bug，速度快，但對界限之外無話可說。一次乾淨的有界執行是強力的證據，而非完整的證明。
- **無界**證明對*所有*時間驗證該性質，沒有週期上限。它給出完整保證，但較難收斂，且在龐大的狀態空間上可能無法完成。

實務上，設計者常先以一次有界執行快速抓出淺層 bug，再對關鍵的安全性性質追求無界證明。一次深度為 *N* 的有界通過意味著「*N* 個週期內無反例」；請把它讀作一個視窗的覆蓋，而非一條定理。

> **設計意圖。** 形式化把斷言從「對你跑過的軌跡的檢查」變成「對環境所允許的每一條軌跡的證明」。設計者以 `assert` 陳述意圖，以 `assume` 陳述環境的承諾，以 `cover` 確認可達性；搜尋由工具完成。思維是全稱的，而非存在的——而約束所承載的意圖不亞於斷言，因為一個錯誤的 `assume` 可能掩蓋你正在追捕的那個 bug。

## 何時該動用形式化

形式化在特定情境中見效：

- **帶有深層角落情形的控制邏輯**——仲裁器、FSM、握手協定——其失敗序列罕見且難以刺激。
- **必須絕對成立的不變式**——one-hot 狀態、不溢位、互斥——此時「我們從沒見它失敗」還不夠強。
- **bug 獵捕**於某個局部區塊上，讓引擎找出你無法寫出測試的那條反例。
- 跨大型結構的**連接性與配置**檢查。

模擬仍是資料路徑吞吐、系統層級情境，以及任何需要長時間真實刺激之事的正確工具。兩者互補：形式化證明角落，模擬執行整體。

## 常見陷阱

- **以 `assume` 過度約束。** 過緊的假設會排除合法輸入並掩蓋真實 bug。只約束真正非法的部分。
- **約束不足。** 假設太少會使執行被來自不可能輸入的假反例淹沒。請加入協定的真實保證。
- **把有界通過當作完整證明。** 深度 *N* 只涵蓋 *N* 個週期。對關鍵的安全性性質請追求無界證明。
- **期望活性免費取得。** 活性需要無界方法與公平性假設。在有真實期限之處，請使用有界的安全性形式。
- **在形式化中忘記 `cover`。** 若無可達性覆蓋，證明可能在一個空的或不可達的空間上空真地成立。請覆蓋關鍵情境。

## 小結

- 形式化對所有合法輸入證明某性質；模擬檢查你跑過的軌跡。
- `assert` 是待證的義務，`assume` 約束輸入空間，`cover` 檢查可達性。
- 思維是全稱的：撰寫意圖與約束，讓工具搜尋；約束所承載的意圖不亞於斷言。
- 安全性性質有有限反例並主導簽核；活性需要無界推理與公平性。
- 有界證明快速涵蓋固定視窗；無界證明給出完整保證但較難收斂。對深層控制邏輯與絕對不變式請動用形式化。

---

[← 覆蓋率與空真（vacuity）](13-coverage-and-vacuity.md) · [目錄](../README.md) · [下一章：checker 與函式庫 →](15-checkers-and-libraries.md)
