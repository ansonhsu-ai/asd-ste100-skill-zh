# 受控中文技術寫作技能（ASD-STE100 台灣繁體版）

把含糊、囉嗦、容易被誤讀的中文技術文字，改寫成受控中文：一句一動作、主動語態、一詞一義、去名詞化、
去行銷形容詞與套話。

讀者是**沒有追問機會的另一方**：另一個 agent、翻譯管線、非母語讀者、半年後的你自己。

這個倉庫是英文技能 [danyuchn/asd-ste100-skill](https://github.com/danyuchn/asd-ste100-skill) 的中文對應物，
**不是翻譯**：ASD-STE100 是為了讓航空維修工不可能讀錯英文而做的受控英語，中文的失敗模式不一樣
（虛動詞、套話、同義輪換、分號串聯、翻譯腔），所以規則按中文重寫。差異清單見 [NOTICE.md](NOTICE.md)。

**本版是繁體中文（台灣用語）版**，由簡體中文版轉換而來：不只換字，也換用詞 —— 例如
「行銷」不寫「營銷」、「設定檔」不寫「配置檔案」、「使用者」不寫「用戶」、「錯誤訊息」不寫「報錯」、
「快取」不寫「緩存」、「最佳化」不寫「優化」。主要對照見下方「台灣用語對照」，完整說明見 [NOTICE.md](NOTICE.md)。

## 台灣用語對照（節選）

| 簡體中文版 | 台灣用語 |
|---|---|
| 營銷形容詞 | 行銷形容詞 |
| 配置 / 配置檔案 | 設定 / 設定檔 |
| 用戶 / 客戶端 | 使用者 / 用戶端 |
| 報錯資訊 | 錯誤訊息 |
| 緩存 | 快取 |
| 數據 / 信息 | 資料 / 資訊 |
| 文件（電腦檔案義） | 檔案（文件只指文件本身） |
| 代碼 | 程式碼 |
| 函數 / 項目 | 函式 / 專案（項目只指條目） |
| 質量（品質義） / 優化 | 品質 / 最佳化 |
| 本地環境 / 返回 | 本機環境 / 傳回 |
| 發貨 / 粘貼 | 出貨 / 貼上 |

## 前後對照

| 原文 | 改寫後 |
|---|---|
| 本工具將會嘗試對已經配置好的各個後端進行狀態同步，如果檢測到衝突，則會根據所設定的策略對其進行處理；否則將把衝突提交人工複核。 | 本工具同步各個已設定後端的狀態。如果發現衝突，本工具讀取已設定的策略。策略允許自動處理時，本工具直接處理衝突。策略不允許時，本工具把衝突交給人工複核。 |
| 需要注意的是，該任務已經完成了，產物已經生成出來了，相關的檔案都已經儲存好了。 | 任務已完成，產物可讀。全部輸出檔案已寫入 `dist/`。 |
| 這是一個一站式、全方位的解決方案，可以賦能開發者快速建構強大的應用程式，讓開發體驗絲滑順暢。 | 這個程式庫把建置、測試、部署三步合成一條命令：`dev up`。使用預設設定，一條命令可以啟動本機環境（Node 20+，首次約 40 秒）。 |

更多（工具描述、錯誤訊息、agent 間指令、狀態彙報、PR、README、system prompt、日誌）見
[`examples/before-after.md`](examples/before-after.md)。

## 安裝

### Claude Code / 支援 Agent Skills 的用戶端

```bash
npx skills add ansonhsu-ai/asd-ste100-skill-zh
```

或者複製到個人技能目錄：

```bash
git clone https://github.com/ansonhsu-ai/asd-ste100-skill-zh ~/.claude/skills/ste-zh-tw
```

### Codex / 其他讀 AGENTS.md 的 agent

把下面這段放進專案的 `AGENTS.md`（或全域指令檔案）即可：

> 改寫中文技術文字時套用受控中文規則：一句一動作、主動語態、一詞一義（同一概念全篇同一個詞）、
> 不用分號連接動作、句長（指令 ≤ 25 字、說明 ≤ 40 字）、去掉虛動詞（進行 / 加以 + 名詞）、
> 套話（需要注意的是、在一定程度上）、行銷形容詞（無縫、強大、賦能、閉環）與含糊詞（若干、一些、相關）；
> **不得改動情態**（可能 / 也許）：置信度是內容。機械首查用
> `python <repo>/scripts/ste-lint-zh.py <檔案>`。

### DSH（DeepSeek Harness）

DSH 的 `skill` 工具只認**已註冊**的技能，`~/.dsh/skills` 與 `~/.agents/skills` 目錄不會被掃描。
可靠做法是由一個本機主機外掛程式在啟動時註冊（把 `<repo>` 換成你 clone 下來的路徑）：

```js
ctx.inject(['skills'], (scoped) => {
  scoped.skills.register({
    name: 'ste-zh-tw',
    description: '把含糊、囉嗦、易誤讀的中文改寫成受控中文……',
    content: readFileSync('<repo>/SKILL.md', 'utf8').replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, ''),
    source: 'runtime',
    path: '<repo>/SKILL.md',
  })
})
```

主機端修改後立即生效，註冊完 `skill({ name: 'ste-zh-tw' })` 當場可載入。

## 用法

```
把這段錯誤訊息改寫清楚
按受控中文改一遍這個工具描述
這段 README 讀起來繞，幫我順一下
給這段 agent 指令消歧義
```

預設只返回改寫後的正文。想看清改了哪幾處，加一句「給我看 diff」或「違反了哪些規則」，
會輸出「違反的規則 / 原文 / 改寫後」的表格。

## linter

僅標準庫，Python 3.8+：

```bash
python scripts/ste-lint-zh.py <檔案...>          # 檢查檔案（不給檔案則讀 stdin）
python scripts/ste-lint-zh.py --json <檔案>      # 結構化輸出
python scripts/ste-lint-zh.py --max-chars 25 f   # 程序步驟用 25 字上限
python scripts/ste-lint-zh.py --baseline 12 f    # 既有文件：容忍 12 處硬違規
python scripts/ste-lint-zh.py --disable vague-word,synonym-rotation f
python scripts/ste-lint-zh.py --list-rules       # 列出全部規則
python scripts/ste-lint-zh.py --selftest         # 自檢（20 項）
```

硬違規：`semicolon`、`long-sentence`、`nominalization`、`marketing-adjective`、`empty-phrase`、
`synonym-rotation`（超過 `--baseline` 時退出碼 1）。
建議類：`passive-voice`、`compound-aspect`、`vague-word`、`halfwidth-punct`、`dash-join`（只報告）。
**永不標記情態** —— 自檢裡有一條斷言：「請求可能已失敗。」必須乾淨。

linter 只做機械首查：它不比較原文與改寫、不判斷情態強度、不證明原意保留。零違規只說明這幾項機械檢查沒發現問題。

## 倉庫結構

```
SKILL.md                     技能正文（規則、模式、流程、輸出格式、邊界）
references/writing-rules.md  規則全集 + 與上游九節 53 條的對應 + 中文特有的坑
examples/before-after.md     8 組前後對照；after-only.md 是改寫列的 lint 夾具（硬違規 0）
scripts/ste-lint-zh.py       確定性 linter（stdlib-only，含 --selftest）
docs/article.md            文章稿：方法論 + Karpathy 原話 + 安裝方式
NOTICE.md                    與上游的關係、差異清單、許可
```

自檢：

```bash
python scripts/ste-lint-zh.py --selftest          # 應列印 selftest OK
python scripts/ste-lint-zh.py examples/after-only.md  # 應列印 硬違規 0 處（退出碼 0）
```

## 許可

MIT。規則分類參考上游 danyuchn/asd-ste100-skill（MIT）；未複製其文字、示例與程式碼。
ASD-STE100 標準正文與受控詞表不在本倉庫中。
