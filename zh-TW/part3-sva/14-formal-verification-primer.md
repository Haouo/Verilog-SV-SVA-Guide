# 第三部 · 14. formal verification 入門

[← coverage 與 vacuity](13-coverage-and-vacuity.md) · [目錄](../README.md) · [下一章：checker 與 library →](15-checkers-and-libraries.md)

## 學習目標

- 區分 `assert`、`assume` 與 `cover` 在 formal verification 中的角色。
- 採取 formal 的思維方式：對*所有*合法輸入的證明，而非 sampling 的軌跡（trace）。
- 以 `assume` 約束輸入空間。
- 區分 **safety property** 與 **liveness property**。
- 分辨有界（bounded）與無界（unbounded）證明，並解讀其結果。
- 判斷設計者何時該動用 formal，而非 simulation。

## 設計者的心智模型

formal verification 把問題從「在我跑過的 test 裡有沒有發生？」改成「在所有允許的行為下，這件事可不可能發生？」在這個視角下，assertion 是待證的義務，assumption 定義出合法的環境，cover 則用來問某個情境到底可不可達。

正因如此，assumption 跟 assertion 一樣重要。太弱的 assumption 可能讓工具去探索根本不存在的環境；太強的 assumption 又可能把 bug 藏起來。好的 formal 設定會刻畫設計與環境如何互動，而不只是堆一袋 property。

## formal 做什麼

**formal verification**（形式化驗證）用數學方式，對*每一個*合法的輸入 sequence 證明某 property，而不是檢查 simulation 碰巧產生的有限軌跡。simulation 回答的是「該 property 在我跑過的刺激上成立」，formal 回答的則是「該 property 對*所有*刺激都成立，否則這裡就有一個反例」。

同一批 SVA property 同時驅動這兩者。assertion 本身一點都不用改，要換的是工具。這正是把意圖寫成 assertion 的實際回報：一條 property 同時服務於 simulation 與證明。

## formal 中的 assert、assume、cover

在 formal 情境中，這三個陳述各自承擔鮮明而相異的角色。

- **`assert`**：工具必須*證明*的義務。證明要嘛對所有合法輸入都成立，要嘛產生一條違反它的反例軌跡。
- **`assume`**：工具可以*依賴*的約束。它把輸入空間限制在合法的刺激內，因此證明只考慮滿足它的輸入。
- **`cover`**：工具設法*觸及*的可達性目標。它要求引擎產生一條該行為發生的軌跡，以證明該情境真的有可能出現。

```systemverilog
// assume: the environment never writes a full FIFO (input constraint)
assume property (@(posedge clk) full |-> !wr_en);

// assert: prove the count never exceeds depth (obligation)
assert property (@(posedge clk) count <= DEPTH);

// cover: show the FIFO can actually fill (reachability)
cover  property (@(posedge clk) full);
```

這套分工是 formal 的核心：`assume` 說明環境承諾了什麼，`assert` 說明在那些承諾下設計必須保證什麼，`cover` 則確認證明空間並非空無一物。

## formal 的思維方式

simulation 對 bug 是存在性的：只要你的刺激剛好命中，它就找到 bug。formal 則是全稱性的：它考慮約束所允許的每一個輸入，因此*只要約束範圍內有 bug*，它就會找到，不必你去寫刺激。

這把工程的著力點換了位置。你不再寫測試去誘發設計，而是為「什麼必須為真」寫 `assert`，為「環境可以做什麼」寫 `assume`，剩下的交給工具去搜尋。風險也跟著移位：太緊的 `assume` 可能悄悄排除掉那些剛好能暴露 bug 的輸入。在 formal 裡，約束跟 assertion 一樣重要。

## 以 assume 約束

沒有約束的話，formal 會探索*所有*輸入組合，連真實環境根本不會產生的那些也算進去：非法的協定 sequence、不可能的 reset、保留的 opcode。這些都會產生假反例。`assume` 則切出合法的輸入空間：

```systemverilog
// The protocol guarantees req stays high until ack — tell the prover
assume property (@(posedge clk) $rose(req) |-> req s_until ack);

// Reset is asserted for at least the first cycle
assume property (@(posedge clk) $initstate |-> !rst_n);
```

一組好的約束，就是排除*非法*輸入所需的最小集合，多一條都不要。約束太少，你會被假反例淹沒；太多，又會掩蓋真實的 bug。這裡要留意一種對偶關係：同一條 property，在某區塊的輸入側是 `assume`，到了驅動它那個區塊的輸出側就成了 `assert`,assume/assert 配對正是這樣跨邊界驗證一個介面的。

