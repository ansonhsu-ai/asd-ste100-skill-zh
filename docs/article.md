# K 神讓 AI 去學 40 年前的航空維修手冊，我把它變成了中文技能

![封面：左邊是寫滿繞句子、畫著航空圖紙的手冊，右邊是同一份內容變成整齊的清單](images/cover-2.35x1.png)

> 文章草稿（部落格／社群發布用）。倉庫：https://github.com/ansonhsu-ai/asd-ste100-skill-zh

## 一、事情從 Karpathy 的一則貼文開始

10 月 2 日，Andrej Karpathy 發了一則貼文，講的是「怎麼讓大模型的輸出變得更容易理解」，瀏覽次數 460 萬。

他給了四條技巧，一條比一條激進。先是讓模型好好寫字，然後畫圖，然後直接生成網頁，最後乾脆做成說明影片。

但他放在第一條、也是唯一一條「Writing」裡的建議，最出人意料：

> Ask your LLM to explain something in ASD-STE100, it's a controlled language specification originally developed for aerospace maintenance documentation.

翻譯過來：**讓大模型用 ASD-STE100 來解釋一件事 —— 那是一套最初為航空維修文件開發的受控語言規範。**

ASD-STE100 是什麼？1986 年，歐洲的航空公司遇到一個具體問題：維修手冊要發給各國的技術人員看。這些人母語大多不是英語，身邊也沒有作者可以打電話問「你這句到底什麼意思」。飛機上讀錯一條指令是會死人的。

於是航空業幹了一件很極端的事 —— **給英語本身加限制**：

- 每個詞只能有一個意思、一種詞性（受控詞表約 900 個詞）。
- 一句話只准有一個動作。
- 程序性指令不超過 20 個詞，說明性文字不超過 25 個詞。
- 分號直接禁用。
- 一個名詞短語最多堆 3 層。

最新的是 Issue 9（2025 年 1 月），53 條寫作規則，9 個章節。

Karpathy 說他自己經常這麼做，而且會**放鬆一點**：

> Sometimes I've tried to soften it a bit e.g. ask for "80% of the way to ASD-STE100" because the spec is quite stringent.

「我有時候會要求它做到 ASD-STE100 的 80%，因為這套規範相當嚴苛。」

他後面三條更激進：

> But even better: Diagrams / images. Instead of writing, ask your LLM to create a diagram.
>
> But even better: Web pages. Ask for output "in HTML" to get a beautiful, interactive webpage.
>
> But even better: Explainer videos. The output format I am most bullish on is fully custom / bespoke explainer videos generated on any arbitrary topic.

畫圖、網頁、客製化說明影片 —— 他最後總結的那段話，是整則貼文的落點：

> As LLMs get better, they will do more and more of the legwork autonomously, and a lot more of our work will rise up the abstractions into oversight and understanding.
>
> Luckily, LLMs can help here too because as intelligence and code are increasingly abundant, you can ask for **large, custom, discardable software artifacts** that would never have made sense to create before.

**大模型把活幹完，人的工作就往上移到「監督」和「理解」。幸運的是，AI 也能幫人做這部分工作。因為智慧和程式碼越來越便宜，你可以為一件具體的事，臨時造一個以前根本不值得造的產物。**

## 二、為什麼這套規範對 Agent 特別有用

Karpathy 是從「人讀模型輸出」的角度講的。但我覺得這套東西對**模型讀模型輸出**更狠。

一個 agent 讀另一個 agent 寫的工具描述或錯誤訊息時，處境和技師一樣：**沒有追問的機會**。當年那個技師在停機坪上翻手冊，身邊也沒有作者可問。它也不能回一句「你這裡的『處理』是指刪除還是重試」。

而中文的問題和英文還不一樣。英文主要栽在兩件事上：一個詞多個意思、一句話多種結構。中文栽的地方很不一樣：

| 中文的壞習慣 | 例子 |
| --- | --- |
| 虛動詞 | 「對日誌**進行分析**」而不是「分析日誌」 |
| 套話 | 「**需要注意的是**，快取會過期」 |
| 同義輪換 | 同一篇裡「檢查 / 驗證 / 核對 / 核查」輪著用，讀者不知道是一個動作還是四個 |
| 一句串三件事 | 「先開票**；**再出貨」，或者「……**並且**……**從而**……」 |
| 翻譯腔 | 「基於……的情況下」「對於……而言」 |
| 含糊詞 | 「**若干**」「**一些**」「**相關**」 |

這些不是文風問題，是**資訊損耗**。模型讀到「進行適當的調整」，只能猜；讀到「重試 2 次，間隔 3 秒」，不用猜。

## 三、我先裝了英文版，然後發現不對味

