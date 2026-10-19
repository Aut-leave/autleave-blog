#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 xishi-secret.md 编译成加密数据文件 static/xishi/secret.json

用法:
    python build-xishi.py

原理:
    借用 Hugo 自己来渲染 Markdown（临时建一个页面，导出 HTML 后删掉），
    这样夕拾页面的语法和站上其他页面完全一致。
    然后把 HTML 加密，写进 secret.json，登录成功后才由前端解密。

    这不是真正的加密，只是「障眼法」——防止别人 Ctrl+U 直接看到正文。
"""

import base64
import os
import hashlib
import json
import shutil
import subprocess
import time
import sys
from pathlib import Path

from mdutils import convert_inline_footnotes

BLOG = Path(__file__).resolve().parent
SRC = BLOG / "xishi-secret.md"
OUT = BLOG / "static" / "xishi" / "secret.json"

TMP_CONTENT = BLOG / "content" / "zz-tmpsecret"
TMP_OUT = BLOG / ".hugo-tmp"

KEY = b"xishi-2026-sql-injection"

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def make_env():
    """Hugo 在 TEMP 为空时会直接 panic，这里兜一个可用目录"""
    env = os.environ.copy()
    tmp = str(BLOG / ".hugo-tmp-env")
    os.makedirs(tmp, exist_ok=True)
    env["TEMP"] = tmp
    env["TMP"] = tmp
    return env


def find_hugo():
    local = BLOG.parent / ".tools" / "hugo.exe"
    if local.exists():
        return str(local)
    found = shutil.which("hugo")
    if found:
        return found
    return None


def render_with_hugo(md: str, hugo: str) -> str:
    """用 Hugo 渲染 Markdown，返回正文 HTML"""
    TMP_CONTENT.mkdir(parents=True, exist_ok=True)
    page = TMP_CONTENT / "index.md"
    page.write_text(
        "---\ntitle: xishi-tmp\ntype: rawhtml\ndraft: false\n---\n\n" + md,
        encoding="utf-8",
    )

    try:
        # --noBuildLock: 避免和正在运行的 hugo server 抢锁
        cmd = [hugo, "--quiet", "--noBuildLock", "--destination", str(TMP_OUT)]
        env = make_env()
        last_err = None
        for attempt in range(3):
            try:
                subprocess.run(cmd, cwd=str(BLOG), check=True, capture_output=True, env=env)
                last_err = None
                break
            except subprocess.CalledProcessError as e:
                last_err = e
                time.sleep(0.6)
        if last_err is not None:
            raise last_err
        html = (TMP_OUT / "zz-tmpsecret" / "index.html").read_text(encoding="utf-8")
    finally:
        shutil.rmtree(TMP_CONTENT, ignore_errors=True)
        shutil.rmtree(TMP_OUT, ignore_errors=True)

    return html.strip()


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

    hugo = find_hugo()
    if not hugo:
        print("[错误] 找不到 hugo，无法渲染 Markdown")
        print("确认 .tools\\hugo.exe 存在，或把 hugo 加到 PATH")
        return 1

    md = SRC.read_text(encoding="utf-8-sig")
    md = convert_inline_footnotes(md)
    try:
        body = render_with_hugo(md, hugo)
    except subprocess.CalledProcessError as e:
        print("[错误] Hugo 渲染失败")
        print(e.stderr.decode("utf-8", "replace")[:800])
        return 1

    cipher = encrypt(body.encode("utf-8"))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"c": cipher}, ensure_ascii=False), encoding="utf-8")

    print(f"源文件: {SRC}  ({len(md)} 字符)")
    print(f"渲染后: {len(body)} 字符 HTML（由 Hugo 生成）")
    print(f"密文:   {len(cipher)} 字符 base64")
    print(f"已写入: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
