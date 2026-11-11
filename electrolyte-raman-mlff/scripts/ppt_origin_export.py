#!/usr/bin/env python3
r"""
PowerPoint-Editable SVG Sanitizer & OriginPro / Excel / Orange Source-Data Exporter.

Solves all three root causes of garbled text (`乱码`), scrambled character order, and black mask
boxes when opening or ungrouping ("转换为形状 / Convert to Shape") Matplotlib SVGs in PowerPoint,
while simultaneously exporting OriginPro-native 3-header source data (`.xlsx` + `.csv`):

  1. Scrambled `<tspan>` XML Order (`gr()Mg-O/Cl of 2+w-`):
     - Matplotlib's `backend_svg` emits `$...$` mathtext `<tspan>` elements grouped by font face/size
       rather than left-to-right `x` coordinate. PowerPoint concatenates `<tspan>` children in XML
       document order and ignores per-`<tspan>` `x`/`y`, scrambling formulas into `乱码`.
     -> `sanitize_svg_for_ppt()` sorts all `<tspan>` glyphs strictly by `x`, reconstructs LaTeX `\ `
        math spaces via glyph advance widths, and flattens contiguous same-baseline/same-style runs
        into standalone `<text x="..." y="...">` elements with ZERO `<tspan>` tags.
  2. Missing System Fonts (`DejaVu Sans` / `STIXGeneral` / `cmex10`) & Missing `Arial.ttf` Glyphs:
     - Normalizes `\u2212` (`-`), `\u27e8`/`\u27e9` (`<`/`>`), `\u22c5` (`·`), `\u2032` (`'`), and
       `\xa0` (` `), and rewrites `font-family` to clean `Arial, sans-serif` (or `'PingFang SC', Arial`
       for CJK), guaranteeing 100% glyph coverage in macOS/Windows `Arial.ttf`.
  3. Solid Black `<clipPath>` Rectangles:
     - `clip_curve_to_box()` and `clip_scatter_to_box()` pre-clip data to axes limits before plotting,
       and `sanitize_svg_for_ppt()` strips all `<clipPath>` definitions and `clip-path` attributes.
"""

from __future__ import annotations

import csv
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Sequence
from xml.sax.saxutils import escape

import numpy as np

try:
    from matplotlib.ft2font import FT2Font, LoadFlags
except ImportError:  # pragma: no cover
    FT2Font = None  # type: ignore[assignment]
    LoadFlags = None  # type: ignore[assignment]


SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

# Characters emitted by Matplotlib mathtext or user strings that are absent from macOS/Windows Arial.ttf
UNICODE_TO_ARIAL_MAP: dict[str, str] = {
    "\u2212": "-",       # MINUS SIGN -> ASCII hyphen-minus
    "\u2013": "-",       # EN DASH (safe fallback)
    "\u27e8": "<",       # MATHEMATICAL LEFT ANGLE BRACKET
    "\u27e9": ">",       # MATHEMATICAL RIGHT ANGLE BRACKET
    "\u2329": "<",       # LEFT-POINTING ANGLE BRACKET
    "\u232a": ">",       # RIGHT-POINTING ANGLE BRACKET
    "\u22c5": "\u00b7",  # DOT OPERATOR -> Latin-1 MIDDLE DOT (present in Arial.ttf)
    "\u2219": "\u00b7",  # BULLET OPERATOR -> Latin-1 MIDDLE DOT
    "\u22ef": "\u00b7\u00b7\u00b7",  # MIDLINE HORIZONTAL ELLIPSIS (\cdots) -> 3 Latin-1 middle dots
    "\u2032": "'",       # PRIME -> ASCII apostrophe
    "\u2033": "''",      # DOUBLE PRIME
    "\xa0": " ",         # NO-BREAK SPACE -> ASCII space
    "\u2009": " ",       # THIN SPACE
    "\u200a": " ",       # HAIR SPACE
    "\u2002": " ",       # EN SPACE
    "\u2003": " ",       # EM SPACE
    # Raw Unicode subscripts/superscripts (absent in macOS Arial.ttf) -> ASCII fallback
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
    "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
    "₊": "+", "₋": "-",
    "⁰": "0", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "⁺": "+", "⁻": "-",
}