社群在兩個多月前就有人把 ASD-STE100 做成了開源技能：[danyuchn/asd-ste100-skill](https://github.com/danyuchn/asd-ste100-skill)（現在近 3000 star，MIT）。它把規則用到工具描述、錯誤訊息、system prompt、agent 間指令上，還分了兩種模式：

- **Strict** —— 程序步驟、錯誤訊息、工具描述這類「讀錯有代價」的文字。
- **STE-flavored** —— README、PR 描述這類說明文，保留句長與結構紀律，但不鎖死用詞。

我把它裝進了我的 DSH（我日常跑的 Agent 環境），跑起來很順。但用在自己身上就發現一個問題：**它是英文的，而我的絕大多數文字是中文。**

把英文規則直譯過來，治不了上面那張表裡的任何一條。因為中文的失敗模式不是「一詞多義」，也不是「分號」。比如「對日誌進行分析」這種虛動詞結構，英文裡壓根沒有對應物。

## 四、於是我寫了中文版（本倉庫是它的台灣繁體版）

倉庫：**https://github.com/ansonhsu-ai/asd-ste100-skill-zh**（MIT）

它不是翻譯，是按中文的失敗模式重寫的：

- **規則重寫**：虛動詞、套話、同義輪換、分號串聯、翻譯腔、含糊詞，每條都給「這樣做 / 不要這樣」的對照。
- **兩種模式**：Strict（誤讀有代價的文字）與「中文-順」（README、PR、說明文）。
- **一條鐵律**：**情態是內容。「可能已失敗」不能改成「失敗」，「可能是 X 導致的」不能改成「X 是原因」。** 丟掉一個「可能」，不是簡化，是換了一個結論。這是受控改寫最常見的翻車方式，因為句長上限最容易引誘人去掉的正是這些詞。

倉庫裡有一個只依賴標準庫的 linter (`scripts/ste-lint-zh.py`)，11 條規則，硬違規 6 條、建議類 5 條：

```bash
python scripts/ste-lint-zh.py <檔案>
python scripts/ste-lint-zh.py --selftest        # 20 項斷言
python scripts/ste-lint-zh.py --max-chars 25 f  # 程序步驟用 25 字上限
python scripts/ste-lint-zh.py --baseline 12 f   # 既有文件：容忍 12 處硬違規
```

拿一段很典型的「AI 味中文」試一下：

> 本工具將會嘗試對已經配置好的各個後端進行狀態同步，如果檢測到衝突，則會根據所設定的策略對其進行處理；否則將把衝突提交人工複核。需要注意的是，這套方案強大且無縫。使用者可以在必要時做一些適當的調整。

linter 輸出 10 處發現，其中 7 處硬違規：

- 57 字長句
- 同義輪換（配置 / 設定）
- 虛動詞「進行處理」
- 分號串聯
- 套話
- 兩個行銷形容詞
- 三個含糊詞

改寫之後是：

> 本工具同步各個已設定後端的狀態。如果發現衝突，本工具讀取已設定的策略。策略允許自動處理時，本工具直接處理衝突。策略不允許時，本工具把衝突交給人工複核。

倉庫裡還有 8 組前後對照：工具描述、報錯、agent 間指令、狀態彙報、PR、README、system prompt、日誌。每一組都標出違反了哪條規則，以及改寫後為什麼沒有遺漏資訊。

## 五、怎麼裝

**在 DSH 裡，一句話就夠。** 對著你的 agent 說：

> 把這個技能裝給你自己：https://github.com/ansonhsu-ai/asd-ste100-skill-zh

它會自己 clone 到本機、在宿主外掛程式裡註冊這個技能、跑一遍 `--selftest` 驗證，然後告訴你裝好了。之後你說「把這段報錯改寫清楚」「這段 README 讀起來繞，幫我順一下」，它就會用這套規則。

（DSH 的一個坑：`~/.dsh/skills` 和 `~/.agents/skills` 這兩個目錄它**不認**，技能必須是宿主外掛在執行時註冊的。所以別手動複製檔案，讓 agent 自己接。）

**Claude Code / 支援 Agent Skills 的用戶端：**

```bash
npx skills add ansonhsu-ai/asd-ste100-skill-zh
```

**讀 AGENTS.md 的 agent（Codex 等）：** 把倉庫 README 裡那段規則貼到 `AGENTS.md` 就行，那一段本身就是用受控中文寫的。

英文文字還是用上游的 [danyuchn/asd-ste100-skill](https://github.com/danyuchn/asd-ste100-skill)，兩個技能在我這兒並存：中文走 `ste-zh-tw`，英文走 `asd-ste100`。

## 六、最後

Karpathy 那則貼文的真正意思是：**當智慧和程式碼變得便宜，你可以為一件事臨時造一個以前不值得造的產物。** 一份技能檔案、一個 200 行的 linter，都屬於這類東西。它們不會是產品，但它們讓你每天寫的東西清楚一點。

而「寫清楚」最容易忽略的地方在於：受益人不止是讀你文件的人，還有**下一個讀你輸出的模型**。給機器寫的東西，越不含糊，它越不會跑偏。

規範和工具都在那兒了，改不改，就看你了。

*（這篇稿子自己也被 linter 過了一遍：`python scripts/ste-lint-zh.py --max-chars 45 docs/article.md`。剩下的命中全落在文中引用的病句上 —— 那是它們能當例子、不能當正文的證據。）*

---

*倉庫：https://github.com/ansonhsu-ai/asd-ste100-skill-zh*
*上游：https://github.com/danyuchn/asd-ste100-skill*
*Karpathy 原始貼文：https://x.com/karpathy/status/2105819303471976479*
