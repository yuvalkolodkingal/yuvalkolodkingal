# SVG animation cookbook

The techniques the renderers use, as snippets to lift. All of them work
inside an `<img>` on GitHub: no script, no external file, CSS only in the
file's own `<style>`, every number baked in by Python. Simplified from the
modules named; tokyo-night colours, 11.5 px font unless shown.

## The card and title bar

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="860" height="204" viewBox="0 0 860 204"
     role="img" aria-label="git log of milestones: cert: IBM Containers; poster: CalcuLab">
  <rect x="0.5" y="0.5" width="859" height="203" rx="10" fill="#1a1b27" stroke="#3b4261" stroke-width="1"/>
  <circle cx="22" cy="21" r="4.5" fill="#ff7a93"/>
  <circle cx="40" cy="21" r="4.5" fill="#e0af68"/>
  <circle cx="58" cy="21" r="4.5" fill="#38bdae"/>
  <text x="430" y="26" text-anchor="middle" font-size="11" fill="#565f89">git log --oneline</text>
  <line x1="12" y1="38" x2="848" y2="38" stroke="#3b4261" stroke-width="1"/>
</svg>
```

`theme.svg_open`, `theme.card` and `theme.title_bar`; rows start at
baseline 66 with a 20 px pad. The half-pixel offset keeps a 1 px border
crisp; `viewBox` matches `width`/`height` so text is never scaled. Use it
for every panel that is a window; snake, typing and exit skip the bar so
they read as output in the page's own terminal.

## Monospace grid math

```svg
<text x="20" y="66" xml:space="preserve" font-size="11.5"
      font-family="ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace"
      textLength="110.40" lengthAdjust="spacing">yuval@scojen:~$ </text>
<rect x="130.4" y="56.5" width="6.9" height="13.5" fill="#70a5fd"/>
```

One advance is `font * 0.6` (6.9 px), column `n` starts at `pad + n * adv`,
the column count is `int((width - 2 * pad) / adv)`. Sixteen characters
times 6.9 is 110.4, so the cursor sits in column 16 on every machine: the
viewer's font is whichever monospace they have, and without `textLength` +
`lengthAdjust="spacing"` a clip edge or cursor lands mid-glyph on a wider
face. `xml:space="preserve"` keeps the doubled spaces in `[  OK  ]`. Emoji
count as two columns (`render_typing.columns`) and are avoided: their width
differs by font and `textLength` cannot fix a missing glyph.

## CSS staggered reveal

```svg
<style>
.r{opacity:0;animation:in .45s ease-out forwards}
@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.r{animation:none;opacity:1;transform:none}}
</style>
<g class="r" style="animation-delay:0.25s">...row 1...</g>
<g class="r" style="animation-delay:0.31s">...row 2...</g>
```

The workhorse for cards of rows: delay each row 40 to 60 ms after the last
so the card prints rather than pops, keep the reveal under a second, let
`forwards` hold the end state. The media query must set `opacity:1` and
`transform:none` itself, because `animation:none` alone leaves the element
at its base `opacity:0` (`theme.reduced_motion_css(".r")` emits the block).
Chromium quirk: `steps(1)` on a fill-forwards fade can leave the last
element invisible, so boot prints lines with `in .05s linear forwards`.

## SMIL typewriter: an animated clip

```svg
<defs><clipPath id="exit-clip">
  <rect x="20" y="0" width="0" height="84">
    <animate attributeName="width" calcMode="discrete"
      values="0;6.90;13.80;20.70;...;138.00" keyTimes="0;0.05;0.1;0.15;...;1"
      begin="0.4s" dur="1.200s" fill="freeze"/>
  </rect>
</clipPath></defs>
<text class="t" clip-path="url(#exit-clip)" x="20" y="29" xml:space="preserve"
      textLength="138.00" lengthAdjust="spacing">yuval@scojen:~$ exit</text>
<rect class="c" x="20" y="19.5" width="6.9" height="13.5" fill="#70a5fd">
  <animate attributeName="x" calcMode="discrete" values="20;26.90;...;158.00"
    keyTimes="0;0.05;...;1" begin="0.4s" dur="1.200s" fill="freeze"/>
  <set attributeName="opacity" to="0" begin="1.9s" fill="freeze"/>