_ARIAL_FONT_CACHE: dict[tuple[bool, bool], Any] = {}


def _get_arial_ft2(bold: bool = False, italic: bool = False) -> Any:
    """Load macOS Arial FT2Font face if available for exact glyph advance measurement."""
    if FT2Font is None:
        return None
    key = (bold, italic)
    if key in _ARIAL_FONT_CACHE:
        return _ARIAL_FONT_CACHE[key]

    candidates = {
        (False, False): [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/Library/Fonts/Arial.ttf",
        ],
        (True, False): [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/Library/Fonts/Arial Bold.ttf",
        ],
        (False, True): [
            "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
            "/Library/Fonts/Arial Italic.ttf",
        ],
        (True, True): [
            "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
            "/Library/Fonts/Arial Bold Italic.ttf",
        ],
    }[key]

    font_obj = None
    for path in candidates:
        if Path(path).exists():
            font_obj = FT2Font(path)
            break
    if font_obj is None and key != (False, False):
        font_obj = _get_arial_ft2(False, False)
    _ARIAL_FONT_CACHE[key] = font_obj
    return font_obj


def _glyph_advance_px(text: str, font_size_px: float, bold: bool = False, italic: bool = False) -> float:
    """Compute horizontal advance width (in SVG px) of `text` in Arial at `font_size_px`."""
    if not text:
        return 0.0
    ft = _get_arial_ft2(bold=bold, italic=italic)
    if ft is not None and LoadFlags is not None:
        cmap = ft.get_charmap()
        units_per_em = float(ft.units_per_EM or 2048)
        total_adv = 0.0
        for ch in text:
            g_idx = cmap.get(ord(ch))
            if g_idx is not None:
                glyph = ft.load_glyph(g_idx, flags=LoadFlags.NO_SCALE)
                total_adv += (glyph.horiAdvance / units_per_em) * font_size_px
            else:
                total_adv += 0.55 * font_size_px
        return total_adv
    return len(text) * 0.55 * font_size_px


def normalize_text_for_arial(text: str | None) -> str:
    """Normalize math symbols and spaces to characters guaranteed to exist in Arial."""
    if not text:
        return ""
    return "".join(UNICODE_TO_ARIAL_MAP.get(ch, ch) for ch in text)


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def _parse_style_props(style_str: str) -> dict[str, str]:
    props: dict[str, str] = {}
    for part in style_str.split(";"):
        part = part.strip()
        if ":" in part:
            k, v = part.split(":", 1)
            props[k.strip().lower()] = v.strip()
    return props


def _normalize_style(style_str: str, text_sample: str = "") -> tuple[str, float, bool, bool]:
    """
    Normalize CSS style on `<text>` so PowerPoint resolves Arial cleanly without DejaVu/STIX/oblique issues.
    Returns `(normalized_style_str, font_size_px, is_bold, is_italic)`.
    """
    props = _parse_style_props(style_str)
    if props.get("font-style") == "oblique":
        props["font-style"] = "italic"

    if _contains_cjk(text_sample):
        props["font-family"] = "'PingFang SC', 'Microsoft YaHei', Arial, sans-serif"
    else:
        props["font-family"] = "Arial, sans-serif"

    fs_raw = props.get("font-size", "8px")
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", fs_raw)
    font_size_px = float(m.group(1)) if m else 8.0

    fw = props.get("font-weight", "normal").lower()
    is_bold = fw in ("bold", "700", "800", "900")
    is_italic = props.get("font-style", "normal").lower() == "italic"

    ordered_keys = ["font-style", "font-weight", "font-size", "font-family", "text-anchor", "fill", "opacity"]
    out_parts: list[str] = []
    for k in ordered_keys:
        if k in props:
            out_parts.append(f"{k}: {props[k]}")
    for k, v in props.items():
        if k not in ordered_keys and k != "clip-path":
            out_parts.append(f"{k}: {v}")
    return "; ".join(out_parts), font_size_px, is_bold, is_italic


