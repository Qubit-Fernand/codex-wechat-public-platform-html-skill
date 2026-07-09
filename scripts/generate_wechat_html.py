#!/usr/bin/env python3
"""Generate WeChat public-account HTML from a compact JSON spec."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from urllib.parse import quote


RED = "rgb(139, 0, 18)"
TEXT = "rgb(62, 62, 62)"
MUTED = "rgb(102, 102, 102)"


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def slug(value: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|]+', "-", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:80] or "wechat-article"


def as_src(image: dict) -> str:
    src = image.get("src") or image.get("url") or image.get("path") or ""
    if not src:
        return ""
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", src):
        return src
    p = Path(src).expanduser()
    if p.is_absolute():
        return p.as_uri()
    return quote(src)


def divider() -> str:
    return (
        '<section style="margin: 0.5em 0px;box-sizing: border-box;">'
        f'<section style="background-color: {RED};height: 1px;box-sizing: border-box;">'
        '<svg viewBox="0 0 1 1" style="float:left;line-height:0;width:0;vertical-align:top;"></svg>'
        "</section></section>"
    )


def editor_note(label: str, body_html: str) -> str:
    label = label or "编者按"
    chars = "".join(
        f'<p style="margin: 0px;padding: 0px;box-sizing: border-box;"><b><span>{esc(ch)}</span></b></p>'
        for ch in label
    )
    return f"""
<section style="margin: 15px 0%;box-sizing: border-box;">
  <table style="border-collapse: collapse;border-spacing: 0;width: 100%;box-sizing: border-box;" cellspacing="0" cellpadding="0">
    <tbody><tr>
      <td style="width: 54px;vertical-align: top;text-align: center;box-sizing: border-box;">
        <section style="display: inline-block;border-left: 1px solid rgb(160, 160, 160);border-right: 1px solid rgb(160, 160, 160);padding: 0px 6px;color: {RED};font-size: 16px;line-height: 1.45;box-sizing: border-box;">
          {chars}
        </section>
      </td>
      <td style="vertical-align: top;padding: 0px 0px 0px 10px;box-sizing: border-box;">
        <section style="color: {MUTED};line-height: 1.8;box-sizing: border-box;">
          <p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;">{body_html}</p>
        </section>
      </td>
    </tr></tbody>
  </table>
</section>""".strip()


def heading(title: str) -> str:
    return f"""
<section style="display: flex;flex-flow: row;margin: 10px 0%;justify-content: flex-start;box-sizing: border-box;">
  <section style="display: inline-block;vertical-align: middle;width: auto;min-width: 10%;max-width: 100%;flex: 0 0 auto;height: auto;align-self: center;box-sizing: border-box;">
    <section style="text-align: center;margin: 0px 0%;box-sizing: border-box;">
      <section style="display: inline-block;min-width: 10%;max-width: 100%;vertical-align: top;transform: matrix(1, 0, -0.2, 1, 0, 0);-webkit-transform: matrix(1, 0, -0.2, 1, 0, 0);-moz-transform: matrix(1, 0, -0.2, 1, 0, 0);-o-transform: matrix(1, 0, -0.2, 1, 0, 0);border-style: none none none solid;border-width: 0px 0px 0px 5px;border-color: {TEXT} {TEXT} {TEXT} {RED};padding: 0px 0px 0px 2px;background-color: rgba(255, 255, 255, 0);box-shadow: rgb(0, 0, 0) 0px 0px 0px;box-sizing: border-box;">
        <section style="justify-content: center;display: flex;flex-flow: row;width: 100%;border-left: 2px solid {RED};border-bottom-left-radius: 0px;padding: 0px 6px;align-self: flex-start;box-sizing: border-box;">
          <section style="color: {RED};letter-spacing: 1px;padding: 0px;font-size: 16px;text-align: justify;width: 100%;box-sizing: border-box;">
            <p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;"><b style="box-sizing: border-box;"><span>{esc(title)}</span></b></p>
          </section>
        </section>
      </section>
    </section>
  </section>
  <section style="display: inline-block;vertical-align: middle;width: auto;flex: 100 100 0%;align-self: center;height: auto;box-sizing: border-box;">
    {divider()}
  </section>