</rect>
```

`render_exit.py`: the text never moves; a clip rectangle grows one advance
per character. `calcMode="discrete"` makes characters appear whole,
`textLength` puts each step between two glyphs, and the cursor steps
through the same x values until a `<set>` hides it. Play once with
`fill="freeze"`, as here. To loop (`render_typing.py`), use
`repeatCount="indefinite"` and lay the whole cycle out in `values` and
`keyTimes`: type, hold, erase, park at 0 until this line's next turn. SMIL
cannot loop a group, so each line's animate runs the full cycle alone.

## Row wipe with a riding cursor

```svg
<clipPath id="w3"><rect x="14" y="47.6" width="0" height="8.8">
  <animate attributeName="width" from="0" to="342.72" dur="0.34s" begin="0.135s" fill="freeze"/>
</rect></clipPath>
<text class="w" clip-path="url(#w3)" x="14" y="54.4" xml:space="preserve" font-size="6.8"
      fill="#c7d0f0" textLength="342.72" lengthAdjust="spacing">    .:--- ATGC ---:.</text>
<rect class="c" x="14" y="48.6" width="4.08" height="6.8" fill="#70a5fd" opacity="0">
  <animate attributeName="x" from="14" to="356.72" dur="0.34s" begin="0.135s"/>
  <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.02;0.95;1" dur="0.34s" begin="0.135s"/>
</rect>
```

`render_portrait.elements`: the same clip, linear instead of discrete, with
a cursor riding the edge. Row `i` begins at `i * 0.045 s`, so 47 rows take
about 2.5 s; the cursor has no `fill="freeze"`, so it snaps back to its
base `opacity="0"` when done. Use it for anything that prints once and stays.

## Reduced motion for SMIL

```css
@media (prefers-reduced-motion:reduce){.w{clip-path:none}.c{display:none}}
```

A media query cannot pause an `<animate>`, so make it not matter. For
clipped text: `clip-path="url(#w3)"` on the element is a presentation
attribute, and a CSS property always beats one in the cascade, so this
rule shows the full text at once and hides the cursors.

```svg
<style>.s{display:none}@media (prefers-reduced-motion:reduce){.m{display:none}.s{display:inline}}</style>
<g class="m"><!-- squares with fill timelines, snake segments, the beam --></g>
<g class="s"><!-- the same squares, filled, nothing animated --></g>
```

For moving shapes, draw a frozen twin and toggle which group is displayed
(`theme.still_layer` + `theme.STILL_CSS`; snake, plate, the systemctl dot).
`display` is the safe attribute because no animation touches it and the
browser never interpolates it, so nothing can fight the media query. Emit
`STILL_CSS` once per file; the twin holds only what moves.

## The snake: per-square fill timeline and an interpolated path

```svg
<rect x="63" y="55" width="12" height="12" rx="2.5" fill="#2f6bbd">
  <animate attributeName="fill"
    values="#2f6bbd;#2f6bbd;#f0e0ff;#1e2235;#1e2235;#2f6bbd;#2f6bbd"
    keyTimes="0;0.0842;0.0854;0.0865;0.8210;0.8417;1"
    dur="21.70s" repeatCount="indefinite"/>
  <title>3 contributions on 2025-10-15</title>
</rect>
```

Each square with data gets one fill animation spanning the loop
(`render_snake.py`, 21.7 s for a year at 45 ms a square): hold until just
before the bite, flash, drop to empty, stay empty until the regrow wave
reaches the column (`crawl + week / weeks * regrow`), refill over 0.45 s,
hold. One shared `dur` keeps every element in step.

```svg
<rect width="12" height="12" rx="3.33" fill="#f0e0ff" x="-100" y="40" filter="url(#glow)">
  <animate attributeName="x" values="-42;-27;-12;3;18;33;48;48;48;48;48;48;48;63;..."
    keyTimes="0;0.00207;0.00415;..." dur="21.70s" repeatCount="indefinite"/>
  <animate attributeName="y" values="40;40;40;40;40;40;40;55;70;85;100;115;130;130;..."
    keyTimes="0;0.00207;0.00415;..." dur="21.70s" repeatCount="indefinite"/>
</rect>
```

The head steps through every square of the path, one `keyTime` per square,
with `calcMode` left linear so it glides between centres. Each body segment
uses the same list shifted by its index (`path[max(i - offset, 0)]`) at a
smaller size, so it follows a beat behind and the turns read as a snake;
the last `keyTime` holds through the regrow and the pause.

## Glow filter and gradient beam

```svg
<filter id="glow" x="-80%" y="-80%" width="260%" height="260%">
  <feGaussianBlur stdDeviation="2.6" result="b"/>
  <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