def _flatten_mathtext_text_element(text_el: ET.Element) -> list[ET.Element]:
    """
    Convert a Matplotlib `<text>` containing positioned `<tspan x="..." y="...">` children into a
    sorted list of standalone `<text x="..." y="..." style="...">` elements with ZERO `<tspan>`.
    """
    tspans = [c for c in text_el if c.tag.endswith("tspan")]
    if not tspans:
        norm_txt = normalize_text_for_arial(text_el.text)
        text_el.text = norm_txt
        if "style" in text_el.attrib:
            norm_st, _, _, _ = _normalize_style(text_el.attrib["style"], norm_txt)
            text_el.attrib["style"] = norm_st
        tf = text_el.attrib.get("transform", "")
        if tf.startswith("rotate(-0 ") or tf.startswith("rotate(0 "):
            del text_el.attrib["transform"]
        return [text_el]

    parent_style = text_el.attrib.get("style", "")
    parent_transform = text_el.attrib.get("transform", "")
    if parent_transform.startswith("rotate(-0 ") or parent_transform.startswith("rotate(0 "):
        parent_transform = ""

    items: list[tuple[int, float, float, str, str, float, bool, bool]] = []
    for idx, ts in enumerate(tspans):
        orig_txt = ts.text or ""
        had_math_minus = "\u2212" in orig_txt
        raw_txt = normalize_text_for_arial(orig_txt)
        if not raw_txt:
            continue
        x_val = float(ts.attrib.get("x", text_el.attrib.get("x", "0")).split()[0])
        y_val = float(ts.attrib.get("y", text_el.attrib.get("y", "0")).split()[0])
        combined_style = f"{parent_style}; {ts.attrib.get('style', '')}" if parent_style else ts.attrib.get("style", "")
        norm_st, fs_px, is_bold, is_italic = _normalize_style(combined_style, raw_txt)
        if had_math_minus and raw_txt == "-":
            # \u2212 (~0.58 em) is wider than Arial ASCII '-' (~0.33 em); shift x right by +0.24*fs
            # so '-1', '-4', '-12' glue flush against the following digit with zero trailing gap.
            x_val += 0.24 * fs_px
        items.append((idx, x_val, y_val, norm_st, raw_txt, fs_px, is_bold, is_italic))

    if not items:
        return []

    # Sort strictly left-to-right by x coordinate (tie-break by original index)
    items.sort(key=lambda it: (round(it[1], 4), it[0]))

    # Bucket items by (baseline y within 0.04*fs, style) so stacked sub/superscripts
    # (e.g. F^i_{DFT}) never split contiguous letters ('D'+'F'+'T') on the same baseline.
    buckets: list[list[Any]] = []  # [ref_y, norm_st, fs_px, list_of_(x, y, txt, adv)]
    for _, x_val, y_val, norm_st, txt, fs_px, is_bold, is_italic in items:
        adv = _glyph_advance_px(txt, fs_px, bold=is_bold, italic=is_italic)
        placed = False
        for b in buckets:
            if b[1] == norm_st and abs(y_val - b[0]) <= 0.04 * max(fs_px, b[2]):
                b[3].append((x_val, y_val, txt, adv, fs_px))
                placed = True
                break
        if not placed:
            buckets.append([y_val, norm_st, fs_px, [(x_val, y_val, txt, adv, fs_px)]])

    runs: list[list[Any]] = []
    for ref_y, norm_st, _, b_items in buckets:
        b_items.sort(key=lambda t: t[0])
        other_xs = [
            ox
            for ob in buckets
            if ob is not b_items and (ob[1] != norm_st or abs(ob[0] - ref_y) > 0.04 * b_items[0][4])
            for (ox, _, _, _, _) in ob[3]
        ]
        cur_runs: list[list[Any]] = []
        for x_val, y_val, txt, adv, fs_px in b_items:
            if not cur_runs:
                cur_runs.append([x_val, y_val, norm_st, txt, x_val + adv, fs_px])
                continue
            prev = cur_runs[-1]
            prev_x, prev_y, prev_st, prev_txt, prev_end_x, _ = prev
            gap = x_val - prev_end_x
            has_intervening_other = any((prev_end_x - 0.08 * fs_px) <= ox <= (x_val + 0.02 * fs_px) for ox in other_xs)

            if not has_intervening_other:
                if -0.15 * fs_px <= gap <= 0.16 * fs_px:
                    prev[3] = prev_txt + txt
                    prev[4] = x_val + adv
                    continue
                if 0.16 * fs_px < gap <= 0.62 * fs_px:
                    if not prev_txt.endswith(" ") and not txt.startswith(" "):
                        prev[3] = prev_txt + " " + txt
                    else:
                        prev[3] = prev_txt + txt
                    prev[4] = x_val + adv
                    continue

            cur_runs.append([x_val, y_val, norm_st, txt, x_val + adv, fs_px])
        runs.extend(cur_runs)

    # Sort final merged runs left-to-right for natural reading order in SVG / PowerPoint
    runs.sort(key=lambda r: (round(r[0], 3), round(r[1], 3)))

    out_elements: list[ET.Element] = []
    tag_name = f"{{{SVG_NS}}}text" if text_el.tag.startswith("{") else "text"
    for r_x, r_y, r_st, r_txt, _, _ in runs:
        if not r_txt.strip():
            continue
        # Strip leading space while shifting x forward by space advance so anchor is exact
        if r_txt.startswith(" "):
            stripped = r_txt.lstrip(" ")
            n_lead = len(r_txt) - len(stripped)
            _, fs_px, b_flag, i_flag = _normalize_style(r_st, stripped)
            r_x += _glyph_advance_px(" " * n_lead, fs_px, bold=b_flag, italic=i_flag)
            r_txt = stripped
        r_txt = r_txt.rstrip(" ")
        new_el = ET.Element(tag_name)
        new_el.attrib["style"] = r_st
        new_el.attrib["x"] = f"{r_x:.4f}".rstrip("0").rstrip(".") if "." in f"{r_x:.4f}" else f"{r_x}"
        new_el.attrib["y"] = f"{r_y:.4f}".rstrip("0").rstrip(".") if "." in f"{r_y:.4f}" else f"{r_y}"
        if parent_transform:
            new_el.attrib["transform"] = parent_transform
        new_el.text = r_txt
        out_elements.append(new_el)

    return out_elements


