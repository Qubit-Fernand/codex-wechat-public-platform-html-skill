# Codex WeChat Public Platform HTML Skill

A Codex skill for generating and extracting WeChat public-account article HTML.

It supports three workflows:

- Generate a complete browser-preview HTML file and a WeChat-editor pasteable body fragment from a compact JSON article spec.
- Prepare a temporary-public-image bridge fragment so WeChat can fetch local article images and rehost them after the draft is saved.
- Extract a compact, previewable article template from a saved `mp.weixin.qq.com` page.

Generated fragments are intended for the WeChat public platform editor or source-editing browser extensions. Keep styles inline and never paste the complete `*.full.html` document into the editor.

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
- `*.wechat-fragment.html`: body-only HTML stripped from the full preview, preserving image tags for local preview.

Only paste body fragments into the WeChat editor/source box. Do not paste the full HTML document.

## Use With The Inshub Chrome Extension

The generated `*.wechat-fragment.html` and `*.wechat-bridge-fragment.html`
files can be used with the Inshub WeChat editor extension:

[https://aigc.inshub.cn/chrome/](https://aigc.inshub.cn/chrome/)

In the WeChat public platform editor, click the green `</>` button labeled
`编辑源代码`, replace the source with the generated body-only fragment, then
click `编辑源代码` again to render the article back in the visual editor.

## Prepare A WeChat Image Bridge

For articles with local images, first keep `*.wechat-fragment.html` as the stripped-body local preview. Then generate a bridge fragment whose local images point to a temporary public HTTPS host:

```bash
python3 scripts/prepare_wechat_image_bridge.py out/示例活动推送.full.html \
  --copy-to out/bridge-site/public/images \
  --base-url 'https://example.com' \
  --out out/示例活动推送.wechat-bridge-fragment.html \
  --manifest out/wechat-image-bridge-manifest.md
```

If the public base URL is not ready yet, use `--base-url '__BRIDGE_BASE_URL__'` and name the output `*.wechat-bridge-fragment.template.html`. After deployment, replace the placeholder with the final HTTPS URL.

After pasting/importing the bridge fragment, save the draft and confirm WeChat rewrote the temporary image URLs to `mmbiz.qpic.cn` or `mmbiz.qlogo.cn` before deleting the temporary host.

## Extract From WeChat Source Page

Save the source article first:

```bash
curl -L 'https://mp.weixin.qq.com/s/...' -o full.html
python3 scripts/extract_wechat_article_html.py full.html \
  --source-url 'https://mp.weixin.qq.com/s/...' \
  --out hyperlink.html
```

The extractor keeps the useful article body, hydrates lazy-loaded image URLs where possible, and forces `#js_content` visible for static local preview.

## Assets

This package includes reusable template and Peking University / Hubei Association assets used by the skill instructions. Before redistributing derived packages, make sure every added asset has an appropriate license and does not include private information.

## License

MIT. See [LICENSE](LICENSE).
