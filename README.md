# Codex WeChat Public Platform HTML Skill

A Codex skill for generating and extracting WeChat public-account article HTML.

It supports two workflows:

- Generate a complete browser-preview HTML file and a WeChat-editor pasteable body fragment from a compact JSON article spec.
- Extract a compact, previewable article template from a saved `mp.weixin.qq.com` page.

The generated fragment is intended for the WeChat public platform editor or source-editing browser extensions. It keeps styles inline and replaces local images with equal-ratio placeholder rectangles so images can be uploaded through the WeChat editor.

## Install

Clone this repository and copy it into your Codex skills directory:

```bash
git clone https://github.com/Qubit-Fernand/codex-wechat-public-platform-html-skill.git
mkdir -p ~/.codex/skills
cp -R codex-wechat-public-platform-html-skill ~/.codex/skills/wechat-public-platform-html
```

Restart Codex or reload skills after copying.

## Generate From JSON

```bash
python3 scripts/generate_wechat_html.py examples/basic-article.json --out-dir out
```

This writes:

- `*.full.html`: complete browser-preview document.
- `*.wechat-fragment.html`: body-only HTML for the WeChat editor.

Only paste the `*.wechat-fragment.html` content into the WeChat editor/source box. Do not paste the full HTML document.

## Extract From WeChat Source Page

Save the source article first:

```bash
curl -L 'https://mp.weixin.qq.com/s/...' -o full.html
python3 scripts/extract_wechat_article_html.py full.html \
  --source-url 'https://mp.weixin.qq.com/s/...' \
  --out hyperlink.html
```

The extractor keeps the useful article body, hydrates lazy-loaded image URLs where possible, and forces `#js_content` visible for static local preview.

## Public Package Notes

The original private working skill referenced local template libraries and bundled institution-specific images. This public package keeps the reusable scripts and skill instructions, but does not include private local template archives, logos, or brand assets. Add your own reusable templates under a project folder or under `assets/` as appropriate.

## License

MIT. See [LICENSE](LICENSE).