def clip_curve_to_box(
    x: np.ndarray,
    y: np.ndarray,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray]:
    """
    Clip a polyline `(x, y)` strictly to `(xlim, ylim)` with linear boundary interpolation so
    curves terminate cleanly right on the axis spine without needing SVG `<clipPath>`.
    """
    x_in = np.asarray(x, dtype=float)
    y_in = np.asarray(y, dtype=float)
    x0, x1 = min(xlim), max(xlim)
    y0, y1 = min(ylim), max(ylim)

    def _inside(px: float, py: float) -> bool:
        return (x0 <= px <= x1) and (y0 <= py <= y1)

    def _clip_segment(ax_: float, ay_: float, bx_: float, by_: float) -> tuple[float, float, float, float] | None:
        # Liang-Barsky parametric segment clipping against [x0, x1] x [y0, y1]
        dx = bx_ - ax_
        dy = by_ - ay_
        t0, t1 = 0.0, 1.0
        for p, q in ((-dx, ax_ - x0), (dx, x1 - ax_), (-dy, ay_ - y0), (dy, y1 - ay_)):
            if p == 0.0:
                if q < 0.0:
                    return None
            else:
                r = q / p
                if p < 0.0:
                    if r > t1:
                        return None
                    if r > t0:
                        t0 = r
                else:
                    if r < t0:
                        return None
                    if r < t1:
                        t1 = r
        return ax_ + t0 * dx, ay_ + t0 * dy, ax_ + t1 * dx, ay_ + t1 * dy

    out_x: list[float] = []
    out_y: list[float] = []
    n = len(x_in)
    if n == 0:
        return x_in.copy(), y_in.copy()
    if n == 1:
        if _inside(x_in[0], y_in[0]):
            return x_in.copy(), y_in.copy()
        return np.array([np.nan]), np.array([np.nan])

    pen_down = False
    for i in range(n - 1):
        ax_, ay_, bx_, by_ = x_in[i], y_in[i], x_in[i + 1], y_in[i + 1]
        if np.isnan(ax_) or np.isnan(ay_) or np.isnan(bx_) or np.isnan(by_):
            if pen_down:
                out_x.append(np.nan)
                out_y.append(np.nan)
                pen_down = False
            continue
        clipped = _clip_segment(ax_, ay_, bx_, by_)
        if clipped is None:
            if pen_down:
                out_x.append(np.nan)
                out_y.append(np.nan)
                pen_down = False
            continue
        cx0, cy0, cx1, cy1 = clipped
        if not pen_down:
            out_x.append(cx0)
            out_y.append(cy0)
            pen_down = True
        elif abs(cx0 - out_x[-1]) > 1e-9 or abs(cy0 - out_y[-1]) > 1e-9:
            out_x.extend([np.nan, cx0])
            out_y.extend([np.nan, cy0])
        out_x.append(cx1)
        out_y.append(cy1)
        if not _inside(bx_, by_):
            out_x.append(np.nan)
            out_y.append(np.nan)
            pen_down = False

    return np.asarray(out_x, dtype=float), np.asarray(out_y, dtype=float)