</section>""".strip()


def paragraph(text: str = "", html_text: str = "") -> str:
    content = html_text if html_text else esc(text)
    return f'<p style="white-space: normal;margin: 0px;padding: 0px;box-sizing: border-box;"><span>{content}</span></p>'


def paragraph_group(blocks: list[dict]) -> str:
    parts = []
    for block in blocks:
        if block.get("type", "paragraph") == "paragraph":
            parts.append(paragraph(block.get("text", ""), block.get("html", "")))
    return '<section style="box-sizing: border-box;">' + "".join(parts) + "</section>"


def image_html(image: dict) -> str:
    width = image.get("width", image.get("width_percent", "100%"))
    ratio = float(image.get("ratio") or 0.75)
    data_w = esc(image.get("data_w") or image.get("data-w") or "")
    src = esc(as_src(image))
    label = esc(image.get("label") or "图片")
    if not src:
        return placeholder_html(image)
    return f"""
<section style="text-align: center;margin-top: 10px;margin-bottom: 10px;line-height: 0;box-sizing: border-box;">
  <section style="max-width: 100%;vertical-align: middle;display: inline-block;line-height: 0;width: {esc(width)};height: auto;box-sizing: border-box;" nodeleaf="">
    <img src="{src}" alt="{label}" class="rich_pages wxw-img" data-ratio="{ratio:g}" data-w="{data_w}" style="vertical-align: middle; max-width: 100%; width: 100%; box-sizing: border-box; height: auto;" width="100%">
  </section>
</section>""".strip()


def placeholder_html(image: dict) -> str:
    width = image.get("width", image.get("width_percent", "100%"))
    ratio = float(image.get("ratio") or 0.75)
    data_w = esc(image.get("data_w") or image.get("data-w") or "未知")
    label = esc(image.get("label") or "图片")
    note = esc(image.get("note") or "请在此处替换本地图片")
    height_percent = 100 / ratio if ratio > 0 else 75
    ratio_text = f"{ratio:.3f}:1" if ratio > 0 else "未知"
    return f"""
<section style="text-align: center;margin-top: 10px;margin-bottom: 10px;line-height: 0;box-sizing: border-box;">
  <section style="max-width: 100%;vertical-align: middle;display: inline-block;line-height: 0;width: {esc(width)};height: auto;box-sizing: border-box;" nodeleaf="">
    <section data-placeholder-image="{label}" style="vertical-align: middle;max-width: 100%;width: 100%;box-sizing: border-box;height: auto;display: block;">
      <section style="width: 100%;height: 0;padding-bottom: {height_percent:.3f}%;background-color: rgb(248, 248, 248);border: 1px dashed {RED};box-sizing: border-box;position: relative;">
        <section style="position: absolute;left: 0;right: 0;top: 50%;transform: translateY(-50%);padding: 0px 12px;text-align: center;color: {RED};font-size: 14px;line-height: 1.6;box-sizing: border-box;">
          <p style="margin: 0px;padding: 0px;box-sizing: border-box;"><strong>{label}</strong></p>
          <p style="margin: 0px;padding: 0px;box-sizing: border-box;">{note}</p>
          <p style="margin: 0px;padding: 0px;box-sizing: border-box;color: {MUTED};font-size: 12px;">原 data-w={data_w}，比例 {ratio_text}</p>
        </section>
      </section>
    </section>
  </section>
