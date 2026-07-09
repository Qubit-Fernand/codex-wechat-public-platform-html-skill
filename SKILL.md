---
name: wechat-public-platform-html
description: Generate, extract, and organize WeChat public account article HTML from user-provided push-notification content or mp.weixin.qq.com source links. Use when the user asks for 微信公众平台html, 公众号 HTML, 秀米/微信公众号排版迁移, previewable full HTML, WeChat-editor HTML fragments, 去头尾 HTML 可搬运到微信平台, image placeholder rectangles, or workflow outputs for both browser-preview HTML and WeChat backend pasteable HTML.
---

# WeChat Public Platform HTML

Use this skill for two related workflows:

1. Turn a draft article into generated WeChat HTML files.
2. Extract compact hyperlink-template HTML from a full `mp.weixin.qq.com` source page.

For generated draft articles, output two files:

1. `*.full.html`: a complete browser-preview document with `<!doctype html>`, `<html lang="zh-CN">`, `<head>`, preview CSS, and real images preserved when provided.
2. `*.wechat-fragment.html`: the "去头尾 HTML，可搬运到微信平台" version for the WeChat public platform editor or source-editing browser extensions. It contains only the article body fragment and must not include `doctype/html/head/style/body/main`. Replace every local or missing image with an equal-ratio placeholder rectangle that tells the user which image to upload there.

The current generator recreates a red WeChat/Xiumi-style visual system: deep-red section headers, 14px / 1.8 body text, editor-note block, image spacing, credits, and an optional bottom quote card.

## Workflow

### Draft-to-HTML generation

1. Parse the user's push content into a JSON spec. If images are mentioned, create one `image` block per image with a clear `label`. Include `src`/`path` only when the user supplied an actual URL or local path.
2. Run:

```bash
python3 scripts/generate_wechat_html.py <spec.json> --out-dir <output-dir>
```

3. Return the two generated file paths. Call the `*.wechat-fragment.html` file "去头尾 HTML，可搬运到微信平台" in user-facing replies, and remind the user that this is the file to paste into the WeChat editor/plugin source box.

Prefer writing the JSON spec in the current project/workspace, not inside the skill folder.

### Source-link extraction

When the user provides a public WeChat article URL and wants a reusable template or compact hyperlink HTML:

1. Fetch the full page with `curl -L` into the working project or template folder. Prefer naming it `full.html`.
2. Run:

```bash
python3 scripts/extract_wechat_article_html.py \
  full.html \
  --source-url 'https://mp.weixin.qq.com/s/...' \
  --out hyperlink.html
```

3. If this is intended as a reusable template, also copy `hyperlink.html` to `source.html`.
4. Keep `full.html` when future re-extraction may be useful, but use `source.html` / `hyperlink.html` as the default lightweight preview/reference and as the preferred base for derived posts.

Use this extraction route to avoid the full WeChat runtime page size. Raw `mp.weixin.qq.com` pages are often several MB; extracted article/template HTML is usually much smaller and closer to the useful editor content.

The compact hyperlink output must force `#js_content` visible. WeChat source pages often mark the article body as `visibility: hidden; opacity: 0;` and rely on WeChat runtime JavaScript to reveal it; static local previews do not run that runtime.

## JSON Spec

Use this shape:

```json
{
  "title": "活动标题",
  "editor_note": {
    "label": "编者按",
    "text": "开头导语。也可以用 html 字段放内联加粗。"
  },
  "sections": [
    {
      "heading": "活动亮点",
      "blocks": [
        { "type": "paragraph", "html": "<strong>轻松加入：</strong>不需要提前准备。" },
        { "type": "paragraph", "html": "<strong>内容丰富：</strong>摊位包含手作、桌游、摄影。" }
      ]
    },
    {
      "heading": "现场剪影",
      "blocks": [
        {
          "type": "image",
          "label": "现场剪影 01｜主视觉横图",
          "path": "/absolute/local/image.jpg",
          "ratio": 1.3333333,
          "data_w": 1080,
          "width": "100%"
        }
      ]
    }
  ],
  "credits": ["策划：宣传部", "编辑：某某"],
  "footer_card": {
    "text": "惟楚有材，于斯为盛。",
    "image": {
      "label": "底部卡片｜协会图片",
      "ratio": 1.5384615,
      "width": "76%"
    }
  }
}
```