def clip_scatter_to_box(
    x: np.ndarray,
    y: np.ndarray,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray]:
    """Filter scatter points strictly to `(xlim, ylim)` so removing SVG `<clipPath>` never leaks points."""
    x_arr = np.asarray(x, dtype=float).ravel()
    y_arr = np.asarray(y, dtype=float).ravel()
    x0, x1 = min(xlim), max(xlim)
    y0, y1 = min(ylim), max(ylim)
    mask = (x_arr >= x0) & (x_arr <= x1) & (y_arr >= y0) & (y_arr <= y1)
    return x_arr[mask], y_arr[mask]


def sanitize_svg_for_ppt(svg_path: str | Path) -> None:
    """
    Post-process a Matplotlib SVG so PowerPoint's 'Convert to Shape' (转换为形状) works with
    ZERO garbled characters (`乱码`), ZERO `<tspan>` pileups, and ZERO black `<clipPath>` boxes.
    """
    svg_path = Path(svg_path)
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)

    tree = ET.parse(svg_path)
    root = tree.getroot()

    for parent in list(root.iter()):
        new_children: list[ET.Element] = []
        modified = False
        for child in list(parent):
            if child.tag.endswith("clipPath"):
                modified = True
                continue
            if child.tag.endswith("text"):
                flattened = _flatten_mathtext_text_element(child)
                new_children.extend(flattened)
                modified = True
                continue
            new_children.append(child)

        if modified:
            parent[:] = new_children

        if "clip-path" in parent.attrib:
            del parent.attrib["clip-path"]
        tf = parent.attrib.get("transform", "")
        if tf.startswith("rotate(-0 ") or tf.startswith("rotate(0 "):
            del parent.attrib["transform"]

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    cleaned = re.sub(rb"clip-path:\s*url\(#[^)]+\);?", b"", xml_bytes)
    svg_path.write_bytes(cleaned)


