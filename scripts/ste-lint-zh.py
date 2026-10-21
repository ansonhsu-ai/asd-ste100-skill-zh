#!/usr/bin/env python3
"""受控中文 linter（繁體中文・台灣用語）—— ASD-STE100 的中文對應物，只查機械可判的規則。

用法：
    python scripts/ste-lint-zh.py <檔案...>          # 檢查檔案
    python scripts/ste-lint-zh.py < 文字             # 從 stdin 讀
    python scripts/ste-lint-zh.py --json <檔案...>   # 結構化輸出
    python scripts/ste-lint-zh.py --max-chars 25 f   # 程序步驟用 25 字上限
    python scripts/ste-lint-zh.py --baseline 12 f    # 既有文件：容忍 12 處硬違規
    python scripts/ste-lint-zh.py --disable vague-word,synonym-rotation f
    python scripts/ste-lint-zh.py --selftest         # 自檢

硬違規（semicolon / long-sentence / nominalization / marketing-adjective /
empty-phrase / synonym-rotation）超過 --baseline 時退出碼 1。
建議類（passive-voice / compound-aspect / vague-word / halfwidth-punct /
dash-join）只報告，永不導致失敗。

它**永遠不挑情態**（可能 / 也許 / 大概 / 傾向於）：置信度是內容，不是風格。
自檢裡有一條斷言：「請求可能已失敗。」必須乾淨。

僅標準庫，Python 3.8+。
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

HARD = "hard"
ADVISORY = "advisory"

RULE_SEVERITY: Dict[str, str] = {
    "semicolon": HARD,
    "long-sentence": HARD,
    "nominalization": HARD,
    "marketing-adjective": HARD,
    "empty-phrase": HARD,
    "synonym-rotation": HARD,
    "passive-voice": ADVISORY,
    "compound-aspect": ADVISORY,
    "vague-word": ADVISORY,
    "halfwidth-punct": ADVISORY,
    "dash-join": ADVISORY,
}

RULE_ORDER = list(RULE_SEVERITY)

CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
SENT_END_RE = re.compile(r"[。！？!?]+")
MASK_RE = re.compile(r"`[^`\n]*`|https?://\S+|\[[^\]]*\]\([^)]*\)")
LIST_MARK_RE = re.compile(r"^(\s*(?:#{1,6}|[-*+]|\d{1,3}[.)]|>)\s+)")
SENTENCE_SPLIT_RE = re.compile(r"[。！？!?；;]")

# 行銷形容詞：宣稱品質而不給證據。命中即刪，或換成可測量的說法。
MARKETING_WORDS = (
    "無縫", "強大", "賦能", "閉環", "極致", "絲滑", "一站式", "全方位", "顛覆",
    "領先", "頂級", "沉浸式", "智慧化", "黑科技", "革命性", "獨創", "完美",
    "極速", "超強", "極致體驗", "降維打擊",
)

# 套話：刪掉之後句子資訊量不變。
EMPTY_PHRASES = (
    "需要注意的是", "值得一提的是", "眾所周知", "不難看出", "不言而喻",
    "在一定程度上", "某種意義上", "從某種角度", "綜上所述", "顯而易見",
    "毋庸置疑", "總的來說",
)

# 名詞化：虛動詞 + 動作名詞。改成單個動詞。
NOMINALIZATION_RE = re.compile(
    r"(進行|作出|加以|予以|給予|開展)(一[下個次些])?"
    r"[^，。！？；、\s]{0,6}?"
    r"(分析|檢查|處理|最佳化|驗證|評估|討論|說明|調整|改造|升級|計算|統計|測試|"
    r"梳理|比對|排查|確認|審核|覆盤|治理|維護|修復|部署|設計|規劃|調研|探索|實踐|嘗試)"
)

PASSIVE_RE = re.compile(r"被[^，。！？；\s]{0,6}")
COMPOUND_ASPECT_RE = re.compile(r"(已經[^，。！？；]{0,10}[了過]|正在[^，。！？；]{0,8}[中著])")
VAGUE_RE = re.compile(r"(相關|有關|若干|一些|適當|酌情|必要時|等等|之類|大致|差不多|一定程度)")
HALFWIDTH_RE = re.compile(r"(?<=[\u4e00-\u9fff])[,;:!?](?=[\u4e00-\u9fff])")
DASH_JOIN_RE = re.compile(r"——")
SEMICOLON_RE = re.compile(r"[；;]")

# 同義輪換：同一篇裡出現兩個以上成員即視為輪換（同一份文件範圍，跨行統計）。
SYNONYM_GROUPS: Tuple[Tuple[str, ...], ...] = (
    ("使用者", "用戶", "客戶", "終端使用者"),
    ("刪除", "移除", "清除", "刪掉"),
    ("檢查", "驗證", "核對", "核查"),
    ("建立", "新增", "新建", "生成"),
    ("錯誤", "異常", "故障"),
    ("設定", "設置", "配置"),
    ("顯示", "展示", "呈現"),
    ("執行", "運行", "運作"),
    ("儲存", "保存"),
    ("修改", "更改", "變更"),
)

# 中文沒有詞邊界，命中後要擋掉"看起來像、其實是別的詞"的字尾：
# 用戶端不是用戶，客戶端不是客戶，使用者名稱不是使用者，檢查點不是檢查，
# 建立時間不是建立，執行緒不是執行……
SYNONYM_BLOCKED_SUFFIX: Dict[str, Tuple[str, ...]] = {
    "使用者": ("名",),
    "用戶": ("端",),
    "客戶": ("端",),
    "檢查": ("點",),
    "建立": ("時間",),
    "生成": ("式",),
    "顯示": ("器",),
    "執行": ("緒",),
    "錯誤": ("碼",),
}


def member_occurrences(text: str, member: str) -> List[int]:
    """找出 member 在 text 裡真正算數的位置，跳過被字尾擋掉的假命中。"""
    blocked = SYNONYM_BLOCKED_SUFFIX.get(member, ())
    positions: List[int] = []
    start = 0
    while True:
        index = text.find(member, start)
        if index < 0:
            break
        tail = text[index + len(member):]
        if not any(tail.startswith(suffix) for suffix in blocked):
            positions.append(index)
        start = index + len(member)
    return positions



@dataclass
class Options:
    max_chars: int = 40
    baseline: int = 0
    disabled: frozenset = frozenset()


@dataclass
class Finding:
    path: str
    line: int
    col: int
    rule: str
    severity: str
    message: str
    match: str

    def as_dict(self) -> dict:
        return {
            "path": self.path,
            "line": self.line,
            "col": self.col,
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
            "match": self.match,
        }

    def render(self) -> str:
        return f"{self.path}:{self.line}:{self.col} {self.rule}: {self.message} [{self.match}]"


def count_chars(text: str) -> int:
    """長度口徑：一個漢字算 1，一段連續的拉丁字母 / 數字算 1（同上遊「按詞算」）。"""
    cjk = len(CJK_RE.findall(text))
    latin = len(TOKEN_RE.findall(text))
    return cjk + latin


def mask_line(line: str) -> str:
    """把行內程式碼、URL、markdown 連結替換成等長空格 —— 程式碼不是散文，不參與檢查。"""
    chars = list(line)
    for match in MASK_RE.finditer(line):
        for index in range(match.start(), match.end()):
            chars[index] = " "
    return "".join(chars)


def split_cells(line: str) -> List[Tuple[int, str]]:
    """按 markdown 表格分隔線切段，保留每段在原行裡的起始列。"""
    cells: List[Tuple[int, str]] = []
    start = 0
    for index, char in enumerate(line):
        if char == "|":
            cells.append((start, line[start:index]))
            start = index + 1
    cells.append((start, line[start:]))
    return cells


def iter_sentences(text: str, base: int) -> Iterable[Tuple[int, str]]:
    """按句末標點切句；分號留在句內，好讓 semicolon 規則看得見它。"""
    start = 0
    for match in SENT_END_RE.finditer(text):
        end = match.end()
        yield base + start, text[start:end]
        start = end
    if text[start:].strip():
        yield base + start, text[start:]


def sentence_findings(
    sentence: str,
    offset: int,
    line_no: int,
    path: str,
    opts: Options,
) -> List[Finding]:
    findings: List[Finding] = []
    stripped = sentence.strip()
    if not stripped:
        return findings

    def add(rule: str, message: str, match_text: str, rel: int) -> None:
        if rule in opts.disabled:
            return
        findings.append(
            Finding(
                path=path,
                line=line_no,
                col=offset + rel + 1,
                rule=rule,
                severity=RULE_SEVERITY[rule],
                message=message,
                match=match_text,
            )
        )

    for match in SEMICOLON_RE.finditer(sentence):
        add(
            "semicolon",
            "分號把兩件事串進了一句。拆成兩句。",
            match.group(0),
            match.start(),
        )

    length = count_chars(sentence)
    if length > opts.max_chars:
        add(
            "long-sentence",
            f"句子 {length} 字（上限 {opts.max_chars}）。拆開，或刪掉不必要的資訊。",
            f"{length} 字",
            0,
        )

    for match in NOMINALIZATION_RE.finditer(sentence):
        add(
            "nominalization",
            f"虛動詞 + 名詞（「{match.group(0)}」）。直接用動詞。",
            match.group(0),
            match.start(),
        )

    for word in MARKETING_WORDS:
        start = sentence.find(word)
        if start >= 0:
            add(
                "marketing-adjective",
                "行銷形容詞。刪掉，或換成撐得起這句話的測量值。",
                word,
                start,
            )

    for phrase in EMPTY_PHRASES:
        start = sentence.find(phrase)
        if start >= 0:
            add(
                "empty-phrase",
                "套話。刪掉，直接說事。",
                phrase,
                start,
            )

    for match in PASSIVE_RE.finditer(sentence):
        add(
            "passive-voice",
            "被動語態。說清施事並改用主動，除非施事未知或無關。",
            match.group(0),
            match.start(),
        )

    for match in COMPOUND_ASPECT_RE.finditer(sentence):
        add(
            "compound-aspect",
            "複合體貌。簡單體貌夠用就簡化；表達當前相關性時保留並標註。",
            match.group(0),
            match.start(),
        )

    for match in VAGUE_RE.finditer(sentence):
        add(
            "vague-word",
            "含糊詞。給出數量、範圍或條件。",
            match.group(0),
            match.start(),
        )

    for match in HALFWIDTH_RE.finditer(sentence):
        add(
            "halfwidth-punct",
            "中文句子裡的半形標點。換成全形。",
            match.group(0),
            match.start(),
        )

    for match in DASH_JOIN_RE.finditer(sentence):
        add(
            "dash-join",
            "破折號連接。通常說明這句話該拆。",
            match.group(0),
            match.start(),
        )

    return findings


def analyze(text: str, path: str = "<stdin>", opts: Optional[Options] = None) -> List[Finding]:
    o = opts or Options()
    findings: List[Finding] = []
    # group_index -> member -> [line, col, count]
    rotation_hits: Dict[int, Dict[str, List[int]]] = {}
    in_fence = False

    for line_no, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        line = mask_line(raw)
        for cell_offset, cell in split_cells(line):
            mark = LIST_MARK_RE.match(cell)
            skip = mark.end() if mark else len(cell) - len(cell.lstrip())
            body = cell[skip:]
            if not body.strip():
                continue
            base = cell_offset + skip
            for sent_offset, sentence in iter_sentences(body, base):
                findings.extend(sentence_findings(sentence, sent_offset, line_no, path, o))
                if "synonym-rotation" not in o.disabled:
                    for group_index, group in enumerate(SYNONYM_GROUPS):
                        for member in group:
                            positions = member_occurrences(sentence, member)
                            if positions:
                                entry = rotation_hits.setdefault(group_index, {}).setdefault(
                                    member, [line_no, sent_offset + positions[0] + 1, 0]
                                )
                                entry[2] += len(positions)

    for group_index, members in sorted(rotation_hits.items()):
        if len(members) < 2:
            continue
        group = SYNONYM_GROUPS[group_index]
        # 保留出現次數最多的那個（並列時取組內順序靠前的），其餘算輪換。
        keeper = max(members.items(), key=lambda item: (item[1][2], -group.index(item[0])))[0]
        found = "、".join(f"{name}×{data[2]}" for name, data in members.items())
        for member, (line_no, col, _count) in sorted(members.items(), key=lambda item: item[1][:2]):
            if member == keeper:
                continue
            findings.append(
                Finding(
                    path=path,
                    line=line_no,
                    col=col,
                    rule="synonym-rotation",
                    severity=RULE_SEVERITY["synonym-rotation"],
                    message=f"同義輪換：{found} 混用。定一個名字全篇用它，建議「{keeper}」。",
                    match=member,
                )
            )

    findings.sort(key=lambda f: (f.line, f.col, RULE_ORDER.index(f.rule)))
    return findings


def summarize(findings: Sequence[Finding], text: str, baseline: int) -> str:
    hard = sum(1 for f in findings if f.severity == HARD)
    total_chars = count_chars(text)
    rate = (len(findings) / total_chars * 100) if total_chars else 0.0
    return (
        f"共 {len(findings)} 處發現（硬違規 {hard}，baseline {baseline}），"
        f"{total_chars} 字，每 100 字 {rate:.1f} 處\n"
        "情態（可能 / 也許 / 大概 / 傾向於）永不標記：置信度是內容。"
    )


def run(paths: Sequence[str], opts: Options, as_json: bool, stream) -> int:
    outputs: List[str] = []
    all_findings: List[Finding] = []
    combined: List[str] = []

    if paths:
        sources = []
        for path in paths:
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    sources.append((path, handle.read()))
            except OSError as error:
                stream.write(f"{path}: 讀不到檔案：{error}\n")
                return 2
    else:
        sources = [("<stdin>", sys.stdin.read())]

    for path, text in sources:
        combined.append(text)
        findings = analyze(text, path, opts)
        all_findings.extend(findings)
        for finding in findings:
            outputs.append(finding.render())
        if not as_json:
            hard = sum(1 for f in findings if f.severity == HARD)
            if hard > opts.baseline:
                outputs.append(f"→ {path}: {hard} 處硬違規（baseline {opts.baseline}）")
            else:
                outputs.append(f"→ {path}: 硬違規 {hard} 處，未超過 baseline {opts.baseline}")

    if as_json:
        stream.write(json.dumps([f.as_dict() for f in all_findings], ensure_ascii=False, indent=2))
        stream.write("\n")
    else:
        for line in outputs:
            stream.write(line + "\n")
        stream.write(summarize(all_findings, "\n".join(combined), opts.baseline) + "\n")

    hard_total = sum(1 for f in all_findings if f.severity == HARD)
    return 1 if hard_total > opts.baseline else 0


def selftest() -> int:
    failures: List[str] = []
    clean = Options()

    def rules(text: str, opts: Options = clean, path: str = "<selftest>") -> List[str]:
        return [finding.rule for finding in analyze(text, path, opts)]

    def check(name: str, condition: bool, detail: str = "") -> None:
        if condition:
            print(f"  ok   {name}")
        else:
            failures.append(f"{name} {detail}")
            print(f"  FAIL {name} {detail}")

    print("受控中文 linter 自檢：")
    check("乾淨文字沒有發現", rules("開啟設定檔。讀取第三行。把結果寫入日誌。") == [])
    check("情態永不標記（可能已失敗）", rules("請求可能已失敗。") == [])
    check("程式碼塊裡的分號不算", rules("```\n先開票；再出貨\n```") == [])
    check("行內程式碼被遮罩", rules("用 `a；b` 分隔即可。") == [])
    check("分號被判硬違規", "semicolon" in rules("先開票；再出貨。"))
    check("名詞化被判", "nominalization" in rules("我們需要對日誌進行分析。"))
    check("行銷形容詞被判", rules("這是一款無縫又強大的工具。").count("marketing-adjective") == 2)
    check("套話被判", "empty-phrase" in rules("需要注意的是，快取會過期。"))
    check("超長句被判", "long-sentence" in rules("把" + "很長的說明" * 9 + "寫完了。"))
    check(
        "同義輪換被判",
        "synonym-rotation" in rules("使用者登入。使用者退出。客戶付款。"),
    )
    check("單一用詞不報輪換", "synonym-rotation" not in rules("使用者登入。使用者退出。使用者付款。"))
    check(
        "字尾擋住假命中（用戶端 ≠ 用戶）",
        "synonym-rotation" not in rules("用戶端版本過舊。用戶端重試。使用者登入。"),
    )
    check("含糊詞是建議類", "vague-word" in rules("在必要時做適當調整。"))
    check(
        "建議類不影響退出判定",
        all(
            finding.severity == ADVISORY
            for finding in analyze("日誌被清空了。", "<selftest>", clean)
        ),
    )
    check("清單標記被剝掉", rules("- 開啟檔案。\n- 讀取第三行。") == [])
    check("表格各儲存格分別檢查", "semicolon" in rules("| 甲 | 先開票；再出貨 |"))
    check("--max-chars 收緊後長句被判", "long-sentence" in rules("讀取設定並寫入日誌。", Options(max_chars=5)))
    check(
        "disable 關得掉規則",
        "semicolon" not in rules("先開票；再出貨。", Options(disabled=frozenset({"semicolon"}))),
    )
    check(
        "baseline 容忍硬違規",
        run_quiet("先開票；再出貨。\n", Options(baseline=1)) == 0,
    )
    check(
        "baseline 不足時退出碼 1",
        run_quiet("先開票；再出貨。\n", Options(baseline=0)) == 1,
    )

    if failures:
        print(f"selftest FAILED（{len(failures)} 項）")
        return 1
    print("selftest OK")
    return 0


def run_quiet(text: str, opts: Options) -> int:
    original = sys.stdin
    sys.stdin = io.StringIO(text)
    try:
        return run([], opts, False, io.StringIO())
    finally:
        sys.stdin = original


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="ste-lint-zh.py",
        description="受控中文 linter（台灣用語）：只查機械可判的規則，永不挑情態。",
    )
    parser.add_argument("files", nargs="*", help="要檢查的檔案；不給則讀 stdin")
    parser.add_argument("--json", action="store_true", help="輸出 JSON")
    parser.add_argument("--max-chars", type=int, default=40, help="句長上限（預設 40；程序步驟建議 25）")
    parser.add_argument("--baseline", type=int, default=0, help="容忍的硬違規數（既有文件接入用）")
    parser.add_argument("--disable", default="", help="要關掉的規則名，逗號分隔")
    parser.add_argument("--selftest", action="store_true", help="跑內建自檢")
    parser.add_argument("--list-rules", action="store_true", help="列出規則與嚴重度")
    return parser.parse_args(argv)


def main(argv: Sequence[str]) -> int:
    args = parse_args(argv)
    if args.selftest:
        return selftest()
    if args.list_rules:
        for rule in RULE_ORDER:
            print(f"{RULE_SEVERITY[rule]:9} {rule}")
        return 0

    disabled = frozenset(name.strip() for name in args.disable.split(",") if name.strip())
    unknown = sorted(name for name in disabled if name not in RULE_SEVERITY)
    if unknown:
        print(f"未知規則名：{', '.join(unknown)}（用 --list-rules 看全部）", file=sys.stderr)
        return 2

    opts = Options(max_chars=args.max_chars, baseline=args.baseline, disabled=disabled)
    return run(args.files, opts, args.json, sys.stdout)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
