#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obsidian -> Hugo 同步（单向，规则驱动，保留文件夹层级）

发布判定优先级（高 → 低）：
    1. 笔记 front matter 里的 publish: true / false
    2. rules.json 的 exclude
    3. rules.json 的 include
    4. rules.json 的 default（private / public）

用法:
    python sync-notes.py            # 试运行，只打印计划，不写任何文件
    python sync-notes.py --write    # 真正生成到 content/notes/
"""

import argparse
import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

from mdutils import convert_inline_footnotes

# ---------------------------------------------------------------- 配置
VAULT = Path(r"C:\Users\yr070\Desktop\Autleave-人生速通计划\计算机\CTF\obsidian")
BLOG = Path(__file__).resolve().parent
OUT = BLOG / "content" / "notes"
IMG_OUT = BLOG / "static" / "images"
RULES = BLOG / "sync" / "rules.json"

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# ---------------------------------------------------------------- 工具
def clean_title(stem: str) -> str:
    t = stem.strip()
    t = re.sub(r"^\d+\.\s*", "", t)
    t = re.sub(r"^\s*\[[^\]]{1,12}\]\s*", "", t)
    return t.strip() or stem.strip()


def leading_number(stem: str):
    m = re.match(r"^(\d+)\.", stem.strip())
    return int(m.group(1)) if m else None


def slugify(text: str) -> str:
    t = unicodedata.normalize("NFKC", text)
    s = "".join(ch.lower() if ch.isalnum() else "-" for ch in t)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "note"


def yaml_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def iso_date(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%dT%H:%M:%S+08:00")


# ---------------------------------------------------------------- 索引
def build_index():
    notes = {}
    for p in VAULT.rglob("*.md"):
        if ".obsidian" in p.parts:
            continue
        notes[p.stem] = {
            "path": p,
            "stem": p.stem,
            "title": clean_title(p.stem),
            "weight": leading_number(p.stem),
            "rel": p.relative_to(VAULT).as_posix(),
            "parts": list(p.relative_to(VAULT).parent.parts),
        }
    return notes


def build_image_index():
    imgs = {}
    for p in VAULT.rglob("*"):
        if ".obsidian" in p.parts or not p.is_file():
            continue
        if p.suffix.lower() in IMAGE_EXT:
            imgs[p.name] = p
    return imgs


def load_rules():
    if RULES.exists():
        try:
            return json.loads(RULES.read_text(encoding="utf-8-sig"))
        except Exception as e:
            print(f"[错误] rules.json 解析失败: {e}")
            raise SystemExit(1)
    return {"default": "private", "include": [], "exclude": []}


def glob_to_re(pattern: str):
    """"WEB/**" 这种 glob 转正则，支持 **、*、?"""
    out, i = [], 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*" and i + 1 < len(pattern) and pattern[i + 1] == "*":
            i += 2
            if i < len(pattern) and pattern[i] == "/":
                i += 1
                out.append("(?:.*/)?")
            else:
                out.append(".*")
            continue
        if c == "*":
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def read_publish(path: Path):
    """读 front matter 里的 publish，支持 true/false/yes/no/1/0，带不带引号都行"""
    try:
        head = path.read_text(encoding="utf-8-sig")[:4000]
    except Exception:
        return None
    head = head.lstrip("\ufeff \t\r\n")
    if not head.startswith("---"):
        return None
    block = head.split("---", 2)
    if len(block) < 3:
        return None
    m = re.search(
        r"""^publish:\s*['"]?(true|false|yes|no|1|0)['"]?\s*(?:#.*)?$""",
        block[1], re.MULTILINE | re.IGNORECASE)
    if not m:
        return None
    return m.group(1).lower() in ("true", "yes", "1")


def decide(rel: str, rules: dict, fm_value):
    """返回 (是否发布, 理由)"""
    if fm_value is not None:
        return fm_value, "frontmatter"
    for pat in rules.get("exclude", []) or []:
        if glob_to_re(pat).match(rel):
            return False, f"exclude: {pat}"
    for pat in rules.get("include", []) or []:
        if glob_to_re(pat).match(rel):
            return True, f"include: {pat}"
    return (rules.get("default", "private") == "public"), "default"


