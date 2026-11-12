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
| **Create** a 上海工程技术大学 (SUES) deck | Start from `scripts/build_sues_2025_template.py` (`python-pptx`) — see [SUES template](#5-sues-template-how-to-use-it) |
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
| `scripts/layout_audit.py deck.pptx` | **MANDATORY layout auditor** (stdlib only). Fails on: text-box overflow (conservative CJK-aware estimate incl. insets and paragraph spacing), table auto-expansion collisions, >380 chars/slide (>600 backup), fonts that are not on both Windows and macOS, >3 font families, >2 chromatic hues, body font <12pt, >14 shapes. Warns if Chinese text has no East Asian font set. **Must exit 0 before delivering any `.pptx`.** |
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

## Design Rules: Clean Academic Style (白底学术风)

Keep slides simple and readable. No marketing-style decks, no card stacks, no decorative badges.

### 1. Color: white background, 1 primary + 1 accent

- **Background**: white (`FFFFFF`) on every slide, including title and thank-you slides.
- **Primary (slate navy)** `1E3A5F`: titles, key lines, table header rule, main series.
- **Accent (one only)** `C2410C` (burnt orange): the single thing you want the audience to look at: the key number, the proposed method's curve, one highlighted word. Use it sparingly, on at most 1–2 elements per slide.
- **Neutrals**: text `1F2937`, muted text `6B7280` (citations, units, footer), rules `D1D5DB`, light fill `F4F6F9`.
- **University Preset — 上海工程技术大学 (SUES 2025 Official New VI)**:
  - **探索蓝 (Exploration Blue, Primary)**: `0A2F99` (`RGB: 10, 47, 153`, `PANTONE 2146C`) — slide titles, header rule, table header, main plot series.
  - **Accent (warm, one only)**: `C2410C` (burnt orange) — the key number, the key finding, the current TOC entry. At most 1–2 elements per slide. An all-blue deck has no visible emphasis, so do not use a second blue as the accent.
  - **展望蓝 (Envision Blue)**: `2E74FF` (`RGB: 46, 116, 255`, `PANTONE 2727C`) — secondary series in charts only. Not for text: on white it is about 4.2:1 contrast.
  - **Neutrals**: body ink `1F2937`, muted text `595959`, official cool grey rule `C7C7C7` (`PANTONE 427C`), subtle surface tint `F4F6FA`, pure white `FFFFFF`.
  - **Bundled assets, template and generator**: see [SUES template](#5-sues-template-how-to-use-it).
- **Never** use a third hue on shapes or text (no green/purple/yellow pills, status boxes, or rainbow bullets). The audit fails at >2 chromatic hues.
- **Figures and charts** may use a colorblind-safe palette (Okabe-Ito: `0072B2`, `D55E00`, `009E73`, `E69F00`, `56B4E9`, `CC79A7`, `000000`). For charts with ≤3 series prefer the primary, the accent and a gray. Add a non-color cue (line style or marker) when more than 3 series share a chart. The audit reads slide XML only, so it does not check native chart colors; review those in the render.

### 2. Layout: no card stacking

- **No** numbered badges, section pills, colored circles with icons, or bottom warning banners.
- **No** gray or colored rounded-rectangle "cards" around bullets. Write text directly on the white canvas with generous whitespace (≥45% open).
- Each slide has three layers: a left-aligned **title** (26–30 pt bold, `1E3A5F`, one line, at x=0.7", y=0.45"), a **body zone** (y=1.25" to 6.4") with ONE structure (figure + 3–4 takeaways, a three-line table, or two columns), and a **footer** with page number (`3 / 14`, 10 pt, `6B7280`).
- Three-line (booktabs) tables: top rule 1.25 pt, header rule 0.75 pt, bottom rule 1.25 pt, no vertical borders, no colored header fills.

### 3. Fonts: must survive Windows ↔ macOS

The deck is opened on both Windows and macOS, so **the font must exist on both or the layout will reflow and overflow.**

- **Latin and digits**: `Arial` (or `Calibri` if the audience uses only Microsoft Office). Not Helvetica Neue, not Segoe UI, not Source Han.
- **Chinese**: `Microsoft YaHei` on Windows, `PingFang SC` on macOS. A run has one `a:ea` typeface, so pick the one matching where the talk is given, or set `Microsoft YaHei` and check the deck once on the other platform (it may be substituted there); in both cases **leave ≥15% width slack** in every text box.
- **pptxgenjs**: `fontFace` sets the Latin typeface. After generating, confirm the XML also carries an `a:ea` typeface for Chinese runs (`unzip -p deck.pptx ppt/slides/slide1.xml | grep -o '<a:ea[^>]*>' | sort | uniq -c`). If it is missing, add `<a:ea typeface="Microsoft YaHei"/>` to the run properties by post-processing; the audit warns when Chinese text has no East Asian font.
- **At most 3 families** per deck (Latin, CJK, optional monospace for code). No decorative or serif display fonts.
- **Sizes**: title 26–30 pt bold (one line); section heading 18–20 pt bold; body 16–18 pt (never below 14); table 12–13 pt (≥11 pt in appendix); captions/citations/footer 10–12 pt. Chart axis labels ≥12 pt.
- **LibreOffice previews substitute fonts**, so a clean render does not prove the deck fits in PowerPoint. Trust the audit's conservative estimate and the slack above, not the preview's apparent fit.

### 4. Density and overflow guardrails

1. **Character budget**: ≤380 characters on main slides, ≤600 on backup slides, body text ≥14 pt (16–18 pt preferred). Put paragraphs, derivations and file paths in `slide.addNotes("...")`.
2. **Text boxes**: size the box to the text, not the reverse. For every text box, estimate lines = ceil(characters × em-width ÷ usable width), where a Chinese character is 1 em and a Latin character is about 0.58 em, and make sure `lines × font size × 1.35` plus paragraph spacing fits the height. Do not rely on auto-shrink; it is not applied when the file is opened.
3. **Tables**: PowerPoint ignores `h` on `addTable()` as a cap and expands rows when text wraps. Never put a large figure (h > 2.5") and a table with more than 4 rows on one slide. Keep main-slide tables ≤6 rows × 6 columns at ≥12 pt, and check `table_y + wrapped height ≤ 6.3"`.
4. **Shapes**: aim for ≤12 shapes per slide (the audit fails at >14).

### 5. SUES template: how to use it

For a 上海工程技术大学 talk, do not write a pptxgenjs deck from scratch and do not hand-edit the bundled `.pptx`. Generate the deck from the script, which owns the chrome (navigation bar, logo, watermark, footer, page numbers):

1. Write `deck.json` with the real metadata. Keys: `title`, `subtitle`, `short_title`, `presenter`, `advisor`, `school`, `date`, `sections` (3–5 short section names). Ask the user for any you do not know; never invent a name or advisor.
2. Import or copy the figure-dominant page builders from `scripts/build_sues_2025_template.py`: `SUES_SLOT_SIZES` (exact `1:1` Matplotlib `figsize` slots), `add_sues_cover`, `add_sues_outline_2x2` (balanced `2×2` TOC grid without right-side blank holes), `add_sues_wide_figure` (`12.03"×4.10"` top diagram + 3 compact bottom columns), `add_sues_hero_split` (`62%` hero figure + optically centered right takeaways), `add_sues_dual_comparison` (symmetric A/B plots + bottom delta strip), `add_sues_grid_2x2` (`2×2` multi-panel plot + right summary), `add_sues_fig_table` (figure + LaTeX booktabs table), `add_sues_plan_gantt` (milestone Gantt chart + deliverables), `add_sues_closing`, and `add_footers()`. Every content slide after the outline should carry a `1:1` figure (`(svg_path, png_path)` `<asvg:svgBlip>` tuple or 300+ DPI PNG) — avoid text-only bullet slides.
3. Run `python3 build_deck.py -o talk.pptx --config deck.json --assets <this skill>/assets/sues_2025_vi` (the copy no longer sits next to the logos, so `--assets` is required), then `python3 scripts/layout_audit.py talk.pptx`.

Rules specific to this template:

- Colors are fixed: primary `0A2F99`, accent `C2410C`, neutrals (`**...**` renders bold `0A2F99`, `{{...}}` renders bold `C2410C`). Use the accent on at most 1–2 elements per slide.
- Sizes come from the `SIZE_*` constants (title 26, heading 17, body 15, table 13, caption 12). Right-side text columns next to figures use `MSO_ANCHOR.MIDDLE` so text and figure edges align optically without bottom blank holes. Do not go below `SIZE_*` to fit more text; cut words or split the slide.
- The slide title is one line, at most about 26 Chinese characters, and states the conclusion.
- The navigation bar and page numbers are generated from `sections` and the slide count. Pass the right section index to `add_chrome()`; never type a page number.
- Fonts are `Arial` + `Microsoft YaHei`. Use plain digits (`1.`, `01`) and `•` for lists. Avoid dingbats and Unicode sub/superscripts such as `❶`, `₆`, `‡`: Arial lacks them and each platform falls back differently. For formulas use run-level subscript formatting.
- `assets/sues_2025_vi/SUES_2025_Academic_Template.pptx` is the rendered example of this script (placeholder text only), for a user who wants to edit by hand in PowerPoint. Running the script with no arguments rebuilds it.

## QA (Required)

Your first render usually has a few real issues — overlaps, overflow, misalignment. Find and fix those, re-render only the slides you changed, and stop.

### Layout, Color, Font & Density QA (FIRST GATE)

Run the zero-dependency layout auditor using built-in `python3` immediately after generating or editing any `.pptx`:

```bash
python3 scripts/layout_audit.py output.pptx   # run from this skill's directory
```

**You are FORBIDDEN from declaring completion or delivering the file until `layout_audit.py` exits with code `0` (`Audit PASSED!`).** If it reports `[FAIL]` on any slide (more than 2 chromatic hues, disallowed fonts, table expansion collision, text-box overflow, `>380` chars, any font `<12pt`, body text mostly `<14pt`, no title of at least 24 pt, or `>14` shapes), fix the generator script and re-run until 0 errors remain.

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

- **Text overflow or text cut off at a box or slide boundary — check this first.** It is the most common defect and always user-visible. (For a font the previewer renders unreliably per Typography, the preview is approximate: trust the ≥15% slack you left, not its apparent fit.)
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

`pptxgenjs` (npm, preinstalled — install only if `require('pptxgenjs')` fails) · `python-pptx` (pip — only for `scripts/build_sues_2025_template.py`) · `markitdown[pptx]`, `Pillow`, `defusedxml`, `lxml` (pip — text dump, thumbnail, clean, validate) · LibreOffice (`soffice`, auto-configured for sandboxed environments via `scripts/office/soffice.py`) · `pdftoppm` (Poppler)