def audit_svg_ppt_compatibility(svg_path: str | Path) -> dict[str, Any]:
    """
    Programmatically verify that an SVG file is 100% immune to PowerPoint garbled text & black boxes:
      - `tspan_count == 0`
      - `clip_path_count == 0`
      - `bad_fonts == []` (no DejaVu Sans, STIX, or cm* TeX fonts)
      - `missing_arial_glyphs == []` (verified against system Arial.ttf charmap)
    """
    svg_path = Path(svg_path)
    root = ET.parse(svg_path).getroot()

    ft = _get_arial_ft2(False, False)
    arial_cmap = set(ft.get_charmap().keys()) if ft is not None else set()

    tspan_count = 0
    clip_path_count = 0
    bad_fonts: set[str] = set()
    missing_glyphs: set[tuple[str, str]] = set()
    text_samples: list[str] = []

    for el in root.iter():
        if el.tag.endswith("tspan"):
            tspan_count += 1
        if el.tag.endswith("clipPath") or "clip-path" in el.attrib:
            clip_path_count += 1
        st = el.attrib.get("style", "")
        for bad in ("DejaVu", "STIX", "cmex", "cmsy", "cmr", "cmmi"):
            if bad.lower() in st.lower():
                bad_fonts.add(st)
        if el.tag.endswith("text") and el.text:
            text_samples.append(el.text)
            if arial_cmap and not _contains_cjk(el.text):
                for ch in el.text:
                    if ord(ch) not in arial_cmap:
                        missing_glyphs.add((ch, hex(ord(ch))))

    return {
        "svg": str(svg_path),
        "text_element_count": len(text_samples),
        "tspan_count": tspan_count,
        "clip_path_count": clip_path_count,
        "bad_fonts": sorted(bad_fonts),
        "missing_arial_glyphs": sorted(missing_glyphs),
        "ok": (
            tspan_count == 0
            and clip_path_count == 0
            and len(bad_fonts) == 0
            and len(missing_glyphs) == 0
        ),
    }


class OriginColumn:
    """Represents a single data column with OriginPro 3-row metadata headers."""

    def __init__(self, long_name: str, units: str, comment: str, values: Sequence[float | str]) -> None:
        self.long_name = long_name
        self.units = units
        self.comment = comment
        self.values = list(values)


def write_origin_csv(csv_path: str | Path, columns: Sequence[OriginColumn]) -> None:
    """
    Write an OriginPro / Orange / Excel compatible UTF-8-BOM CSV with Origin's native 3 header rows:
      Row 1: Long Name
      Row 2: Units
      Row 3: Comments (Legend Name)
      Row 4+: Data values
    """
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    max_len = max((len(c.values) for c in columns), default=0)

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([c.long_name for c in columns])
        writer.writerow([c.units for c in columns])
        writer.writerow([c.comment for c in columns])
        for r_idx in range(max_len):
            row = []
            for col in columns:
                if r_idx < len(col.values):
                    val = col.values[r_idx]
                    if isinstance(val, (float, np.floating)) and (np.isnan(val) or np.isinf(val)):
                        row.append("")
                    else:
                        row.append(val)
                else:
                    row.append("")
            writer.writerow(row)


def _col_letter(idx_zero_based: int) -> str:
    res = ""
    n = idx_zero_based + 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        res = chr(65 + rem) + res
    return res


def write_origin_xlsx(xlsx_path: str | Path, sheets: list[tuple[str, Sequence[OriginColumn]]]) -> None:
    """
    Write a standard multi-sheet `.xlsx` workbook (zero external dependencies) with OriginPro's
    3-row header (`Long Name`, `Units`, `Comments`) on every worksheet.
    """
    xlsx_path = Path(xlsx_path)
    xlsx_path.parent.mkdir(parents=True, exist_ok=True)

    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '  <Default Extension="xml" ContentType="application/xml"/>',
        '  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
    ]
    wb_sheets = []
    wb_rels = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    ]

    sheet_xmls: dict[str, str] = {}
    for s_idx, (raw_name, cols) in enumerate(sheets, start=1):
        safe_name = re.sub(r"[\[\]:*?/\\]", "_", raw_name)[:31]
        part_name = f"worksheets/sheet{s_idx}.xml"
        content_types.append(
            f'  <Override PartName="/xl/{part_name}" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        )
        wb_sheets.append(f'    <sheet name="{escape(safe_name)}" sheetId="{s_idx}" r:id="rId{s_idx}"/>')
        wb_rels.append(
            f'  <Relationship Id="rId{s_idx}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="{part_name}"/>'
        )

        max_len = max((len(c.values) for c in cols), default=0)
        rows_xml = []
        headers = [
            [c.long_name for c in cols],
            [c.units for c in cols],
            [c.comment for c in cols],
        ]
        for r_num, h_row in enumerate(headers, start=1):
            cells = []
            for c_idx, text_val in enumerate(h_row):
                ref = f"{_col_letter(c_idx)}{r_num}"
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(text_val))}</t></is></c>')
            rows_xml.append(f'    <row r="{r_num}">{"".join(cells)}</row>')

        for d_idx in range(max_len):
            r_num = d_idx + 4
            cells = []
            for c_idx, col in enumerate(cols):
                if d_idx >= len(col.values):
                    continue
                val = col.values[d_idx]
                if val is None or (isinstance(val, (float, np.floating)) and (np.isnan(val) or np.isinf(val))):
                    continue
                ref = f"{_col_letter(c_idx)}{r_num}"
                if isinstance(val, (int, float, np.integer, np.floating)):
                    cells.append(f'<c r="{ref}"><v>{float(val):.8g}</v></c>')
                else:
                    cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(val))}</t></is></c>')
            rows_xml.append(f'    <row r="{r_num}">{"".join(cells)}</row>')

        sheet_xmls[f"xl/{part_name}"] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">\n'
            '  <sheetData>\n'
            + "\n".join(rows_xml)
            + "\n  </sheetData>\n</worksheet>"
        )

    content_types.append("</Types>")
    wb_rels.append("</Relationships>")
    workbook_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">\n'
        "  <sheets>\n"
        + "\n".join(wb_sheets)
        + "\n  </sheets>\n</workbook>"
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>\n'
        "</Relationships>"
    )

    with zipfile.ZipFile(xlsx_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "\n".join(content_types))
        zf.writestr("_rels/.rels", root_rels)
        zf.writestr("xl/workbook.xml", workbook_xml)
        zf.writestr("xl/_rels/workbook.xml.rels", "\n".join(wb_rels))
        for path_in_zip, xml_content in sheet_xmls.items():
            zf.writestr(path_in_zip, xml_content)


