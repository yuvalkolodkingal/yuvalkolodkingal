# What a GitHub profile README can and cannot do

Read this before designing any panel. Most broken or ugly profiles come from
guessing at these rules.

## Where the README lives

- A repository named exactly like the user (`octocat/octocat`), public, with a
  `README.md` at the root. GitHub shows it at the top of the profile page.
- Relative links and image paths resolve against the default branch, so
  `./assets/x.svg` works once the file is on `main`. On a feature branch the
  images 404 until merged; preview locally instead.

## Markdown and the HTML subset

GitHub renders GitHub Flavored Markdown and then sanitises HTML. What
survives:

- `<img>`, `<a>`, `<p>`, `<div>`, `<table>`, `<tr>`, `<td>`, `<th>`, `<br>`,
  `<hr>`, `<details>`, `<summary>`, `<sub>`, `<sup>`, `<kbd>`, `<picture>`,
  `<source>`, headings, lists, code fences, `<b>`, `<i>`, `<code>`.
- Attributes that survive: `src`, `href`, `alt`, `title`, `width`, `height`,
  `align` (on `<p>`, `<div>`, `<img>`, `<td>`), `valign`, `media` and
  `srcset` (on `<source>`), `open` (on `<details>`).

What is stripped, so never rely on it:

- `<style>`, `<script>`, `<iframe>`, `<object>`, `<embed>`, `<form>`,
  `<input>`, `<video>`, `<audio>`, `<canvas>`, `<svg>` inline.
- `style=""`, `class=""`, `id=""`, `onclick` and every other event attribute.
- CSS of any kind in the Markdown itself. There is no way to set a font, a
  colour or a layout rule on the page. Layout comes from `<table>`,
  `align="center"` and image widths only.

Consequences:

- Anything with a specific colour, font or motion has to be an image. That
  is why this style renders panels as SVG.
- Two-column layouts are a `<table>` with two `<td valign="top">` cells, or
  an `<img align="right">` floated next to text.
- Centering is `<p align="center">` or `<div align="center">`.

## Images

- Every image is fetched through GitHub's camo proxy and cached. Camo strips
  cookies and only serves image content types; a URL that returns HTML shows
  as a broken image.
- Images in the repository are served from `raw.githubusercontent.com` via
  camo. Caching means a changed file can take minutes to update on the
  profile, and a file at the same path with new content is fine (the daily
  workflow relies on this).
- `width` on `<img>` scales the image; give SVGs an explicit width that
  matches their viewBox width so text stays crisp.

## What an SVG may contain when shown through `<img>`

An SVG loaded as an image runs in a locked-down mode. This is the part most
people get wrong.

Works:

- Shapes, paths, text, gradients (`<linearGradient>`, `<radialGradient>`),
  masks, clip paths, filters (`<feGaussianBlur>`, `<feMerge>` glow, etc.).
- SMIL animation (`<animate>`, `<animateTransform>`, `<animateMotion>`,
  `<set>`), including `repeatCount="indefinite"`, `begin` offsets,
  `fill="freeze"`, `calcMode="discrete"` for stepwise motion and `keyTimes`.
- CSS animations and transitions declared in a `<style>` element *inside*
  the SVG (`@keyframes`, `animation`, `transform`), and media queries in that
  same block, which is how `prefers-reduced-motion` is honoured.
- `<title>` for tooltips inside the image (only visible when the SVG is
  opened directly, not through `<img>`, but harmless and good for a11y).
- `role="img"` and `aria-label` on the root, which is the alt text when the
  SVG is opened directly. Still set `alt` on the `<img>` in the README.

Does not work, ever, in this mode:

- `<script>`. Nothing runs.
- External resources of any kind: web fonts via `@import` or `@font-face
  src: url(...)`, external images in `<image href>`, external CSS, `<use>`
  pointing at another file. The image simply renders without them, so a
  panel that depends on a font falls back to the viewer's default.
- `<foreignObject>` with HTML inside it (rendered blank).
- Fetching data at render time. Numbers must be baked in by the generator.

Therefore:

- Use a font stack of system monospace fonts, in this order, and set
  `textLength` + `lengthAdjust="spacing"` on any text whose width must line
  up with a clip or cursor, so every viewer's font lands characters on the
  same grid:
  `ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'DejaVu Sans Mono', 'Liberation Mono', monospace`.
- Treat emoji as two columns wide when computing text widths.
- Keep each SVG under roughly 300 KB. A 53-week calendar with a per-square
  animation is about 130 KB; do not animate squares that have nothing to
  show.

## Light and dark mode

GitHub has both. A dark terminal card on a light page reads as an
intentional terminal window and is fine. If you want a light variant:

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/x-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="./assets/x-light.svg">
  <img src="./assets/x-dark.svg" width="860" alt="...">
</picture>
```

The `<img>` inside is the fallback for clients that ignore `<picture>`
(some feed readers and the GitHub mobile app in older versions). GitHub's
own `#gh-dark-mode-only` / `#gh-light-mode-only` URL fragment trick still
works but is legacy; prefer `<picture>`.

## Motion etiquette

- Every animation loops or freezes in a settled state; never leave a panel
  mid-transition.
- One typing effect per page is enough. Two competing typewriters read as
  noise.
- Honour `prefers-reduced-motion` in CSS-driven panels: freeze at the final
  frame, fully opaque. SMIL cannot be gated by a media query, so SMIL panels
  should be gentle (slow, small movement) or short (play once, then freeze).
- Keep loops between 8 and 25 seconds. Shorter loops feel nervous; longer
  ones look broken to someone who lands mid-cycle.

## Data sources that need no server of your own

- The contribution calendar: `https://github.com/users/<user>/contributions`
  is a public HTML fragment; no token. Cells carry `data-date`,
  `data-level` (0 to 4) and, via `<tool-tip>`, the count.
- REST API from GitHub Actions with the built-in `GITHUB_TOKEN`
  (`permissions: contents: write` is enough): `/users/{u}`,
  `/users/{u}/repos`, `/repos/{o}/{r}/languages`,
  `/users/{u}/events/public`. 1000 requests an hour with the token, 60
  without. Events only cover about the last 90 days and 300 events.
- Third-party stats services (readme-stats, streak-stats, typing-svg,
  capsule-render and friends) are rate limited on shared hosts and go down.
  Generate the same thing locally and commit it; the profile then never
  shows a broken image.

## Accessibility and polish

- Every `<img>` gets an `alt` that states what the image says, not "banner".
- Headings in the terminal style use inline code in the heading:
  `### \`user@host ~ $ cat about.txt\``. Screen readers read them fine.
- Keep the page under ~1.5 MB of images total so it loads on mobile.
- Test on a phone width: images with `width="860"` shrink to fit, tables do
  not, so keep tables to two columns.
