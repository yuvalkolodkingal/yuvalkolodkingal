# SVG animation cookbook

The techniques the renderers use, as snippets you can lift. Every one of
them works inside an `<img>` on GitHub, which is the whole constraint: no
script, no external file, CSS only in the file's own `<style>`, and every
number baked in by Python. Snippets are simplified from the modules named;
colours are tokyo-night.

## The card and title bar

`theme.svg_open`, `theme.card` and `theme.title_bar` draw the window every
panel sits in:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="860" height="204" viewBox="0 0 860 204"
     role="img" aria-label="git log of milestones: cert: IBM Containers; poster: CalcuLab">
  <style>/* the panel's animation rules */</style>
  <rect x="0.5" y="0.5" width="859" height="203" rx="10" fill="#1a1b27" stroke="#3b4261" stroke-width="1"/>
  <circle cx="22" cy="21" r="4.5" fill="#ff7a93"/>
  <circle cx="40" cy="21" r="4.5" fill="#e0af68"/>
  <circle cx="58" cy="21" r="4.5" fill="#38bdae"/>
  <text x="430" y="26" text-anchor="middle" font-size="11" fill="#565f89">git log --oneline</text>
  <line x1="12" y1="38" x2="848" y2="38" stroke="#3b4261" stroke-width="1"/>
  <!-- first text baseline at y=66, left pad 20 -->
</svg>
```

Use it for any panel that is a window. The half-pixel offset keeps the 1 px
border crisp. Snake, typing and exit skip the bar on purpose: they read as
output in the page's own terminal, not as another window. Set `width` and
`height` to the CSS size GitHub will show and put the same numbers in
`viewBox`, so text is never scaled.

## Monospace grid math

Every row is laid out in columns, not pixels: one advance is `font * 0.6`
(6.9 px at 11.5), a column count is `int((width - 2 * pad) / adv)`, and
column `n` starts at `pad + n * adv`.

```svg
<text x="20" y="66" xml:space="preserve" font-size="11.5"
      font-family="ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace"
      textLength="110.40" lengthAdjust="spacing">yuval@scojen:~$ </text>
