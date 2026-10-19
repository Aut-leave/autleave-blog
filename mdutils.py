#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown 预处理：把 Obsidian 专有语法翻译成 Goldmark 能认的写法。

目前处理：
    ^[行内脚注]  ->  [^xN]  + 文末追加定义
"""

import re

INLINE_FN = re.compile(r"\^\[([^\]\n]+)\]")


def convert_inline_footnotes(md: str) -> str:
    """把 ^[文字] 转成标准脚注 [^xN] + 文末定义"""
    lines = md.split("\n")
    out = []
    defs = []
    in_fence = False

    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            continue

        if in_fence:
            out.append(line)
            continue

        def repl(m):
            idx = len(defs) + 1
            defs.append(m.group(1).strip())
            return f"[^x{idx}]"

        out.append(INLINE_FN.sub(repl, line))

    if defs:
        out.append("")
        for i, text in enumerate(defs, 1):
            out.append(f"[^x{i}]: {text}")

    return "\n".join(out)