```

Only the head glows: a filter is per-frame work and seven of them show on a
laptop. The enlarged region stops the blur being clipped at the box.

```svg
<linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#70a5fd" stop-opacity="0"/>
  <stop offset="0.5" stop-color="#70a5fd" stop-opacity="0.9"/>
  <stop offset="1" stop-color="#70a5fd" stop-opacity="0"/>
</linearGradient>
<rect x="24" y="55.5" width="10" height="161" fill="url(#beam)" opacity="0">
  <animate attributeName="x" from="24" to="264" dur="3.36s" begin="0.3s" fill="freeze"/>
  <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.05;0.95;1" dur="3.36s" begin="0.3s" fill="freeze"/>
</rect>
```

The plate's reader beam slides once; the opacity envelope stops it popping
in or parking at the far edge. Use a beam whenever elements light up in
order and the eye needs to see what is doing it.

## Blinking block cursor

```svg
<style>.k{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){.k{animation:none}}</style>
<rect class="k" x="130.4" y="279" width="6.9" height="13.5" fill="#70a5fd"/>
```

`steps(1)` is right here: a blink has no final frame to lose, and a faded
blink looks like a breathing light. One advance wide, `font + 2` tall, one
per panel: after a prompt, the pager marker or a typed line.

## Deterministic decoration

```python
digest = hashlib.sha256(unit_name.encode("utf-8")).digest()      # render_systemctl.py
pid = 1000 + int.from_bytes(digest[0:2], "big") % 60000
tasks = 4 + digest[2] % 20
memory = 24 + int.from_bytes(digest[3:5], "big") % 400 + digest[5] % 10 / 10
short_hash = hashlib.sha1(f"{date}|{subject}".encode("utf-8")).hexdigest()[:7]   # render_gitlog.py
```

Numbers that only exist to look real must not change between builds, or
the daily job commits a diff for nothing, so hash the thing they decorate.
Real values come from data, invented ones from a hash, nothing from `random`.

## ASCII-only text

Text renders in the viewer's system monospace font, so any glyph outside
ASCII may be missing or a different width. `build.py check` warns on every
character above U+007E except `… · ●`, the box set
`└ ─ │ ├ ┌ ┐ ┘ ┬ ┴ ┼`, the blocks `▁ ▂ ▃ ▄ ▅ ▆ ▇ █ ░ ▒ ▓` and the arrows
`→ ← ↑ ↓`, which the common monospace fonts all carry. Use `…` only to mark
a truncated value; systemctl draws its dot as a `<circle>` rather than `●`
so it can pulse. Run every string through `theme.esc`.

## File-size discipline

Keep each SVG under about 300 KB (`check` warns above it) and the page
under 1.5 MB of images. Bytes go where `values` lists go, so animate only
elements with something to show: the snake animates squares with data and
leaves empty squares as plain rects, which lands a year of steady activity
at about 140 KB. Round to two decimals, use `from`/`to` for straight lines
and `values` only when the path bends, and give a still twin only to what
moves.

## Testing

```python
import xml.etree.ElementTree as ET
ET.fromstring(svg)   # render_all does this; a ParseError stops the build
```

```js
const ctx = await browser.newContext({ reducedMotion: 'reduce', colorScheme: 'dark' });
const page = await ctx.newPage();
await page.setContent(`<body style="margin:0;background:#0d1117">${fs.readFileSync(file, 'utf8')}</body>`);
await page.waitForTimeout(100);
await page.screenshot({ path: 'reduced-100ms.png' });
const shown = await page.evaluate(() =>
  [...document.querySelectorAll('g.r')].filter(g => getComputedStyle(g).opacity === '1').length);
```

Parse before writing so a broken file never reaches the repository, then
look at it in headless Chromium with Playwright. For the GitHub view, load
the file through an `<img>` with a `data:` URL and screenshot at two times:
about 100 ms (mid-animation) and after the longest delay, 3 to 5 s (the
state a reader lands on). For reduced motion, inline the markup as above:
an SVG inside `<img>` is its own document and does not receive the
emulated media features, so through `<img>` the test passes without
testing anything. Inline, every row should report opacity 1 at 100 ms.
Finish with `build.py check --strict`, which also catches `<script>`,
`<foreignObject>`, external URLs, animation without a
`prefers-reduced-motion` rule, odd glyphs and oversized files.
