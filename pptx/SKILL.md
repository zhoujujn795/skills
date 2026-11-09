---
name: pptx
description: "Use this skill any time a .pptx or .potx file is involved in any way — as input, output, or both. This includes: creating slide decks, pitch decks, or presentations; reading, parsing, or extracting text from any .pptx or .potx file (even if the extracted content will be used elsewhere, like in an email or summary); editing, modifying, or updating existing presentations; combining or splitting slide files; working with templates (.potx), layouts, speaker notes, or comments. Trigger whenever the user mentions \"deck,\" \"slides,\" \"presentation,\" or references a .pptx or .potx filename, regardless of what they plan to do with the content afterward. If a .pptx or .potx file needs to be opened, created, or touched, use this skill."
license: Complete terms in LICENSE.txt
---

# PPTX creation, editing, and analysis

A `.pptx` is a ZIP archive of XML files. Choose your approach by task:

| Task | Approach |
|---|---|
| **Create** a new deck | Write a `pptxgenjs` script — see gotchas below |
| **Edit** an existing deck, or build from a template | unzip → edit `ppt/slides/slideN.xml` → zip |
| **Read** content | `markitdown deck.pptx` (one block per slide under `<!-- Slide number: N -->` markers); visual grid: `python scripts/thumbnail.py deck.pptx` |

## Scripts

Paths are relative to this skill's directory. Everything else is plain Python, `node`, or shell.

| Script | What it does |
|---|---|
| `scripts/thumbnail.py deck.pptx [prefix]` | Labeled grid of every slide, for picking template layouts. `.pptx` only. Pass `prefix` — it defaults to `thumbnails`, which overwrites the grids of any other deck done in the same directory |
| `scripts/add_slide.py unpacked/ slide2.xml [--after slideN.xml]` | Duplicate a slide (or a `slideLayoutN.xml`) with all the package bookkeeping. Also takes a `.pptx` directly with `-o out.pptx` |
| `scripts/clean.py unpacked/` | Delete slides, media, and rels no longer referenced. Run **after** `<p:sldIdLst>` is final |
| `scripts/office/validate.py deck.pptx [--original src.pptx]` | Schema, relationship, content-type, chart and slide checks; each failure names its fix. Pass `--original` for any template-derived deck — it baselines the schema checks against the template, so the template's own XSD errors don't read as yours |
| `scripts/layout_audit.py deck.pptx` | **MANDATORY zero-dependency layout & CJK academic density auditor** (runs with built-in macOS `python3`). Detects table vertical auto-expansion collisions, CJK text box overflow, character overload (`>420` chars/slide), micro-fonts (`<12pt`), and AI card-stacking (`>28` shapes/slide). **Must exit 0 before delivering any `.pptx`!** |
| `scripts/office/soffice.py --headless --convert-to pdf deck.pptx` | LibreOffice wrapper — bare `soffice` hangs in this sandbox |

## Creating with pptxgenjs — gotchas

`pptxgenjs` is preinstalled — do not run `npm install` first; write the script and `require('pptxgenjs')` directly. Only if that require fails: `npm install pptxgenjs`. The model knows the API; these are the footguns:

- **Set `pres.layout` before adding slides.** The default canvas is `LAYOUT_16x9` = **10" × 5.625"**, not 13.3" wide. Coordinates past the edge are written, not clamped — the shape just isn't on the slide. (`LAYOUT_WIDE` is 13.3" × 7.5".)
- **Hex colors: never `#`, never 8 digits.** `color: "FF0000"`. Both `"#FF0000"` and alpha baked into the hex (`"00000020"`) **corrupt the file**. For translucency: `transparency: 0-100` on fills and images, `opacity: 0.0-1.0` on shadows — each is silently ignored on the other.
- **pptxgenjs mutates option objects in place** (converts values to EMU on first use). Never share one `shadow`/options object across two `add*` calls — build a fresh object each time.
- **Shadow `offset` must be ≥ 0** — a negative offset corrupts the file. To cast a shadow upward, use `angle: 270` with a positive offset.
- **`letterSpacing` is silently ignored** — the real option is `charSpacing`.
- **Lists:** `bullet: true` on each item, never a literal `•` (renders double bullets). Set `breakLine: true` on every array item except the last. Space bulleted paragraphs with `paraSpaceAfter`, not `lineSpacing` (huge gaps).
- **One `new pptxgen()` per output file** — never reuse an instance.
- **`rectRadius` only works on `ROUNDED_RECTANGLE`**, not `RECTANGLE`.
- **Gradient fills aren't supported** — use a gradient image as the background instead.
- **Text boxes have built-in internal padding** — set `margin: 0` whenever text must align with a shape, line, or icon at the same x.
- **Speaker notes go in `slide.addNotes("...")`** (plain text, once per slide), never in a text box on the slide.
- **Keep charts native.** Use `addChart()` for everything PowerPoint can chart (pass an array of `{type, data, options}` for combos). For PowerPoint-native features the library doesn't expose (trendlines, error bars), compute the extra series yourself or post-process the generated OOXML — do not fall back to a rendered image. Only chart types PowerPoint has no native form for (Sankey, network, chord) go in as images.
- **Default charts render bare** — no title, no data labels, dated palette. Set `showTitle` + `title`, `showValue: true` + `dataLabelPosition`, `chartColors: [...]` from your palette, and quiet the frame (`catAxisLabelColor`/`valAxisLabelColor`, `valGridLine: { color, size }`, `catGridLine: { style: "none" }`, `showLegend: false` for a single series).
- **On a stacked bar or column chart, `dataLabelPosition` must be `ctr`, `inEnd`, or `inBase`.** `outEnd` **corrupts the file**.
- **A combo series using `secondaryValAxis`/`secondaryCatAxis` needs both `valAxes` and `catAxes` on the chart options, two entries each.** Without them pptxgenjs writes axis *ids* it never declares, and PowerPoint **discards that chart** and reports the file as corrupt. Supplying only `valAxes` is not enough.
- **After `writeFile()`, run `python scripts/office/validate.py deck.pptx`.** It reports the two chart faults above and the slide-XML defects PowerPoint refuses, and names the fix for each. Fix them in your generator, not by hand-editing the packed XML.
- **Never reorder the children of `<p:presentation>`.** pptxgenjs writes `<p:notesMasterIdLst>` right after `<p:sldIdLst>` and points both masters at one theme part. PowerPoint reads that happily — move the element and the same deck becomes unopenable.
- **Icons:** render `react-icons` to SVG (`ReactDOMServer.renderToStaticMarkup`), rasterize with `sharp` at ≥256px, and insert via `addImage({ data: "image/png;base64," + buf.toString("base64") })` — the `image/png;base64,` prefix is required (`react-icons`, `react`, `react-dom`, and `sharp` are preinstalled — `npm install react-icons react react-dom sharp` only if a require fails).

## Editing existing decks and templates

