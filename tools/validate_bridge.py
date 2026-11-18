#!/usr/bin/env python3
"""Validate subway-map <-> LEGO bridge references. Standard library only."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_js_object(path: Path, name: str):
    text = path.read_text(encoding="utf-8")
    marker = f"window.{name} ="
    pos = text.find(marker)
    if pos < 0:
        raise ValueError(f"{path}: missing {marker}")
    value, _ = json.JSONDecoder().raw_decode(text[pos + len(marker):].lstrip())
    return value


def main() -> int:
    errors = []
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    match = re.search(r'<script type="application/json" id="lego-config">(.*?)</script>', html, re.S)
    if not match:
        print("index.html: missing lego-config")
        return 1
    cfg = json.loads(match.group(1))
    nodes = {n["id"] for n in read_js_object(ROOT / "data/knowledge-data.js", "KNOWLEDGE_DATA")["nodes"]}
    bricks = {b["id"] for b in cfg.get("bricks", [])}
    presets = {p["id"] for p in cfg.get("presets", [])}
    bridge = read_js_object(ROOT / "data/knowledge-bridge.js", "KNOWLEDGE_BRIDGE")
    seen = set()
    allowed = {"brick", "preset", "version"}
    versions = {"M3", "M4", "EF4", "M5"}
    for i, link in enumerate(bridge.get("links", []), 1):
        key = (link.get("nodeId"), link.get("targetType"), link.get("targetId"))
        if key in seen:
            errors.append(f"bridge link {i}: duplicate relation {key}")
        seen.add(key)
        if link.get("nodeId") not in nodes:
            errors.append(f"bridge link {i}: missing knowledge node {link.get('nodeId')}")
        kind, target = link.get("targetType"), link.get("targetId")
        if kind not in allowed:
            errors.append(f"bridge link {i}: unsupported targetType {kind}")
        elif kind == "brick" and target not in bricks:
            errors.append(f"bridge link {i}: missing brick {target}")
        elif kind == "preset" and target not in presets:
            errors.append(f"bridge link {i}: missing preset {target}")
        elif kind == "version" and target not in versions:
            errors.append(f"bridge link {i}: unknown NERO version {target}")
    if errors:
        print(f"Found {len(errors)} bridge issue(s):")
        for error in errors:
            print(" -", error)
        return 1
    print(f"Bridge OK: {len(nodes)} knowledge nodes, {len(bricks)} bricks, {len(presets)} presets, {len(bridge.get('links', []))} cross-links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
