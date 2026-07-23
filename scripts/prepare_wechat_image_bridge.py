#!/usr/bin/env python3
"""Prepare a WeChat fragment that points local images at a temporary public host."""

from __future__ import annotations

import argparse
import html
import posixpath
import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urlparse


WECHAT_IMAGE_HOSTS = ("mmbiz.qpic.cn", "mmbiz.qlogo.cn")


def extract_js_content(raw: str) -> str:
    start_match = re.search(r'<div\b(?=[^>]*\bid=["\']js_content["\'])[^>]*>', raw, re.I)
    if not start_match:
        return raw

    pos = start_match.end()
    depth = 1
    token_re = re.compile(r'</?div\b[^>]*>', re.I)
    for match in token_re.finditer(raw, pos):
        token = match.group(0)
        if token.lower().startswith("</div"):
            depth -= 1
            if depth == 0:
                return raw[start_match.start() : match.end()]
        else:
            depth += 1
    raise SystemExit("Could not find closing </div> for #js_content")


def attrs_from_tag(tag: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in re.finditer(r'([:\w-]+)\s*=\s*(["\'])(.*?)\2', tag, flags=re.S):
        attrs[match.group(1).lower()] = html.unescape(match.group(3))
    return attrs


def set_attr(tag: str, name: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    pattern = re.compile(rf'({re.escape(name)}\s*=\s*)(["\']).*?\2', re.I | re.S)
    if pattern.search(tag):
        return pattern.sub(rf'\1"{escaped}"', tag, count=1)
    return tag[:-1].rstrip() + f' {name}="{escaped}">'


def is_wechat_url(value: str) -> bool:
    parsed = urlparse(value if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", value) else "https:" + value)
    return parsed.hostname in WECHAT_IMAGE_HOSTS


def resolve_local_image(value: str, source_dir: Path) -> Path | None:
    if not value or is_wechat_url(value):
        return None
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https", "data"}:
        return None
    if parsed.scheme == "file":
        return Path(unquote(parsed.path))
    path_text = unquote(value.split("?", 1)[0])
    path = Path(path_text)
    if path.is_absolute():
        return path
    return source_dir / path


def unique_destination(target_dir: Path, src: Path, used: set[str]) -> Path:
    stem = src.stem or "image"
    suffix = src.suffix or ".jpg"
    candidate = src.name
    index = 2
    while candidate in used:
        candidate = f"{stem}-{index}{suffix}"
        index += 1
    used.add(candidate)
    return target_dir / candidate


def prepare_fragment(
    raw: str,
    *,
    source_dir: Path,
    base_url: str,
    public_path: str,
    copy_to: Path | None,
) -> tuple[str, list[tuple[Path, str]]]:
    fragment = extract_js_content(raw)
    copied: list[tuple[Path, str]] = []
    used_names: set[str] = set()
    normalized_public_path = "/" + public_path.strip("/")
    normalized_base = base_url.rstrip("/")

    def replace_img(match: re.Match[str]) -> str:
        tag = match.group(0)
        attrs = attrs_from_tag(tag)
        candidate = attrs.get("src") or attrs.get("data-src") or ""
        local = resolve_local_image(candidate, source_dir)
        if local is None:
            return tag
        if not local.exists():
            raise SystemExit(f"Local image does not exist: {local}")

        image_name = local.name
        if copy_to is not None:
            copy_to.mkdir(parents=True, exist_ok=True)
            dest = unique_destination(copy_to, local, used_names)
            shutil.copy2(local, dest)
            image_name = dest.name

        url_path = posixpath.join(normalized_public_path, image_name)
        public_url = normalized_base + url_path
        copied.append((local, public_url))
        tag = set_attr(tag, "src", public_url)
        tag = set_attr(tag, "data-src", public_url)
        return tag

    return re.sub(r"<img\b[^>]*>", replace_img, fragment, flags=re.I | re.S), copied


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("html", type=Path, help="Full preview HTML or existing body fragment.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--base-url",
        default="__BRIDGE_BASE_URL__",
        help="Temporary public origin, for example https://example.com.",
    )
    parser.add_argument("--public-path", default="/images")
    parser.add_argument(
        "--copy-to",
        type=Path,
        help="Optional public image directory to populate, usually bridge-site/public/images.",
    )
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()

    raw = args.html.read_text(encoding="utf-8", errors="ignore")
    fragment, copied = prepare_fragment(
        raw,
        source_dir=args.html.parent,
        base_url=args.base_url,
        public_path=args.public_path,
        copy_to=args.copy_to,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(fragment, encoding="utf-8")

    if args.manifest:
        lines = ["# WeChat image bridge manifest", ""]
        for local, public_url in copied:
            lines.append(f"- `{local}` -> {public_url}")
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(args.out)
    print(f"local images bridged: {len(copied)}")


if __name__ == "__main__":
    main()