<rect x="130.4" y="56.5" width="6.9" height="13.5" fill="#70a5fd"/>
```

Sixteen characters times 6.9 is 110.4, so the cursor sits in column 16.
`textLength` with `lengthAdjust="spacing"` is what makes that true on every
machine: the viewer's monospace font is whichever one they have, and without
it a clip edge or cursor lands mid-glyph on a font with a wider advance.
`xml:space="preserve"` keeps the doubled spaces in `[  OK  ]` and leading
indentation. Count emoji as two columns (`render_typing.columns` counts
anything above U+2500 as two), and avoid them anyway: their width differs
between fonts and no `textLength` can fix a glyph that is missing.

## CSS staggered reveal

The workhorse for cards of rows (info, neofetch, systemctl, finger, stack,
gitlog, activity, boot):

```svg
<style>
.r{opacity:0;animation:in .45s ease-out forwards}
@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.r{animation:none;opacity:1;transform:none}}
</style>
<g class="r" style="animation-delay:0.25s">...row 1...</g>
<g class="r" style="animation-delay:0.31s">...row 2...</g>
```

Delay each row 40 to 60 ms after the last so the card prints rather than
pops, and keep the whole reveal under a second. `forwards` holds the end
state. The media query must set `opacity:1` and `transform:none` itself,
because `animation:none` alone leaves the element at its base `opacity:0`.
`theme.reduced_motion_css(".r")` emits that block. One Chromium quirk:
`steps(1)` on a fill-forwards fade can leave the last element invisible
(the end keyframe is never sampled), so boot prints its lines with
`in .05s linear forwards`, which is short enough to look like a step.

## SMIL typewriter: an animated clip

Text that types itself is a clip rectangle whose width grows one advance
per character; the text underneath never moves. From `render_exit.py`:

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

`calcMode="discrete"` makes characters appear whole instead of sliding in
from the left, and `textLength` makes each step land exactly between two
glyphs. The cursor rect steps through the same x values, then a `<set>`
hides it a beat after the last character. To play once, use `fill="freeze"`
as above. To loop (`render_typing.py`), put `repeatCount="indefinite"` on
each animate and lay the whole cycle out in `values` and `keyTimes`: type,
hold, erase, then park at 0 until this line's next turn. SMIL has no way to
loop a group, so every line's animate runs the full cycle and spends most
of it at zero width.

## Row wipe with a riding cursor

The portrait (`render_portrait.elements`) wipes each row with the same clip
idea, linear instead of discrete, and a cursor that rides the edge:

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

Row `i` begins at `i * 0.045 s`, so 47 rows finish in about 2.5 s. The
cursor's animations have no `fill="freeze"`, so when they end it snaps
back to its base `opacity="0"` and disappears. Use this for anything that
should print once and stay: a picture, a banner, a block of art.

## Reduced motion for SMIL

A media query cannot pause an `<animate>`. Two tricks make it not matter.

For clipped text, override the clip with CSS:

```css
@media (prefers-reduced-motion:reduce){.w{clip-path:none}.c{display:none}}
```

`clip-path="url(#w3)"` on the element is a presentation attribute, and in
the cascade any CSS property beats a presentation attribute. So the rule
removes the clip, the full text shows at once, and the cursors are hidden.
The animation still runs on a rect that no longer clips anything.

For moving shapes, draw a frozen twin and toggle which one is displayed
(`theme.still_layer` plus `theme.STILL_CSS`; snake, plate, the systemctl dot):

```svg
<style>.s{display:none}@media (prefers-reduced-motion:reduce){.m{display:none}.s{display:inline}}</style>
<g class="m"><!-- squares with fill timelines, snake segments, the beam --></g>
<g class="s"><!-- the same squares, filled, nothing animated --></g>
```

`display` is the safe attribute because no SMIL animation in the file
touches it and it is not something the browser interpolates, so nothing
can fight the media query. Emit `STILL_CSS` once per file. The twin only
needs the elements that move, which is why it costs little.

## The snake: per-square fill timeline and an interpolated path

Each square with data gets one fill animation over the whole loop
(`render_snake.py`, 21.7 s for a full year at 45 ms per square):

```svg
<rect x="63" y="55" width="12" height="12" rx="2.5" fill="#2f6bbd">
  <animate attributeName="fill"
    values="#2f6bbd;#2f6bbd;#f0e0ff;#1e2235;#1e2235;#2f6bbd;#2f6bbd"
    keyTimes="0;0.0842;0.0854;0.0865;0.8210;0.8417;1"
    dur="21.70s" repeatCount="indefinite"/>
  <title>3 contributions on 2025-10-15</title>
</rect>
```

The marks are: hold the heat colour until just before the bite, flash,
drop to empty just after, stay empty until the regrow wave reaches this
column (`crawl + week / weeks * regrow`), refill over 0.45 s, hold to the
end. Every element shares one `dur`, so the loop never drifts apart.

The head is a rect whose x and y step through every square of the path,
one `keyTime` per square:

```svg
<rect width="12" height="12" rx="3.33" fill="#f0e0ff" x="-100" y="40" filter="url(#glow)">
  <animate attributeName="x" values="-42;-27;-12;3;18;33;48;48;48;48;48;48;48;63;..."
    keyTimes="0;0.00207;0.00415;..." dur="21.70s" repeatCount="indefinite"/>
  <animate attributeName="y" values="40;40;40;40;40;40;40;55;70;85;100;115;130;130;..."
    keyTimes="0;0.00207;0.00415;..." dur="21.70s" repeatCount="indefinite"/>
</rect>
```

`calcMode` is left at its default, linear, so the head glides between
centres instead of jumping. Each body segment uses the same list shifted by
its index (`path[max(i - offset, 0)]`) and a smaller size, so it follows a
beat behind and the turns read as a snake. The list starts off-canvas
(a lead-in of six squares) and the last `keyTime` holds the final position
through the regrow and the pause.

## Glow filter and gradient beam

The head glows; nothing else does, because a filter is per-frame work and
seven of them are visible on a laptop:

```svg
<filter id="glow" x="-80%" y="-80%" width="260%" height="260%">
  <feGaussianBlur stdDeviation="2.6" result="b"/>
  <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