Pick layouts first: `python scripts/thumbnail.py template.pptx template-thumbs` writes a labeled grid of every slide and prints the file(s) it created — `template-thumbs.jpg`, split into `template-thumbs-N.jpg` past 12 slides. **Always pass that second argument, named after the deck.** It defaults to `thumbnails`, so two decks thumbnailed in one directory silently overwrite each other's grids — the first deck's are simply gone (template analysis only — visual QA needs the full-resolution renders from [Converting to Images](#converting-to-images); it only accepts `.pptx`, so copy a `.potx` to a `.pptx` name first). Use it with `markitdown` to map each content section onto a template slide, and vary the layouts — don't put every section on the same title-and-bullets slide.

```bash
python3 -c "import sys,zipfile; zipfile.ZipFile(sys.argv[1]).extractall('unpacked')" deck.pptx
python scripts/add_slide.py unpacked/ slide2.xml --after slide2.xml   # duplicate a slide (or slideLayoutN.xml); prints the new slide's path
# reorder / delete slides = edit <p:sldIdLst> in ppt/presentation.xml
python scripts/clean.py unpacked/                                     # after deletions: removes orphaned slides, media, rels
# edit slide content in ppt/slides/slideN.xml
(cd unpacked && rm -f ../out.pptx && zip -Xr ../out.pptx .)           # zip from INSIDE the dir; rm first or deleted parts survive
python scripts/office/validate.py out.pptx --original deck.pptx
```

- **Do all structural work — add, delete, reorder — before editing any slide's content.** `add_slide.py` copies a slide file verbatim, so duplicating after you edit clones the edited content; and `clean.py` deletes any slide missing from `<p:sldIdLst>`, including one you just wrote.
- **Never copy a slide file by hand** — `add_slide.py` does every registration a new slide needs and reports what it made (`Created ppt/slides/slide17.xml from slide2.xml`). It also works directly on a file: `add_slide.py deck.pptx slide2.xml -o out.pptx` — **pass `-o`, or it rewrites the input deck in place.** A duplicated slide still *references* its source's chart/SmartArt/embedded-object parts rather than cloning them, so editing one slide's chart changes the other's.
- **If you use `python-pptx`**, three things it won't do: duplicate a slide (its only entry point is `add_slide(layout)`), preserve formatting through `text_frame.text = "..."` (that collapses the paragraph to a single unstyled run — assign `run.text` instead), or read the SVG/EMF most template art uses (`add_picture` raises `UnidentifiedImageError`).
- Legacy `.ppt` must be converted first: `python scripts/office/soffice.py --headless --convert-to pptx file.ppt`. `.potx` templates unpack and pack identically — keep the `.potx` extension on the output.
- To reuse a template icon or image, duplicate a slide or layout that already contains it.

When filling in a template:

- If you script an XML transform, parse with `defusedxml.minidom` — round-tripping OOXML through `xml.etree.ElementTree` rewrites namespace prefixes and corrupts the deck.
- **Template slots ≠ source items.** If the template shows 4 team members and you have 3, delete the 4th member's entire group (image + text boxes), not just its text — then check for orphaned visuals in QA.
- One `<a:p>` per list item — never concatenate items into a single paragraph. Copy the sibling `<a:pPr>` to preserve spacing, and put `b="1"` on the `<a:rPr>` of titles, section headers, and inline labels (`Status:`, `Owner:`).
- Let bullets inherit from the layout; only add `<a:buChar>`, `<a:buAutoNum>` (numbered), or `<a:buNone>` to override — never a literal `•` in the text.
- Text with leading or trailing spaces needs `xml:space="preserve"` on its `<a:t>`.

## Design Rules: Monochromatic Minimalist Academic Style (单色系极简学术风)

**CRITICAL OVERRIDE: Keep slides simple, clean, and strictly monochromatic.** Never create flashy marketing decks, multi-colored cards, or cluttered AI templates.

### 1. Strict Monochromatic Palette (严格单色系 + 纯白底)

- **Pure White Background Everywhere (`FFFFFF`)**: Every slide — including the Title slide and Thank-You slide — MUST use a clean white (`FFFFFF`) background. Never use dark navy/black backgrounds.
- **Single Chromatic Hue Only**: Across all slide shapes, lines, tables, and text, use **at most ONE muted academic primary color** (plus neutral grays/blacks):
  - **Primary Accent (Academic Slate Navy)**: `1E3A5F` (titles, key numbers, table header rule)
  - **Light Tint (Subtle Fill, when needed)**: `F4F6F9` (very light cool gray)
  - **Primary Text**: `1F2937` (near-black charcoal)
  - **Secondary / Muted Text**: `6B7280` (medium gray for citations, units, footers)
  - **Hairline Rules / Borders**: `D1D5DB` (light gray, `0.5–0.75 pt`)
- **FORBIDDEN Colors on Slide Shapes**: Never use red, orange, yellow, green, purple, or multi-colored status boxes/pills on slides. (Scientific figures embedded as images may use colorblind-safe data palettes, or monochromatic/grayscale palettes when requested.)

### 2. Minimalist Academic Layout (极简排版，禁止卡片堆砌)

- **NO Decorative Badges, Pills, or Callout Bars**:
  - **NEVER** draw numbered square badges (`01`, `M1`, `Q0`, `L1`), top-right section pills, colored circles with icons, or bottom `!` warning banners.
  - **NEVER** wrap bullet points inside gray/colored rounded-rectangle "cards". Write clean, left-aligned text directly on the white canvas with generous whitespace (`>= 45%` open canvas).
- **Only 3 Clean Visual Layers per Slide**:
  1. **Header**: Left-aligned concise title (`22–26 pt` bold, `1E3A5F`, single line `<= 26` CJK chars) at `x=0.7", y=0.45"`, optionally with a subtle subtitle or thin `0.5 pt` gray rule (`D1D5DB`).
  2. **Body Zone (`y=1.25"` to `6.4"`)**: Choose ONE clean structure per slide:
     - **Figure + Key Takeaways** (60% figure on left or top, 3–4 concise bullet points on right or bottom)
     - **Academic Three-Line Table (`booktabs` style)**: Clean white cells, `1E3A5F` or `1F2937` bold header text, top rule (`1.25 pt`), mid rule (`0.75 pt`), bottom rule (`1.25 pt`), **no vertical borders and no heavy colored header fills**.
     - **Two-Column Comparison**: Clean left/right text columns separated by whitespace (`0.6"` gap), not boxed cards.
  3. **Minimal Footer**: Page number (`3 / 14`) in `10 pt` gray (`6B7280`) at bottom-right.

### 3. Typography & Spacing

- **Safe fonts**: **Arial, Calibri, Microsoft YaHei (微软雅黑), PingFang SC**.
- **Sizes**:
  - Slide title: `22–26 pt` bold (`1E3A5F`)
  - Section / column heading: `16–18 pt` bold (`1F2937`)
  - Body bullet text: `14–16 pt` regular (`1F2937`), `paraSpaceAfter: 8–10`
  - Table text: `12–13 pt` (`>= 11 pt` in appendix)
  - Captions / citations / footer: `10–11 pt` (`6B7280`)
- **Chinese (CJK) & Academic Presentation Guardrails**:
  1. **Table Auto-Expansion Trap (`addTable`)**: PowerPoint ignores the `h` property on `addTable()` as a maximum cap and automatically expands rows downward whenever cell text wraps. **NEVER place a large figure (`h > 2.5"`) AND a multi-row table (`> 4` rows) on the same slide.** Always keep main-slide tables `<= 6 rows × 6 cols` with `fontSize >= 12`, and verify `table_y + estimated_wrapped_height <= 6.3"`.
  2. **Slide Character Budget (`<= 380` chars on main slides)**: Never dump a full Markdown/Word research report onto slides at `9.5–11pt`. Keep main slides `<= 380` characters (`<= 600` for Backup slides) and body text `>= 14pt`. Put full paragraph explanations, methodological derivations, and file paths into **`slide.addNotes("...")`**.
  3. **No Shape Clutter (`<= 12` shapes/slide)**: Because you are not drawing boxed cards or badges, a clean slide should have **at most 6–12 shapes total** (title, body text box, optional takeaway line, footer).

## QA (Required)

Your first render usually has a few real issues — overlaps, overflow, misalignment. Find and fix those, re-render only the slides you changed, and stop.

### Layout, Monochromatic Style & Academic Density QA (MANDATORY FIRST GATE)

Run the zero-dependency layout auditor using built-in `python3` immediately after generating or editing any `.pptx`:

```bash
python3 /Users/zhoujun/.cc-switch/skills/pptx/scripts/layout_audit.py output.pptx
```

**You are FORBIDDEN from declaring completion or uploading to Google Drive until `layout_audit.py` exits with code `0` (`Audit PASSED!`).** If it reports `[FAIL]` on any slide (multi-color violations, dark background, table expansion collision, text box overflow, `>380` chars, font `<12pt`, or `>14` shapes), fix the generator script and re-run until 0 errors remain.

### Content QA

```bash
markitdown output.pptx
```

Check for missing content, typos, wrong order.

**When using templates, check for leftover placeholder text:**

```bash
markitdown output.pptx | grep -iE "\bx{3,}\b|lorem|ipsum|\bTODO|\[insert|this.*(page|slide).*layout"
```

If grep returns results, fix them before declaring success.

### File QA (required)

```bash
python scripts/office/validate.py output.pptx                      # built from scratch
python scripts/office/validate.py output.pptx --original src.pptx  # built from a template
```

**If the deck came from a template, always pass `--original`.** A template may itself
contain parts the XSD rejects, so a bare run can report failures you never caused — and
a genuine regression can hide among them. `--original` baselines
the schema and slide checks against the template, suppressing errors it already had.
The structural checks — relationships, content types, charts — ignore `--original` and
report template-inherited problems either way, so read those on their own merits.

pptxgenjs emits chart XML PowerPoint refuses to open, and every other tool
accepts: python-pptx opens those decks, LibreOffice renders them, the XSD
passes them. Every failure names its fix. Fix it in the generator and rebuild.

### Visual QA

Convert the slides to images (see [Converting to Images](#converting-to-images)) and inspect every one. After staring at the generating code you tend to see what you expect rather than what rendered, so look at the images fresh (a subagent works well for this if you have one). User-visible defects to look for:

- **Text overflow or text cut off at a box or slide boundary — check this first.** It is the most common defect and always user-visible. (For a font the previewer renders unreliably per Typography, the preview is approximate: trust the ~10% slack you left, not its apparent fit.)
- Overlapping elements (text through shapes, lines through words, stacked elements)
- Source citations or footers colliding with content above
- Elements too close (< 0.3" gaps) or cards/sections nearly touching
- Uneven gaps (large empty area in one place, cramped in another)
- Insufficient margin from slide edges (< 0.5")
- Columns or similar elements not aligned consistently
- Low-contrast text (e.g., light gray text on cream-colored background)
- Template decoration mispositioned after text replacement — e.g., a title underline positioned for one line, but the replaced title wrapped to two
- Low-contrast icons (e.g., dark icons on dark backgrounds without a contrasting circle)
- Text boxes too narrow causing excessive wrapping
- Leftover placeholder content

## Converting to Images

Convert presentations to individual slide images for visual inspection:

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
rm -f slide-*.jpg
pdftoppm -jpeg -r 150 output.pdf slide
ls -1 "$PWD"/slide-*.jpg
```

**Pass the absolute paths printed above directly to the view tool.** The `rm` clears stale images from prior runs. `pdftoppm` zero-pads based on page count: `slide-1.jpg` for decks under 10 pages, `slide-01.jpg` for 10-99, `slide-001.jpg` for 100+.

**After fixes, rerun all four commands above** — the PDF must be regenerated from the edited `.pptx` before `pdftoppm` can reflect your changes.

## Dependencies

`pptxgenjs` (npm, preinstalled — install only if `require('pptxgenjs')` fails) · `markitdown[pptx]`, `Pillow`, `defusedxml`, `lxml` (pip — text dump, thumbnail, clean, validate) · LibreOffice (`soffice`, auto-configured for sandboxed environments via `scripts/office/soffice.py`) · `pdftoppm` (Poppler)