# ---------------------------------------------------------------- 转换
EMBED = re.compile(r"!\[\[(.+?)\]\]")
LINK = re.compile(r"\[\[(.+?)\]\]")
STANDALONE_LINK = re.compile(r"^[ \t]*(\[[^\]\n]+\]\([^)\n]+\))[ \t]*$", re.MULTILINE)


def convert(text, index, url_of, images, stats, used_images):
    def embed(m):
        target = m.group(1).split("|")[0].strip()
        src = images.get(target)
        if not src:
            stats["missing_images"].append(target)
            return f"*[缺失图片: {target}]*"
        name = slugify(Path(target).stem) + src.suffix.lower()
        used_images.add((src, name))
        return f"![](/images/{name})"

    text = EMBED.sub(embed, text)

    def link(m):
        raw = m.group(1)
        alias = heading = None
        if "|" in raw:
            raw, alias = raw.split("|", 1)
            alias = alias.strip()
        if "#" in raw:
            raw, heading = raw.split("#", 1)
            heading = heading.strip()
        target = raw.strip()

        note = index.get(target)
        if note is None:
            stats["unresolved"].append(target)
            return alias or target

        if note["stem"] not in url_of:
            stats["private_links"].append(target)
            return alias or note["title"]

        label = alias or note["title"]
        anchor = ("#" + slugify(heading)) if heading else ""
        return f"[{label}]({url_of[note['stem']]}{anchor})"

    text = LINK.sub(link, text)
    return STANDALONE_LINK.sub(r"- \1", text)