```

The enlarged filter region keeps the blur from being clipped at the
element's box. The plate's reader beam is a gradient rect that slides once:

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

The opacity envelope stops the beam popping in at the start and parking at
the far edge forever. Use a beam or a wave whenever a set of elements
should light up in order and the eye needs to see what is doing it.

## Blinking block cursor

```svg
<style>.k{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}
@media (prefers-reduced-motion:reduce){.k{animation:none}}</style>
<rect class="k" x="130.4" y="279" width="6.9" height="13.5" fill="#70a5fd"/>
```

`steps(1)` is right here: a blink has no final frame to lose, and a faded
blink looks like a breathing light. One advance wide, `font + 2` tall, top
at `baseline - font + 1`. Put it after a prompt (boot, stack), after the
pager marker (activity), or at the end of a typed line (exit), never on
more than one element per panel.

## Deterministic decoration

Numbers that only exist to look real must not change between builds, or
the daily job commits a diff and the page flickers for nothing. Hash the
thing they decorate:

```python
digest = hashlib.sha256(unit_name.encode("utf-8")).digest()
pid = 1000 + int.from_bytes(digest[0:2], "big") % 60000
tasks = 4 + digest[2] % 20
memory = 24 + int.from_bytes(digest[3:5], "big") % 400 + digest[5] % 10 / 10
```

```python
hashlib.sha1(f"{date}|{subject}".encode("utf-8")).hexdigest()[:7]   # a gitlog "commit"
```

The same idea gives boot its rising kernel timestamps from the line index.
Anything real (uptime, the build stamp, contributions) comes from data;
anything invented comes from a hash; nothing comes from `random`.

## ASCII-only text

Text renders in the viewer's system monospace font, and the fallback chain
ends at plain `monospace`. Any glyph outside ASCII may be missing or a
different width there. `build.py check` warns on every character above
U+007E except this set, which the common monospace fonts all carry:

```
…  ·  ●  └ ─ │ ├ ┌ ┐ ┘ ┬ ┴ ┼  ▁ ▂ ▃ ▄ ▅ ▆ ▇ █  ░ ▒ ▓  → ← ↑ ↓
```

Use `…` only to mark a truncated value, `·` as a separator in a stamp, and
the box set for trees and bars. Systemctl draws its status dot as a
`<circle>` rather than `●` so it can pulse. Run every string through
`theme.esc` so `<`, `&` and quotes cannot break the XML.

## File-size discipline

Keep each SVG under about 300 KB (`check` warns above it) and the page
under 1.5 MB of images. Bytes go where `values` lists go: one animate per
moving element, with one entry per keyframe. The rules the snake follows:

- Only squares with data get an `<animate>` and a `<title>`; empty squares
  are plain rects. A year of steady activity is about 140 KB.
- One shared `dur` and `keyTimes` list per kind of element; round values to
  two decimals.
- `from`/`to` when the motion is a straight line, `values` only when it is
  not.
- No twin for elements that do not move.

## Testing

Parse before writing, so a broken file never reaches the repository:

```python
import xml.etree.ElementTree as ET
ET.fromstring(svg)   # render_all does this; a ParseError stops the build
```

Then look at it in headless Chromium with Playwright, two ways. For the
GitHub view, load the file through an `<img>` with a `data:` URL and
screenshot the element at two times: around 100 ms (mid-animation, to see
that it moves) and after the longest delay, 3 to 5 s (settled, to see the
state a reader lands on). For reduced motion, inline the SVG markup in the
page instead:

```js
const ctx = await browser.newContext({ reducedMotion: 'reduce', colorScheme: 'dark' });
const page = await ctx.newPage();
await page.setContent(`<body style="margin:0;background:#0d1117">${fs.readFileSync(file, 'utf8')}</body>`);
await page.waitForTimeout(100);
await page.screenshot({ path: 'reduced-100ms.png' });
const shown = await page.evaluate(() =>
  [...document.querySelectorAll('g.r')].filter(g => getComputedStyle(g).opacity === '1').length);
```

An SVG inside `<img>` is its own document and does not receive the
emulated media features, so through `<img>` the reduced test would pass
without testing anything. Inline, every row should report opacity 1 at
100 ms and the still layer should be the one on screen. Finish with
`build.py check --strict`, which also catches `<script>`,
`<foreignObject>`, external URLs, an animated file with no
`prefers-reduced-motion` rule, odd glyphs and oversized files.