def build_editable_svg_pptx(
    pptx_out_path: str | Path,
    slides_spec: Sequence[dict[str, Any]],
) -> Path:
    """
    Build a 16:9 Clean Academic PowerPoint deck (`13.333" x 7.5"`) where every figure is embedded
    as a native Office 2016+ `<asvg:svgBlip>` vector graphic (paired with a 450 DPI PNG fallback) so
    users can right-click -> 'Convert to Shape (转换为形状)' in PowerPoint with zero garbled text.

    Each item in `slides_spec` is a dict:
      {
        "title": str,
        "svg_path": str | Path,
        "png_path": str | Path,
        "takeaways": list[str],   # 3-4 concise academic bullets (<= 380 chars total on slide)
        "footer": str,
      }
    """
    from PIL import Image
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT
    from pptx.opc.package import Part
    from pptx.opc.packuri import PackURI
    from pptx.oxml import parse_xml
    from pptx.util import Inches, Pt

    out_path = Path(pptx_out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.500)
    blank_layout = prs.slide_layouts[6]

    navy = RGBColor(0x1E, 0x3A, 0x5F)
    ink = RGBColor(0x1F, 0x29, 0x37)
    muted = RGBColor(0x6B, 0x72, 0x80)
    accent = RGBColor(0xC2, 0x41, 0x0C)

    def _set_cjk_run_font(run: Any, size_pt: float, color: RGBColor, bold: bool = False) -> None:
        run.font.name = "Arial"
        run.font.size = Pt(size_pt)
        run.font.bold = bold
        run.font.color.rgb = color
        rPr = run._r.get_or_add_rPr()
        for existing_ea in list(rPr.findall("{http://schemas.openxmlformats.org/drawingml/2006/main}ea")):
            rPr.remove(existing_ea)
        rPr.append(parse_xml('<a:ea xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" typeface="Microsoft YaHei"/>'))

    total = len(slides_spec)
    for idx, spec in enumerate(slides_spec, start=1):
        slide = prs.slides.add_slide(blank_layout)

        # 1. Left-aligned single-line academic title
        tb_title = slide.shapes.add_textbox(Inches(0.60), Inches(0.32), Inches(12.10), Inches(0.58))
        tf_t = tb_title.text_frame
        tf_t.word_wrap = True
        tf_t.margin_left = tf_t.margin_right = tf_t.margin_top = tf_t.margin_bottom = 0
        p_t = tf_t.paragraphs[0]
        r_t = p_t.add_run()
        r_t.text = spec["title"]
        _set_cjk_run_font(r_t, 22.0, navy, bold=True)

        # 2. Native SVG + 450 DPI PNG picture in left/main column (x=0.60"..7.75", y=1.02"..6.68")
        svg_p = Path(spec["svg_path"])
        png_p = Path(spec["png_path"])
        with Image.open(png_p) as im:
            im_w, im_h = im.size
        box_x, box_y, max_w, max_h = 0.60, 1.02, 7.15, 5.66
        aspect = im_w / max(im_h, 1)
        if max_w / max_h > aspect:
            pic_h = max_h
            pic_w = pic_h * aspect
        else:
            pic_w = max_w
            pic_h = pic_w / aspect
        px = box_x + 0.5 * (max_w - pic_w)
        py = box_y + 0.5 * (max_h - pic_h)

        pic = slide.shapes.add_picture(str(png_p), Inches(px), Inches(py), width=Inches(pic_w), height=Inches(pic_h))
        svg_part = Part(
            PackURI(f"/ppt/media/editable_fig_{idx}.svg"),
            "image/svg+xml",
            prs.part.package,
            blob=svg_p.read_bytes(),
        )
        svg_rid = slide.part.relate_to(svg_part, RT.IMAGE)
        blip = pic._element.xpath(".//a:blip")[0]
        ext_lst = blip.find("{http://schemas.openxmlformats.org/drawingml/2006/main}extLst")
        if ext_lst is None:
            ext_lst = parse_xml('<a:extLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>')
            blip.append(ext_lst)
        ext_lst.append(
            parse_xml(
                f'<a:ext xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
                f'uri="{{96DAC541-7B7A-43D3-8B79-37D633B846F1}}">'
                f'<asvg:svgBlip xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/SVG/main" '
                f'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
                f'r:embed="{svg_rid}"/></a:ext>'
            )
        )

        # 3. Right-hand academic takeaway column (x=8.05"..12.75", y=1.18"..6.40")
        tb_body = slide.shapes.add_textbox(Inches(8.05), Inches(1.18), Inches(4.68), Inches(5.25))
        tf_b = tb_body.text_frame
        tf_b.word_wrap = True
        tf_b.margin_left = tf_b.margin_right = tf_b.margin_top = tf_b.margin_bottom = 0

        p_hdr = tf_b.paragraphs[0]
        p_hdr.space_after = Pt(10)
        r_hdr = p_hdr.add_run()
        r_hdr.text = "核心物理结论与编辑说明"
        _set_cjk_run_font(r_hdr, 16.0, accent, bold=True)

        for b_line in spec.get("takeaways", []):
            p_item = tf_b.add_paragraph()
            p_item.space_after = Pt(10)
            p_item.line_spacing = 1.25
            r_item = p_item.add_run()
            r_item.text = b_line
            _set_cjk_run_font(r_item, 13.5, ink, bold=False)

        # 4. Clean footer at y >= 6.88" (>= 0.88 * 7.5" = 6.60")
        tb_foot = slide.shapes.add_textbox(Inches(0.60), Inches(6.92), Inches(12.13), Inches(0.36))
        tf_f = tb_foot.text_frame
        tf_f.word_wrap = False
        tf_f.margin_left = tf_f.margin_right = tf_f.margin_top = tf_f.margin_bottom = 0
        p_f = tf_f.paragraphs[0]
        r_f = p_f.add_run()
        r_f.text = f"{spec.get('footer', '')}    |    {idx} / {total}"
        _set_cjk_run_font(r_f, 10.5, muted, bold=False)

    prs.save(str(out_path))

    # Ensure [Content_Types].xml registers Default Extension="svg" ContentType="image/svg+xml"
    tmp_path = out_path.with_suffix(".tmp.pptx")
    with zipfile.ZipFile(out_path, "r") as zin, zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml" and b'Extension="svg"' not in data:
                data = data.replace(
                    b"</Types>",
                    b'<Default Extension="svg" ContentType="image/svg+xml"/></Types>',
                )
            zout.writestr(item, data)
    tmp_path.replace(out_path)
    return out_path