## 安全性與活性

formal 以不同方式處理兩類 property。

- **safety property** 說的是「壞事絕不發生」。它的違反有一條*有限*的反例，一條長度有界、終止於那個壞週期的軌跡。FIFO 溢位、兩個 grant 同時發生、valid 酬載上出現 `X`，都屬於 safety。
- **liveness property** 說的是「好事終將發生」。它的違反是一條*無限*軌跡，其中那個好事件永遠不到來。「每個請求終將被授予」就屬於 liveness。

```systemverilog
// Safety: a bad state is unreachable
assert property (@(posedge clk) !(grant_a && grant_b));

// Liveness: a request is eventually served (needs unbounded reasoning)
assert property (@(posedge clk) req |-> s_eventually gnt);
```

多數 RTL 簽核屬於 safety：不變式與有界的回應。liveness 需要無界的證明方法，還要一個公平性（fairness）假設，即授予機制不會被永遠餓死。因此它較為沉重，使用上也得更有選擇性。

## 有界與無界證明

formal engine 有兩種保證的型態。

- **有界**證明（bounded model checking）只對自 reset 起固定 *N* 個週期內的所有輸入驗證該 property。它能找出 *N* 步內可達的任何 bug，速度快，但對界限之外的事一句話都說不上。一次乾淨的有界執行是強力的證據，而非完整的證明。
- **無界**證明對*所有*時間驗證該 property，沒有週期上限。它給出完整保證，但較難收斂，碰上龐大的狀態空間時甚至可能跑不完。

實務上，設計者常先用一次有界執行快速抓出淺層 bug，再對關鍵的 safety property 追求無界證明。一次深度為 *N* 的有界通過，代表「*N* 個週期內沒有反例」；請把它當成對一個視窗的 cover，而非一條定理。

> **設計意圖。** formal 把 assertion 從「對你跑過的軌跡所做的檢查」，變成「對環境所允許的每一條軌跡所做的證明」。設計者用 `assert` 陳述意圖，用 `assume` 陳述環境的承諾，用 `cover` 確認可達性，搜尋則交給工具。這套思維是全稱的，而非存在的，而且約束所承載的意圖不亞於 assertion，因為一個寫錯的 `assume` 就可能掩蓋你正在追捕的那個 bug。

## 何時該動用 formal

formal 在特定情境中見效：

- **帶有深層角落情形的控制邏輯**,例如仲裁器、FSM、握手協定，其失敗 sequence 罕見又難以刺激。
- **必須絕對成立的不變式**,例如 one-hot 狀態、不溢位、互斥，這時「我們從沒見它失敗」還不夠有力。
- **針對某個局部區塊的 bug 獵捕**，讓引擎找出那條你寫不出測試的反例。
- 跨大型結構的**連接性與配置**檢查。

simulation 仍適合資料路徑吞吐、系統層級情境，以及任何需要長時間真實刺激的檢查。兩者互補：formal 用來證明角落與不變式，simulation 用來執行整體情境。

## 常見陷阱

- **用 `assume` 過度約束。** 太緊的假設會排除合法輸入並掩蓋真實 bug。只約束真正非法的部分。
- **約束不足。** 假設太少，執行就會被來自不可能輸入的假反例淹沒。請補上協定真正的保證。
- **把有界通過當成完整證明。** 深度 *N* 只涵蓋 *N* 個週期。對關鍵的 safety property，請追求無界證明。
- **以為 liveness 不費力就能拿到。** liveness 需要無界方法與公平性假設。在有真實期限之處，請改用有界的 safety 形式。
- **在 formal 裡忘了 `cover`。** 少了可達性 cover，證明可能只是在一個空的或不可達的空間上空真地成立。請 cover 關鍵情境。

## 小結

- formal 對所有合法輸入證明某 property；simulation 只檢查你跑過的軌跡。
- `assert` 是待證的義務，`assume` 約束輸入空間，`cover` 檢查可達性。
- 思維是全稱的：寫好意圖與約束，讓工具去搜尋；約束所承載的意圖不亞於 assertion。
- safety property 有有限反例，主導著簽核；liveness 需要無界推理與公平性。
- 有界證明能快速涵蓋一個固定視窗；無界證明給出完整保證但較難收斂。碰到深層控制邏輯與絕對不變式，就該動用 formal。

---

[← coverage 與 vacuity](13-coverage-and-vacuity.md) · [目錄](../README.md) · [下一章：checker 與 library →](15-checkers-and-libraries.md)
