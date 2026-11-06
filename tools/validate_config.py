#!/usr/bin/env python3
"""检查 index.html 顶部 JSON 配置是否完整、引用是否正确。

用法：python3 tools/validate_config.py [index.html]
没有第三方依赖。发现问题时列出全部问题并以非 0 退出码结束。
"""
import json
import re
import sys
from pathlib import Path

REQUIRED_BRICK = ["id", "slot", "cat", "name", "paper", "year", "org", "idea", "solves", "metaphor"]
INNER = ["pos", "norm", "attn", "ffn"]
L1 = ["tokenizer", "vision", "connector", "proprio", "backbone", "head"]
CATS = {"input", "connector", "backbone", "pos", "norm", "attn", "ffn", "text", "action", "recipe"}


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "index.html")
    html = path.read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="lego-config">(.*?)</script>', html, re.S)
    if not m:
        print(f"{path}: 找不到 id=\"lego-config\" 的配置块")
        return 1
    try:
        cfg = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        line = m.group(1)[: e.pos].count("\n") + html[: m.start(1)].count("\n") + 1
        print(f"JSON 语法错误（index.html 第 {line} 行附近）：{e.msg}")
        return 1

    errs = []
    slots = {s["id"]: s for s in cfg.get("slots", [])}
    bricks = {}
    for b in cfg.get("bricks", []):
        bid = b.get("id", "?")
        if bid in bricks:
            errs.append(f"积木 id 重复：{bid}")
        bricks[bid] = b
        for f in REQUIRED_BRICK:
            if not b.get(f):
                errs.append(f"积木 {bid} 缺少字段 {f}")
        if b.get("slot") not in slots:
            errs.append(f"积木 {bid} 的 slot「{b.get('slot')}」不存在")
        if b.get("cat") not in CATS:
            errs.append(f"积木 {bid} 的 cat「{b.get('cat')}」不在 {sorted(CATS)} 中")
        for f in b.get("verify", []):
            if f not in b:
                errs.append(f"积木 {bid} 的 verify 里写了 {f}，但没有这个字段")
        for link in b.get("links", []):
            if not str(link.get("url", "")).startswith("http"):
                errs.append(f"积木 {bid} 有一条链接不是 http(s) 地址")

    def check_ref(owner, key, bid, want_slot):
        if bid is None:
            return
        if bid not in bricks:
            errs.append(f"{owner} 的 {key} 引用了不存在的积木 {bid}")
        elif bricks[bid]["slot"] != want_slot:
            errs.append(f"{owner} 的 {key} 放了 {bid}，但它属于 {bricks[bid]['slot']} 槽")

    for b in bricks.values():
        if b.get("slot") == "backbone":
            inner = b.get("inner")
            if not inner:
                errs.append(f"主干积木 {b['id']} 缺少 inner（Block 内部四个槽）")
                continue
            for k in INNER:
                check_ref(f"主干 {b['id']}", k, inner.get(k), k)

    hotkeys = {}
    pids = set()
    for p in cfg.get("presets", []):
        pid = p.get("id", "?")
        if pid in pids:
            errs.append(f"预设 id 重复：{pid}")
        pids.add(pid)
        for k in L1:
            if k not in p.get("slots", {}):
                errs.append(f"预设 {pid} 的 slots 缺少 {k}（没有就写 null）")
            check_ref(f"预设 {pid}", k, p.get("slots", {}).get(k), k)
        for k in INNER:
            check_ref(f"预设 {pid}", k, p.get("inner", {}).get(k), k)
        for r in p.get("recipe", []):
            check_ref(f"预设 {pid}", "recipe", r, "recipe")
        for k, alts in (p.get("alt") or {}).items():
            for a in alts:
                check_ref(f"预设 {pid} 的 alt", k, a, k)
        for k in p.get("ignore", []):
            if k not in L1 + INNER:
                errs.append(f"预设 {pid} 的 ignore 里有未知槽 {k}")
        hk = p.get("hotkey")
        if hk:
            if hk in hotkeys:
                errs.append(f"快捷键 {hk} 同时分给了 {hotkeys[hk]} 和 {pid}")
            hotkeys[hk] = pid
        if p.get("kind") not in {"LLM", "VLM", "VLA"}:
            errs.append(f"预设 {pid} 的 kind 应为 LLM / VLM / VLA")

    for pid in cfg.get("evolution", []):
        if pid not in pids:
            errs.append(f"evolution 里的 {pid} 不是已有预设")

    if errs:
        print(f"发现 {len(errs)} 个问题：")
        for e in errs:
            print("  -", e)
        return 1
    print(f"配置正常：{len(slots)} 个插槽，{len(bricks)} 块积木，{len(pids)} 个预设。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