def front_matter(title, date, weight, extra=None):
    lines = ["---", f"title: {yaml_str(title)}", f"date: {date}"]
    if weight is not None:
        lines.append(f"weight: {weight}")
    for k, v in (extra or {}).items():
        lines.append(f"{k}: {v}")
    lines += ["draft: false", "---", ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    if not VAULT.exists():
        print(f"[错误] 找不到库: {VAULT}")
        return 1

    index = build_index()
    images = build_image_index()
    rules = load_rules()

    # ---- 规则扫描：整库自动判定
    selected, skipped = [], []
    for n in sorted(index.values(), key=lambda x: x["rel"]):
        ok, why = decide(n["rel"], rules, read_publish(n["path"]))
        n["reason"] = why
        (selected if ok else skipped).append(n)

    # 哪些笔记要当作“文件夹首页”：
    #   a) 同名文件夹存在      WEB/http.md + WEB/http/
    #   b) 自己就是文件夹同名笔记  WEB/http/http.md
    def is_folder_note(note):
        parts = note["parts"]
        if parts and parts[-1] == note["stem"]:
            return True
        return (VAULT.joinpath(*parts) / note["stem"]).is_dir()

    pages = []          # (note, dest_rel, is_section_index)
    url_of = {}         # stem -> /notes/...
    used_dests = {}

    for n in selected:
        leaf = slugify(n["title"])
        if is_folder_note(n):
            dirs = [slugify(p) for p in n["parts"]]
            if n["parts"] and n["parts"][-1] == n["stem"]:
                dirs = dirs[:-1]          # 文件夹同名笔记：退一层
            dest = "/".join(dirs + [leaf] + ["_index.md"])
            is_sec = True
        else:
            dirs = [slugify(p) for p in n["parts"]]
            dest = "/".join(dirs + [leaf + ".md"])
            is_sec = False
        url = "/notes/" + "/".join(dirs + [leaf]) + "/"
        if dest in used_dests:
            print(f"[错误] 目标冲突: {dest}\n  - {used_dests[dest]}\n  - {n['rel']}")
            return 1
        used_dests[dest] = n["rel"]
        pages.append((n, dest, is_sec, url))
        url_of[n["stem"]] = url

    # ---- 需要生成的文件夹 _index.md
    folder_pages = {}
    for n, dest, is_sec, url in pages:
        parts = n["parts"]
        for i in range(len(parts)):
            dirs = [slugify(p) for p in parts[: i + 1]]
            d = "/".join(dirs + ["_index.md"])
            if d not in folder_pages:
                folder_pages[d] = {
                    "title": parts[i],
                    "date": iso_date(n["path"]),
                    "weight": None,
                    "body": "",
                }
        if is_sec:
            folder_pages[dest] = {"title": n["title"], "date": iso_date(n["path"]),
                                  "weight": n["weight"], "body": None}  # 正文稍后填

    # ---- 转换正文
    stats = {"unresolved": [], "private_links": [], "missing_images": []}
    used_images = set()
    generated = {}

    for n, dest, is_sec, url in pages:
        raw = n["path"].read_text(encoding="utf-8-sig")
        if raw.startswith("---"):
            bits = raw.split("---", 2)
            if len(bits) == 3:
                raw = bits[2]
        raw = convert_inline_footnotes(raw)
        body = convert(raw, index, url_of, images, stats, used_images)
        generated[dest] = {"title": n["title"], "date": iso_date(n["path"]),
                           "weight": n["weight"], "body": body, "note": n}

    # 把文件夹页和笔记页合并
    final = dict(generated)
    for d, meta in folder_pages.items():
        if d not in final:
            final[d] = dict(meta, note=None, body=meta["body"] or "")

    # ---- 目录排序：同层里英文在前、中文在后，按名称排
    from collections import defaultdict
    groups = defaultdict(list)
    for d in final:
        if d.endswith("_index.md"):
            groups["/".join(d.split("/")[:-2])].append(d)
    for parent, ds in groups.items():
        ds.sort(key=lambda d: (0 if final[d]["title"].isascii() else 1,
                               final[d]["title"].lower()))
        for i, d in enumerate(ds):
            final[d]["weight"] = (i + 1) * 10


    # ---------------- 报告
    print(f"库: {VAULT}")
    print(f"库内 md: {len(index)}   发布: {len(selected)}   不发布: {len(skipped)}   页面: {len(final)}")
    print("规则: default={}  include={} 条  exclude={} 条".format(
        rules.get("default", "private"),
        len(rules.get("include", []) or []),
        len(rules.get("exclude", []) or [])))

    if skipped:
        print(f"\n不发布 {len(skipped)} 篇:")
        for n in skipped:
            print(f"  · {n['rel']}   ({n['reason']})")

    print(f"\n将生成 {len(final)} 个文件:")
    for d in sorted(final):
        indent = "  " * (d.count("/"))
        print(f"  {d}")

    if used_images:
        print(f"\n图片 {len(used_images)} 张:")
        for src, name in sorted(used_images, key=lambda x: x[1]):
            print(f"  {src.name} → /images/{name}")
    if stats["missing_images"]:
        print(f"\n[警告] 找不到图片: {stats['missing_images']}")
    if stats["private_links"]:
        print(f"\n[提示] {len(stats['private_links'])} 处链接指向未发布笔记，已降级为纯文本")
    if stats["unresolved"]:
        print(f"\n[警告] 链接目标不存在: {sorted(set(stats['unresolved']))}")

    if not args.write:
        print("\n试运行结束。确认后加 --write 生成。")
        return 0

    # ---------------- 写入
    OUT.mkdir(parents=True, exist_ok=True)
    IMG_OUT.mkdir(parents=True, exist_ok=True)

    keep = set()
    for d, meta in final.items():
        dest = OUT / d
        dest.parent.mkdir(parents=True, exist_ok=True)
        fm = front_matter(meta["title"], meta["date"], meta.get("weight"))
        dest.write_text(fm + "\n" + (meta.get("body") or "").strip() + "\n", encoding="utf-8")
        keep.add(dest.resolve())

    # 手写文件保护
    keep.add((OUT / "_index.md").resolve())

    removed = 0
    for p in sorted(OUT.rglob("*.md"), key=lambda x: -len(str(x))):
        if p.resolve() not in keep:
            p.unlink()
            removed += 1
    for p in sorted(OUT.rglob("*"), key=lambda x: -len(str(x))):
        if p.is_dir() and not any(p.iterdir()):
            p.rmdir()

    for src, name in used_images:
        shutil.copy2(src, IMG_OUT / name)

    print(f"\n[完成] 写入 {len(final)} 个文件，清理 {removed} 个过期文件，图片 {len(used_images)} 张")
    return 0


if __name__ == "__main__":
    sys.exit(main())
