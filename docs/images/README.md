# 文章配圖

文章首圖，2026-10-03 產生。

| 檔案 | 尺寸 | 用途 |
| --- | --- | --- |
| `cover-2.35x1.png` / `.jpg` | 1792×763 | 首圖（2.35:1），PNG 是母版 |
| `cover-900x383.jpg` | 900×383 | 文章首圖規格 |
| `cover-1x1-1024.png` / `.jpg` | 1024×1024 | 次圖 / 方圖位 |
| `run-02/image-01.png` | 1792×1024 | 生圖原圖（未裁切） |

## 出處

- 模型：`openai/gpt-image-2.5-sunburst`（OFOX，`size=1792x1024`，`background=opaque`）
- prompt：`prompt-cover.txt`
- 生成器：`E:\development\tools\ofox-image.py`（官方 skill 的 `generate.py` 固定 1024×1024，這裡補了 `--size`）
- 裁切：`python make-covers.py`（原圖只有一張，尺寸都是衍生的，可重跑）

第一次請求（`run-01`）被內容安全策略拒了，改寫 prompt 後第二次透過 —— 同一個主題換措辭即可，拒稿不計費。
