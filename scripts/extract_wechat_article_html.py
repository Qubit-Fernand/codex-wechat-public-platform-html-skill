#!/usr/bin/env python3
"""Extract a compact preview HTML from a raw mp.weixin.qq.com article page."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


def meta_content(raw: str, key: str) -> str:
    pattern = (
        r'<meta\s+(?:property|name)=["\']'
        + re.escape(key)
        + r'["\']\s+content=["\']([^"\']*)["\']'
    )
    match = re.search(pattern, raw, re.I)
    return html.unescape(match.group(1)).strip() if match else ""


def extract_js_content(raw: str) -> str:
    start_match = re.search(r'<div\b(?=[^>]*\bid=["\']js_content["\'])[^>]*>', raw, re.I)
    if not start_match:
        raise SystemExit("Could not find #js_content")

    pos = start_match.end()
    depth = 1
    token_re = re.compile(r"</?div\b[^>]*>", re.I)
    for match in token_re.finditer(raw, pos):
        token = match.group(0)
        if token.lower().startswith("</div"):
            depth -= 1
            if depth == 0:
                return raw[start_match.start() : match.end()]
        else:
            depth += 1
    raise SystemExit("Could not find closing </div> for #js_content")


def hydrate_lazy_images(fragment: str) -> str:
    def repl(match: re.Match[str]) -> str:
        tag = match.group(0)
        if re.search(r'\ssrc=["\']', tag, re.I):
            return tag
        data_src = re.search(r'\sdata-src=(["\'])(.*?)\1', tag, re.I)
        if not data_src:
            return tag
        return tag[:4] + f' src="{html.escape(data_src.group(2), quote=True)}"' + tag[4:]

    return re.sub(r"<img\b[^>]*>", repl, fragment, flags=re.I)


def force_js_content_visible(fragment: str) -> str:
    """Make extracted WeChat article content visible in static previews."""

    div_match = re.search(r'<div\b(?=[^>]*\bid=["\']js_content["\'])[^>]*>', fragment, re.I)
    if not div_match:
        return fragment

    tag = div_match.group(0)
    style_match = re.search(r'\sstyle=(["\'])(.*?)\1', tag, re.I | re.S)
    if style_match:
        style = style_match.group(2)
        style = re.sub(r"visibility\s*:\s*hidden\s*;?", "", style, flags=re.I)
        style = re.sub(r"opacity\s*:\s*0\s*;?", "", style, flags=re.I)
        style = style.strip()
        if style and not style.endswith(";"):
            style += ";"
        style = f"{style} visibility: visible; opacity: 1;".strip()
        tag = tag[: style_match.start()] + f' style="{html.escape(style, quote=True)}"' + tag[style_match.end() :]
    else:
        tag = tag[:-1] + ' style="visibility: visible; opacity: 1;">'

    return fragment[: div_match.start()] + tag + fragment[div_match.end() :]


def build_html(title: str, source_url: str, fragment: str) -> str:
    safe_title = html.escape(title or "WeChat Article", quote=False)
    safe_url = html.escape(source_url, quote=True)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{safe_title}</title>
<style>
  body {{ margin: 0; background: #f6f6f6; color: #111; font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif; }}
  main {{ max-width: 680px; margin: 0 auto; background: #fff; min-height: 100vh; padding: 28px 16px 48px; box-sizing: border-box; }}
  h1 {{ font-size: 22px; line-height: 1.35; margin: 0 0 12px; font-weight: 700; }}
  .meta {{ color: #666; font-size: 14px; margin-bottom: 24px; word-break: break-all; }}
  img {{ max-width: 100%; height: auto; }}
</style>
</head>
<body>
<main>
<h1>{safe_title}</h1>
<div class="meta">source: {safe_url}</div>
{fragment}
</main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_html", type=Path)
    parser.add_argument("--source-url", default="")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    raw = args.raw_html.read_text(encoding="utf-8", errors="ignore")
    title = meta_content(raw, "og:title") or meta_content(raw, "description")
    fragment = force_js_content_visible(hydrate_lazy_images(extract_js_content(raw)))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(build_html(title, args.source_url, fragment), encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