Notes:

- `ratio` means width / height. If unknown, infer from the image file when possible; otherwise use `1.3333333` for landscape, `0.75` for portrait, or ask only if the image placement depends on exact shape.
- `width` controls displayed width and accepts values like `"100%"`, `"76%"`, or `"73%"`.
- Use `html` for paragraphs when bold labels are needed, for example `<strong>报名方式：</strong>扫描二维码加入群聊。`
- The full HTML preserves image URLs/local paths. Local absolute paths become `file://...` for browser preview.
- The "去头尾 HTML，可搬运到微信平台" output (`*.wechat-fragment.html`) always uses placeholder rectangles instead of `<img>` tags. The user should upload local pictures inside the WeChat editor afterward.

## Image URL Strategy

For local interview photos or event photos, do not expect the WeChat public platform backend to load `file://`, absolute local paths, or relative `assets/...` paths after paste. For images extracted from an existing public WeChat article, first check whether the original `src` / `data-src` already points to a WeChat CDN such as `mmbiz.qpic.cn`, `mmbiz.qlogo.cn`, or `mmbiz.qpic.cn/sz_mmbiz_*`.

Use one of these strategies:

1. Safest default: generate a preview HTML with real local images, and generate a "去头尾 HTML，可搬运到微信平台" file (`*.wechat-fragment.html`) with equal-ratio placeholder blocks plus an image manifest; the user manually uploads each local image in the WeChat editor.
2. If the image already has a stable WeChat CDN URL such as `mmbiz.qpic.cn` or `mmbiz.qlogo.cn`, preserve that remote URL in `src` and `data-src`.
3. Verified bridge workflow: if the image is truly local or only available from a non-WeChat source, upload it to a mainland-accessible temporary public object-storage URL, paste/import the HTML into the WeChat editor, save the draft, then check whether WeChat rehosts those images into its own media/CDN.

Avoid Google Drive, GitHub raw links, and overseas-only storage for WeChat paste/import workflows because mainland access may be blocked or slow.

## WeChat Cover Sizes

For WeChat public-account cover assets, use the two-ratio splice workflow by default when the user mentions the cover/crop workflow:

- Wide cover: `2538x1080` pixels, aspect ratio `2.35:1`.
- Square share cover: `1080x1080` pixels, aspect ratio `1:1`.
- Combined upload/crop helper image: `3618x1080` pixels, made by placing the `2538x1080` wide cover on the left and the `1080x1080` square cover on the right.

For generated posts, store these under the post's `assets/wechat_cover_outputs/` directory with names like:

- `*_cover_2_35x1.png`
- `*_cover_1x1.png`
- `*_cover_combined_for_wechat_crop.png`

## Important Rules

- Never paste a complete HTML document into the WeChat public platform editor or source box. It can render `<style>body {...}</style>` as article text.
- Paste only the "去头尾 HTML，可搬运到微信平台" content from `*.wechat-fragment.html`.
- Keep styles inline. WeChat strips or changes many external/global CSS rules.
- Use the stable table-based editor-note block generated by the script; it avoids float/inline-block "编者按" drift after paste.
- For user-facing guidance, avoid abstract names like "pasteable fragment" when possible. Say: first import the "去头尾 HTML，可搬运到微信平台" file, then delete each placeholder rectangle and use WeChat's own "图片 -> 本地上传" to insert the matching local image.
- For source extraction, keep both full and compact files when archiving a template: `full.html` for provenance, `hyperlink.html` for the extracted preview/editing base, and `source.html` as the default template entry.