</section>""".strip()


def credits(items: list[str]) -> str:
    rows = []
    for item in items:
        rows.append(
            f'<p style="text-align: right;margin: 0px;padding: 0px;box-sizing: border-box;">'
            f'<span style="font-size: 12px;color: {MUTED};box-sizing: border-box;"><span>{esc(item)}</span></span></p>'
        )
    return '<section style="text-align: center;box-sizing: border-box;">' + "".join(rows) + "</section>"


def quote_card(text: str, image: dict | None, placeholders: bool) -> str:
    image_part = placeholder_html(image) if placeholders and image else image_html(image or {})
    return f"""
<section style="text-align: center;margin: 10px 0%;justify-content: center;display: flex;flex-flow: row;box-sizing: border-box;">
  <section style="display: inline-block;width: 95%;vertical-align: top;box-shadow: rgb(178, 185, 192) 1px 0px 10px;align-self: flex-start;flex: 0 0 auto;box-sizing: border-box;">
    {image_part}
    <section style="margin-top: 10px;margin-bottom: 10px;box-sizing: border-box;">
      <section style="display: inline-block;padding: 3px;background-color: rgb(134, 193, 212);box-sizing: border-box;">
        <section style="padding: 2px 8px;border: 1px dotted rgb(255, 255, 255);color: rgb(255, 255, 255);line-height: 1.4em;font-size: 11px;box-sizing: border-box;">
          <p style="margin: 0px;padding: 0px;box-sizing: border-box;"><span>{esc(text)}</span></p>
        </section>
      </section>
    </section>
  </section>
</section>""".strip()


def render_fragment(spec: dict, placeholders: bool) -> str:
    parts = [
        f'<section style="font-size: 14px;line-height: 1.8;padding: 0px 20px;box-sizing: border-box;font-style: normal;font-weight: 400;text-align: justify;color: {TEXT};">',
        divider(),
    ]
    note = spec.get("editor_note") or {}
    if note:
        parts.append(editor_note(note.get("label", "编者按"), note.get("html") or esc(note.get("text", ""))))
        parts.append(divider())
    for section in spec.get("sections", []):
        title = section.get("heading") or section.get("title")
        if title:
            parts.append(heading(title))
        paragraph_blocks = []
        for block in section.get("blocks", []):
            kind = block.get("type", "paragraph")
            if kind == "paragraph":
                paragraph_blocks.append(block)
            else:
                if paragraph_blocks:
                    parts.append(paragraph_group(paragraph_blocks))
                    paragraph_blocks = []
                if kind == "image":
                    parts.append(placeholder_html(block) if placeholders else image_html(block))
                elif kind == "html":
                    parts.append(block.get("html", ""))
        if paragraph_blocks:
            parts.append(paragraph_group(paragraph_blocks))
    if spec.get("credits"):
        parts.append(credits(spec["credits"]))
    card = spec.get("footer_card")
    if card:
        parts.append(quote_card(card.get("text", ""), card.get("image"), placeholders))
    parts.append("</section>")
    return "\n".join(parts)


def full_html(title: str, fragment: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    body {{
      margin: 0;
      background: #f5f5f5;
      color: #1f2329;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.75;
    }}
    main {{
      box-sizing: border-box;
      width: min(760px, 100%);
      margin: 0 auto;
      padding: 32px 20px 56px;
      background: #fff;
    }}
    img {{
      max-width: 100%;
      height: auto;
    }}
  </style>
</head>
<body>
  <main>
{fragment}
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path, help="JSON article spec")
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    title = spec.get("title") or "wechat-article"
    base = slug(title)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    preview_fragment = render_fragment(spec, placeholders=False)
    placeholder_fragment = render_fragment(spec, placeholders=True)

    full_path = args.out_dir / f"{base}.full.html"
    fragment_path = args.out_dir / f"{base}.wechat-fragment.html"
    full_path.write_text(full_html(title, preview_fragment), encoding="utf-8")
    fragment_path.write_text(placeholder_fragment + "\n", encoding="utf-8")

    print(full_path)
    print(fragment_path)


if __name__ == "__main__":
    main()
