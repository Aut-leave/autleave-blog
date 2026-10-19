#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 xishi-secret.md 编译成加密数据文件 data/xishi.json

用法:
    python build-xishi.py

说明:
    这不是真正的加密，只是「障眼法」——防止别人 Ctrl+U 直接看到正文。
    懂 JS 的人在控制台里跑几行就能解出来，别拿它存真正机密的东西。
"""

import base64
import hashlib
import html
import json
import re
import sys
from pathlib import Path

BLOG = Path(__file__).resolve().parent
SRC = BLOG / "xishi-secret.md"
OUT = BLOG / "static" / "xishi" / "secret.json"

KEY = b"xishi-2026-sql-injection"

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------- 极简 Markdown
def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def md_to_html(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out, i = [], 0
    n = len(lines)

    while i < n:
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        if line.startswith("```"):
            lang = line[3:].strip()
            i += 1
            buf = []
            while i < n and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = f' class="language-{lang}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(buf))}</code></pre>")
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        if line.startswith(">"):
            buf = []
            while i < n and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>" + inline(" ".join(buf)) + "</p></blockquote>")
            continue

        if re.match(r"^\s*[-*+]\s+", line):
            buf = []
            while i < n and re.match(r"^\s*[-*+]\s+", lines[i]):
                buf.append(re.sub(r"^\s*[-*+]\s+", "", lines[i]))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in buf) + "</ul>")
            continue

        if re.match(r"^\s*\d+\.\s+", line):
            buf = []
            while i < n and re.match(r"^\s*\d+\.\s+", lines[i]):
                buf.append(re.sub(r"^\s*\d+\.\s+", "", lines[i]))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(x)}</li>" for x in buf) + "</ol>")
            continue

        if line.strip() in ("---", "***"):
            out.append("<hr>")
            i += 1
            continue

        buf = []
        while i < n and lines[i].strip() and not re.match(r"^(#{1,6}\s|```|>|\s*[-*+]\s|\s*\d+\.\s)", lines[i]):
            buf.append(lines[i])
            i += 1
        out.append("<p>" + inline(" ".join(x.strip() for x in buf)) + "</p>")

    return "\n".join(out)


# ---------------------------------------------------------------- 加解密
def keystream(key: bytes, length: int) -> bytes:
    out = b""
    counter = 0
    while len(out) < length:
        out += hashlib.sha256(key + counter.to_bytes(4, "big")).digest()
        counter += 1
    return out[:length]


def encrypt(plain: bytes) -> str:
    ks = keystream(KEY, len(plain))
    return base64.b64encode(bytes(a ^ b for a, b in zip(plain, ks))).decode()


def main():
    if not SRC.exists():
        print(f"[错误] 找不到 {SRC}")
        print("先创建这个文件，写你的正文（Markdown）。")
        return 1

    md = SRC.read_text(encoding="utf-8-sig")
    body = md_to_html(md)
    cipher = encrypt(body.encode("utf-8"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"c": cipher}, ensure_ascii=False), encoding="utf-8")

    print(f"源文件: {SRC}  ({len(md)} 字符)")
    print(f"渲染后: {len(body)} 字符 HTML")
    print(f"密文:   {len(cipher)} 字符 base64")
    print(f"已写入: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
