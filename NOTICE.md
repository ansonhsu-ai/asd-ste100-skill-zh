# 歸屬與差異

## 上游

- **英文版技能**：[danyuchn/asd-ste100-skill](https://github.com/danyuchn/asd-ste100-skill)（MIT License, Copyright (c) danyuchn）。
  它把 ASD-STE100 的規則類別做成了 Claude Code / agent 技能，並提供英文 linter `scripts/ste-lint.py`。
- **標準本身**：ASD-STE100（Simplified Technical English），ASD 發佈，Issue 9（2025-01）。標準可免費取得，
  但正文與約 900 詞的受控詞表**不可自由再分發**。上游與本倉庫都只複述規則類別，不含其正文與詞表。

## 本倉庫做了什麼

不是翻譯，是按中文的失敗模式重寫：

| | 上游 | 本倉庫 |
|---|---|---|
| 語言 | 英文 | 中文 |
| 主要失敗模式 | 一詞多義、結構歧義 | 虛動詞、套話、同義輪換、分號串聯、翻譯腔 |
| 詞表 | 依賴 ASD 的 ~900 詞受控詞表（不複製） | 中文沒有對應標準，詞彙規則明確降級為「方向」 |
| 句長口徑 | 按詞：程序 ≤ 20、說明 ≤ 25 | 按字：指令 ≤ 25、說明 ≤ 40（linter 預設 40） |
| linter | `scripts/ste-lint.py` | `scripts/ste-lint-zh.py`（另寫，非移植） |
| 情態 | 不標記 | 不標記，並寫進自檢斷言 |

規則類別與上游對應關係見 [`references/writing-rules.md`](references/writing-rules.md) 第二節。

## 台灣繁體版做了什麼

本倉庫由簡體中文版 [lemonhall/asd-ste100-skill-zh](https://github.com/lemonhall/asd-ste100-skill-zh)（MIT）轉換而來，
對象改為台灣讀者。轉換分三層：

1. **字體**：簡體字全部換成繁體字，標點與引號維持全形「」。
2. **用詞**：換成台灣慣用術語 —— 行銷（非營銷）、設定／設定檔（非配置／配置檔案）、使用者／用戶端
   （非用戶／客戶端）、錯誤訊息（非報錯）、快取（非緩存）、資料／資訊（非數據／信息）、
   函式（非函數）、專案（非項目，指 project 時）、品質（非質量，指 quality 時）、最佳化（非優化）、
   本機（非本地，指 local machine 時）、傳回（非返回）、出貨（非發貨）。電腦檔案義用「檔案」，
   「文件」只指文件本身；步驟義的 procedure 仍寫「程序」，程式碼義才寫「程式」。
3. **linter 同步**：`scripts/ste-lint-zh.py` 的詞表與同義組同步換成台灣用語（建議詞以台灣慣用詞為準，
   例如同義組以「使用者」「設定」「檢查」「建立」為建議詞），自檢 20 項全過，
   `examples/after-only.md` 硬違規 0。

原簡體版的 `docs/wechat-article.md`（微信公眾號稿）在本版改名為 `docs/article.md`，內容同步改為台灣用語。

## 許可

本倉庫 MIT（見 LICENSE）。上游同為 MIT，規則類別屬思想與分類，不受版權限制；
上游的具體文字、示例與程式碼未被複製到本倉庫。
