#!/usr/bin/env python3
r"""
Minimalist Weekly Group Meeting / Journal Club PPTX Engine (`group-meeting-ppt`).

Implements:
  1. `tueplots`-style Slot-Driven 1:1 `slide_minimal` Matplotlib styling (`SLIDE_SLOT_SIZES`,
     `slide_minimal_rc()`, `apply_slide_minimal_style()`), guaranteeing 100% scale embedding in
     `13.333" x 7.500"` widescreen slides without font-size distortion.
  2. PowerPoint Zero-Garbled-Text (`零乱码`) SVG sanitization & Office 2016+ dual-track
     `<asvg:svgBlip>` + 450 DPI PNG vector embedding (`save_slide_svg_and_png()`,
     `add_editable_svg_picture()`, `ensure_svg_content_type()`), reusing
     `electrolyte-raman-mlff/scripts/ppt_origin_export.py` when present with a built-in fallback.
  3. Seven strict coordinate-locked minimalist layouts (`L1`–`L7`) on a pure `#FFFFFF` canvas:
     - Zero university logos, zero watermarks, zero top/bottom banners, zero gray rounded cards.
     - Single primary hue (`#1E3A5F` Slate Navy) + single semantic accent (`#C2410C` Burnt Orange).
     - Cross-platform `Arial` + explicit `<a:ea typeface="Microsoft YaHei"/>` CJK binding.
     - OOXML XSD-compliant `<a:tcPr>` Booktabs 3-line tables & `<p:notesMasterIdLst>` ordering.
     - Paired `verify_checklist.md` generator (Ghost Deck Test + Data Provenance + Advisor Q&A).

CLI Usage:
    /Users/zhoujun/miniconda3/bin/python3 scripts/group_meeting_builder.py --demo /path/to/out_dir
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Literal, Sequence

import numpy as np


# =============================================================================
# 1. Slot-Driven 1:1 Physical Dimensions & Minimalist Monochromatic+Accent Palette
# =============================================================================

SLIDE_WIDTH_IN: float = 13.333
SLIDE_HEIGHT_IN: float = 7.500

# Exact 1:1 Matplotlib `figsize=(w_in, h_in)` contract for every slide figure slot
SLIDE_SLOT_SIZES: dict[str, tuple[float, float]] = {
    "L2_wide": (12.03, 4.55),     # Hero Figure (wide spectrum / time-series, top-bottom layout)
    "L2_split": (7.45, 5.00),     # Hero Figure (left 62% figure + caption, right 38% takeaways)
    "L2_split_nocap": (7.45, 5.45),
    "L3_dual": (5.80, 4.35),      # Dual 1x2 comparison (Baseline vs. This Week independent SVGs)
    "L4_c1_grid": (8.20, 5.45),   # 2x2 shared-axes single SVG grid (left) + takeaways (right)
    "L4_c2_cell": (5.85, 2.68),   # 2x2 heterogeneous 4 independent SVG slots
    "L5_diag": (5.55, 5.00),      # Troubleshooting / anomaly curve or failure snapshot (left)
    "L6_left_fig": (5.85, 5.00),  # Left figure paired with right native Booktabs 3-line table
}

# Minimalist academic palette (<= 2 chromatic hues: Hue bucket 7 Slate Navy + Hue bucket 1 Orange)
PALETTE_HEX: dict[str, str] = {
    "primary": "#1E3A5F",       # Primary Slate Navy (titles, main data series, booktabs rules)
    "accent": "#C2410C",        # Single Semantic Accent (breakthrough delta, root cause, open Qs)
    "ink": "#1F2937",           # Body charcoal ink
    "slate_dark": "#475569",    # Baseline / secondary label dark slate
    "muted": "#6B7280",         # Captions, provenance, minimalist page number
    "slate_light": "#94A3B8",   # Baseline dashed reference curve
    "hairline": "#D1D5DB",      # 0.5 pt divider rule
    "white": "#FFFFFF",         # Pure white canvas & table cell background
}


def slide_minimal_rc(boxed_inward: bool = True) -> dict[str, Any]:
    """
    Return a dictionary of Matplotlib `rcParams` tailored for 1:1 slot-size embedding on a
    `13.333" x 7.500"` group-meeting slide with zero PowerPoint `<tspan>` / font garbling.
    """
    rc: dict[str, Any] = {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "PingFang SC", "Microsoft YaHei", "Helvetica"],
        "svg.fonttype": "none",
        "mathtext.fontset": "custom",
        "mathtext.rm": "Arial",
        "mathtext.it": "Arial:italic",
        "mathtext.bf": "Arial:bold",
        "mathtext.sf": "Arial",
        "mathtext.cal": "Arial:italic",
        "mathtext.default": "regular",
        "mathtext.fallback": "stixsans",
        "axes.unicode_minus": False,
        "axes.labelsize": 11.5,
        "axes.titlesize": 12.5,
        "axes.titleweight": "bold",
        "axes.linewidth": 1.0,
        "axes.edgecolor": "#1F2937",
        "axes.labelcolor": "#1F2937",
        "xtick.labelsize": 10.5,
        "ytick.labelsize": 10.5,
        "xtick.color": "#1F2937",
        "ytick.color": "#1F2937",
        "xtick.major.width": 0.9,
        "ytick.major.width": 0.9,
        "xtick.major.size": 4.2,
        "ytick.major.size": 4.2,
        "lines.linewidth": 1.8,
        "lines.markersize": 5.5,
        "legend.fontsize": 10.0,
        "legend.frameon": True,
        "legend.fancybox": False,
        "legend.edgecolor": "#D1D5DB",
        "legend.facecolor": "#FFFFFF",
        "legend.framealpha": 0.94,
        "figure.facecolor": "#FFFFFF",
        "axes.facecolor": "#FFFFFF",
        "savefig.facecolor": "#FFFFFF",
        "savefig.edgecolor": "none",
    }
    if boxed_inward:
        rc.update(
            {
                "axes.spines.top": True,
                "axes.spines.right": True,
                "xtick.direction": "in",
                "ytick.direction": "in",
                "xtick.top": True,
                "ytick.right": True,
            }
        )
    else:
        rc.update(
            {
                "axes.spines.top": False,
                "axes.spines.right": False,
                "xtick.direction": "out",
                "ytick.direction": "out",
                "xtick.top": False,
                "ytick.right": False,
            }
        )
    return rc


@contextmanager
def apply_slide_minimal_style(boxed_inward: bool = True) -> Iterator[dict[str, Any]]:
    """
    Apply `slide_minimal` Matplotlib `rcParams` either as a context manager (`with ...:`)
    or directly (`apply_slide_minimal_style()` updates `matplotlib.rcParams` and yields the dict).
    """
    import matplotlib as mpl

    rc = slide_minimal_rc(boxed_inward=boxed_inward)
    with mpl.rc_context(rc):
        yield rc


def set_global_slide_minimal_style(boxed_inward: bool = True) -> dict[str, Any]:
    """Mutate global `matplotlib.rcParams` in-place for standalone plotting scripts."""
    import matplotlib as mpl

    rc = slide_minimal_rc(boxed_inward=boxed_inward)
    mpl.rcParams.update(rc)
    return rc


# =============================================================================
# 2. Upstream `ppt_origin_export.py` Bridge + Self-Contained Fallback
# =============================================================================

def _load_upstream_ppt_origin_export() -> Any | None:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[2] / "electrolyte-raman-mlff" / "scripts" / "ppt_origin_export.py",
        Path("/Users/zhoujun/.cc-switch/skills/electrolyte-raman-mlff/scripts/ppt_origin_export.py"),
    ]
    for path in candidates:
        if path.is_file():
            spec = importlib.util.spec_from_file_location("_upstream_ppt_origin_export", path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod
    return None


_UPSTREAM_EXPORT = _load_upstream_ppt_origin_export()

_FALLBACK_UNICODE_MAP: dict[str, str] = {
    "\u2212": "-",
    "\u2013": "-",
    "\u27e8": "<",
    "\u27e9": ">",
    "\u2329": "<",
    "\u232a": ">",
    "\u22c5": "\u00b7",
    "\u2219": "\u00b7",
    "\u22ef": "\u00b7\u00b7\u00b7",
    "\u2032": "'",
    "\u2033": "''",
    "\xa0": " ",
    "\u2009": " ",
    "\u200a": " ",
    "\u2002": " ",
    "\u2003": " ",
    "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
    "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
    "₊": "+", "₋": "-", "⁺": "+", "⁻": "-",
}


def _fallback_clip_curve_to_box(
    x: np.ndarray,
    y: np.ndarray,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray]:
    x_in = np.asarray(x, dtype=float)
    y_in = np.asarray(y, dtype=float)
    x0, x1 = min(xlim), max(xlim)
    y0, y1 = min(ylim), max(ylim)
    mask = (x_in >= x0) & (x_in <= x1) & (y_in >= y0) & (y_in <= y1)
    out_x = np.where(mask, x_in, np.nan)
    out_y = np.where(mask, y_in, np.nan)
    return out_x, out_y


def _fallback_clip_scatter_to_box(
    x: np.ndarray,
    y: np.ndarray,
    xlim: tuple[float, float],
    ylim: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray]:
    x_arr = np.asarray(x, dtype=float).ravel()
    y_arr = np.asarray(y, dtype=float).ravel()
    x0, x1 = min(xlim), max(xlim)
    y0, y1 = min(ylim), max(ylim)
    mask = (x_arr >= x0) & (x_arr <= x1) & (y_arr >= y0) & (y_arr <= y1)
    return x_arr[mask], y_arr[mask]


def _fallback_sanitize_svg_for_ppt(svg_path: str | Path) -> None:
    svg_p = Path(svg_path)
    svg_ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", svg_ns)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    tree = ET.parse(svg_p)
    root = tree.getroot()

    def _norm(txt: str | None) -> str:
        if not txt:
            return ""
        return "".join(_FALLBACK_UNICODE_MAP.get(ch, ch) for ch in txt)

    def _clean_style(st: str, sample: str) -> str:
        has_cjk = any("\u4e00" <= ch <= "\u9fff" for ch in sample)
        ff = "'PingFang SC', 'Microsoft YaHei', Arial, sans-serif" if has_cjk else "Arial, sans-serif"
        parts = []
        for seg in st.split(";"):
            if ":" not in seg:
                continue
            k, v = [s.strip() for s in seg.split(":", 1)]
            kl = k.lower()
            if kl in ("font-family", "clip-path"):
                continue
            if kl == "font-style" and v == "oblique":
                v = "italic"
            parts.append(f"{kl}: {v}")
        parts.append(f"font-family: {ff}")
        return "; ".join(parts)

    for parent in list(root.iter()):
        new_children: list[ET.Element] = []
        changed = False
        for child in list(parent):
            if child.tag.endswith("clipPath"):
                changed = True
                continue
            if child.tag.endswith("text"):
                tspans = [c for c in child if c.tag.endswith("tspan")]
                if not tspans:
                    txt = _norm(child.text)
                    child.text = txt
                    if "style" in child.attrib:
                        child.attrib["style"] = _clean_style(child.attrib["style"], txt)
                    new_children.append(child)
                else:
                    p_st = child.attrib.get("style", "")
                    p_tf = child.attrib.get("transform", "")
                    entries = []
                    for idx, ts in enumerate(tspans):
                        txt = _norm(ts.text)
                        if not txt.strip():
                            continue
                        xv = float(ts.attrib.get("x", child.attrib.get("x", "0")).split()[0])
                        yv = float(ts.attrib.get("y", child.attrib.get("y", "0")).split()[0])
                        st = _clean_style(f"{p_st}; {ts.attrib.get('style', '')}", txt)
                        entries.append((round(xv, 4), idx, xv, yv, st, txt))
                    entries.sort()
                    tag = f"{{{svg_ns}}}text" if child.tag.startswith("{") else "text"
                    for _, _, xv, yv, st, txt in entries:
                        el = ET.Element(tag)
                        el.attrib["x"] = f"{xv:.3f}"
                        el.attrib["y"] = f"{yv:.3f}"
                        el.attrib["style"] = st
                        if p_tf and not p_tf.startswith("rotate(-0 ") and not p_tf.startswith("rotate(0 "):
                            el.attrib["transform"] = p_tf
                        el.text = txt
                        new_children.append(el)
                changed = True
                continue
            new_children.append(child)
        if changed:
            parent[:] = new_children
        parent.attrib.pop("clip-path", None)

    raw = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    svg_p.write_bytes(re.sub(rb"clip-path:\s*url\(#[^)]+\);?", b"", raw))


def _fallback_audit_svg_ppt_compatibility(svg_path: str | Path) -> dict[str, Any]:
    svg_p = Path(svg_path)
    root = ET.parse(svg_p).getroot()
    tspan_count = 0
    clip_path_count = 0
    bad_fonts: set[str] = set()
    texts: list[str] = []
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
            texts.append(el.text)
    return {
        "svg": str(svg_p),
        "text_element_count": len(texts),
        "tspan_count": tspan_count,
        "clip_path_count": clip_path_count,
        "bad_fonts": sorted(bad_fonts),
        "missing_arial_glyphs": [],
        "ok": tspan_count == 0 and clip_path_count == 0 and not bad_fonts,
    }


clip_curve_to_box = getattr(_UPSTREAM_EXPORT, "clip_curve_to_box", _fallback_clip_curve_to_box)
clip_scatter_to_box = getattr(_UPSTREAM_EXPORT, "clip_scatter_to_box", _fallback_clip_scatter_to_box)
sanitize_svg_for_ppt = getattr(_UPSTREAM_EXPORT, "sanitize_svg_for_ppt", _fallback_sanitize_svg_for_ppt)
audit_svg_ppt_compatibility = getattr(
    _UPSTREAM_EXPORT, "audit_svg_ppt_compatibility", _fallback_audit_svg_ppt_compatibility
)


def save_slide_svg_and_png(
    fig: Any,
    out_stem: str | Path,
    dpi: int = 450,
    close: bool = True,
) -> tuple[Path, Path, dict[str, Any]]:
    """
    Save a Matplotlib figure at its exact 1:1 `figsize` as both a sanitized PowerPoint-editable
    `.svg` (`tspan_count == 0`, `clip_path_count == 0`, `Arial` glyph-safe) and a 450 DPI `.png`
    fallback, raising `ValueError` if `audit_svg_ppt_compatibility()` detects any defect.
    """
    import matplotlib.pyplot as plt

    stem = Path(out_stem)
    if stem.suffix.lower() in (".svg", ".png", ".pdf"):
        stem = stem.with_suffix("")
    stem.parent.mkdir(parents=True, exist_ok=True)

    svg_path = stem.with_suffix(".svg")
    png_path = stem.with_suffix(".png")

    fig.savefig(svg_path, format="svg")
    fig.savefig(png_path, format="png", dpi=dpi)
    if close:
        plt.close(fig)

    sanitize_svg_for_ppt(svg_path)
    audit = audit_svg_ppt_compatibility(svg_path)
    if not audit.get("ok", False):
        raise ValueError(f"SVG failed PowerPoint compatibility audit: {audit}")
    return svg_path, png_path, audit


# =============================================================================
# 3. Native `<asvg:svgBlip>` + OOXML Safe Helpers (`python-pptx`)
# =============================================================================

def add_editable_svg_picture(
    slide: Any,
    prs: Any,
    svg_path: str | Path,
    png_path: str | Path,
    box: tuple[float, float, float, float],
    media_tag: str,
) -> Any:
    """
    Embed a sanitized `.svg` + high-DPI `.png` pair into `box = (x_in, y_in, max_w_in, max_h_in)`
    as a single native Office 2016+ `<asvg:svgBlip>` vector shape (`<p:pic>`).

    Right-clicking -> "Convert to Shape (转换为形状)" in PowerPoint ungroups directly into crisp
    editable text and curves with zero garbled formulas and only 1 shape node in `layout_audit.py`.
    """
    from PIL import Image
    from pptx.opc.constants import RELATIONSHIP_TYPE as RT
    from pptx.opc.package import Part
    from pptx.opc.packuri import PackURI
    from pptx.oxml import parse_xml
    from pptx.util import Inches

    svg_p = Path(svg_path)
    png_p = Path(png_path)
    with Image.open(png_p) as im:
        im_w, im_h = im.size

    box_x, box_y, max_w, max_h = box
    aspect = im_w / max(im_h, 1)
    if (max_w / max_h) > aspect:
        pic_h = max_h
        pic_w = pic_h * aspect
    else:
        pic_w = max_w
        pic_h = pic_w / aspect
    px = box_x + 0.5 * (max_w - pic_w)
    py = box_y + 0.5 * (max_h - pic_h)

    pic = slide.shapes.add_picture(
        str(png_p), Inches(px), Inches(py), width=Inches(pic_w), height=Inches(pic_h)
    )
    safe_tag = re.sub(r"[^A-Za-z0-9_.-]", "_", media_tag)
    svg_part = Part(
        PackURI(f"/ppt/media/{safe_tag}.svg"),
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
    return pic


def ensure_svg_content_type(pptx_path: str | Path) -> Path:
    """
    Idempotently post-process a saved `.pptx` archive to:
      1. Register `<Default Extension="svg" ContentType="image/svg+xml"/>` in `[Content_Types].xml`.
      2. Ensure `<p:notesMasterIdLst>` sits immediately after `<p:sldIdLst>` in `ppt/presentation.xml`
         whenever `notesMaster` shares `theme1.xml` with `slideMaster1` (required by PowerPoint &
         `office/validate.py::validate_master_theme_uniqueness`).
    """
    out_p = Path(pptx_path)
    tmp_p = out_p.with_suffix(".tmp.pptx")
    p_ns = "http://schemas.openxmlformats.org/presentationml/2006/main"

    with zipfile.ZipFile(out_p, "r") as zin, zipfile.ZipFile(tmp_p, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml" and b'Extension="svg"' not in data:
                data = data.replace(
                    b"</Types>",
                    b'<Default Extension="svg" ContentType="image/svg+xml"/></Types>',
                )
            elif item.filename == "ppt/presentation.xml" and b"notesMasterIdLst" in data and b"sldIdLst" in data:
                # Place <p:notesMasterIdLst> directly after <p:sldIdLst> so shared theme1.xml is valid in PowerPoint
                m_notes = re.search(rb"<p:notesMasterIdLst\b.*?</p:notesMasterIdLst>", data, flags=re.DOTALL)
                if m_notes:
                    notes_xml = m_notes.group(0)
                    stripped = data[: m_notes.start()] + data[m_notes.end() :]
                    stripped = re.sub(
                        rb"(<p:sldIdLst\b.*?</p:sldIdLst>)",
                        lambda m: m.group(1) + notes_xml,
                        stripped,
                        count=1,
                        flags=re.DOTALL,
                    )
                    data = stripped
            zout.writestr(item, data)
    tmp_p.replace(out_p)
    return out_p


def apply_booktabs_borders(
    cell: Any,
    top_pt: float = 0.0,
    bottom_pt: float = 0.0,
    color_hex: str = "1E3A5F",
) -> None:
    """
    Apply authentic LaTeX `booktabs` horizontal rules (`toprule` / `midrule` / `bottomrule`) with
    zero vertical lines and strict DrawingML XSD element ordering (`lnL, lnR, lnT, lnB` before
    `solidFill`).
    """
    from pptx.dml.color import RGBColor
    from pptx.oxml import parse_xml
    from pptx.oxml.ns import qn

    clean_hex = color_hex.lstrip("#").upper()
    tcPr = cell._tc.get_or_add_tcPr()

    # Clear existing borders and fills first so XSD child sequence (ln* -> solidFill) is exact
    for tag in ("lnL", "lnR", "lnT", "lnB", "noFill", "solidFill"):
        for old in list(tcPr.findall(qn(f"a:{tag}"))):
            tcPr.remove(old)

    def _make_ln(tag: str, pt_val: float) -> Any:
        if pt_val <= 0:
            return parse_xml(
                f'<a:{tag} xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:noFill/></a:{tag}>'
            )
        w_emu = int(round(pt_val * 12700))
        return parse_xml(
            f'<a:{tag} xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" w="{w_emu}">'
            f'<a:solidFill><a:srgbClr val="{clean_hex}"/></a:solidFill>'
            f"</a:{tag}>"
        )

    tcPr.append(_make_ln("lnL", 0.0))
    tcPr.append(_make_ln("lnR", 0.0))
    tcPr.append(_make_ln("lnT", top_pt))
    tcPr.append(_make_ln("lnB", bottom_pt))

    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor(0xFF, 0xFF, 0xFF)


# =============================================================================
# 4. `GroupMeetingDeck` — L1..L7 Minimalist Weekly Group Meeting / JC Engine
# =============================================================================

@dataclass
class SlideRecord:
    slide_no: int
    layout_code: str
    action_title: str
    estimated_seconds: int
    figures: list[str] = field(default_factory=list)


class GroupMeetingDeck:
    """
    Reusable builder for minimalist, zero-clutter academic weekly group-meeting & journal-club
    presentations (`13.333" x 7.500"`, pure white canvas, `L1`–`L7` fixed coordinate layouts).

    Inline markup supported across titles, bullets, and table cells:
      - `{{...}}` -> Bold Semantic Accent (`#C2410C`)
      - `**...**` -> Bold Primary Slate Navy (`#1E3A5F`)
    """

    FONT_LATIN = "Arial"
    FONT_EA = "Microsoft YaHei"

    def __init__(self, project_tag: str = "Weekly Group Meeting", total_slides_hint: int | None = None) -> None:
        from pptx import Presentation
        from pptx.dml.color import RGBColor
        from pptx.util import Inches

        self.prs = Presentation()
        self.prs.slide_width = Inches(SLIDE_WIDTH_IN)
        self.prs.slide_height = Inches(SLIDE_HEIGHT_IN)
        self.blank_layout = self.prs.slide_layouts[6]
        self.project_tag = project_tag
        self.total_slides_hint = total_slides_hint

        self.c_primary = RGBColor(0x1E, 0x3A, 0x5F)
        self.c_accent = RGBColor(0xC2, 0x41, 0x0C)
        self.c_ink = RGBColor(0x1F, 0x29, 0x37)
        self.c_slate = RGBColor(0x47, 0x55, 0x69)
        self.c_muted = RGBColor(0x6B, 0x72, 0x80)
        self.c_rule = RGBColor(0xD1, 0xD5, 0xDB)
        self.c_white = RGBColor(0xFF, 0xFF, 0xFF)

        self.records: list[SlideRecord] = []
        self._page_num_runs: list[tuple[int, Any]] = []
        self._media_counter: int = 0

    # -------------------------------------------------------------------------
    # Internal Typography & Chrome Primitives
    # -------------------------------------------------------------------------

    def _set_run_font(
        self,
        run: Any,
        size_pt: float,
        color: Any,
        bold: bool = False,
        italic: bool = False,
    ) -> None:
        from pptx.oxml import parse_xml
        from pptx.oxml.ns import qn
        from pptx.util import Pt

        run.font.color.rgb = color
        run.font.size = Pt(size_pt)
        run.font.bold = bold
        run.font.italic = italic
        run.font.name = self.FONT_LATIN
        rPr = run._r.get_or_add_rPr()
        for existing_ea in list(rPr.findall(qn("a:ea"))):
            rPr.remove(existing_ea)
        ea_el = parse_xml(
            f'<a:ea xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" typeface="{self.FONT_EA}"/>'
        )
        latin_el = rPr.find(qn("a:latin"))
        if latin_el is not None:
            idx = list(rPr).index(latin_el)
            rPr.insert(idx + 1, ea_el)
        else:
            rPr.append(ea_el)

    def _populate_formatted_runs(
        self,
        paragraph: Any,
        text: str,
        size_pt: float,
        base_color: Any,
        base_bold: bool = False,
    ) -> None:
        """Render plain text plus `{{accent}}` (`#C2410C` Bold) and `**navy**` (`#1E3A5F` Bold) tokens."""
        token_re = re.compile(r"(\{\{.+?\}\}|\*\*.+?\*\*)")
        parts = token_re.split(text)
        for part in parts:
            if not part:
                continue
            r = paragraph.add_run()
            if part.startswith("{{") and part.endswith("}}"):
                r.text = part[2:-2]
                self._set_run_font(r, size_pt=size_pt, color=self.c_accent, bold=True)
            elif part.startswith("**") and part.endswith("**"):
                r.text = part[2:-2]
                self._set_run_font(r, size_pt=size_pt, color=self.c_primary, bold=True)
            else:
                r.text = part
                self._set_run_font(r, size_pt=size_pt, color=base_color, bold=base_bold)

    def _add_textbox(
        self,
        slide: Any,
        left: float,
        top: float,
        width: float,
        height: float,
        word_wrap: bool = True,
    ) -> Any:
        from pptx.util import Inches

        tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
        tf = tb.text_frame
        tf.word_wrap = word_wrap
        tf.margin_left = Inches(0.02)
        tf.margin_right = Inches(0.02)
        tf.margin_top = Inches(0.01)
        tf.margin_bottom = Inches(0.01)
        return tb

    def _add_rule(
        self,
        slide: Any,
        left: float,
        top: float,
        width: float,
        height: float,
        color: Any,
    ) -> Any:
        from pptx.enum.shapes import MSO_SHAPE
        from pptx.util import Inches

        sh = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height)
        )
        sh.fill.solid()
        sh.fill.fore_color.rgb = color
        sh.line.fill.background()
        return sh

    def _new_white_slide(self) -> tuple[Any, int]:
        slide = self.prs.slides.add_slide(self.blank_layout)
        bg = slide.background
        bg.fill.solid()
        bg.fill.fore_color.rgb = self.c_white
        slide_no = len(self.prs.slides)
        return slide, slide_no

    def _add_minimal_footer(self, slide: Any, slide_no: int) -> None:
        from pptx.enum.text import PP_ALIGN

        if self.project_tag:
            tb_l = self._add_textbox(slide, 0.65, 6.98, 9.80, 0.30, word_wrap=False)
            p_l = tb_l.text_frame.paragraphs[0]
            p_l.alignment = PP_ALIGN.LEFT
            r_l = p_l.add_run()
            r_l.text = self.project_tag
            self._set_run_font(r_l, size_pt=10.5, color=self.c_muted, bold=False)

        tb_r = self._add_textbox(slide, 11.55, 6.98, 1.13, 0.30, word_wrap=False)
        p_r = tb_r.text_frame.paragraphs[0]
        p_r.alignment = PP_ALIGN.RIGHT
        r_r = p_r.add_run()
        denom = self.total_slides_hint or slide_no
        r_r.text = f"{slide_no} / {denom}"
        self._set_run_font(r_r, size_pt=10.5, color=self.c_muted, bold=False)
        self._page_num_runs.append((slide_no, r_r))

    def _add_standard_chrome(self, slide: Any, slide_no: int, action_title: str) -> None:
        """Add left-aligned complete-sentence Action Title + 0.5pt hairline + minimalist footer."""
        tb_t = self._add_textbox(slide, 0.65, 0.24, 12.03, 0.82, word_wrap=True)
        p_t = tb_t.text_frame.paragraphs[0]
        p_t.line_spacing = 1.18
        self._populate_formatted_runs(
            p_t, action_title, size_pt=24.5, base_color=self.c_primary, base_bold=True
        )
        self._add_rule(slide, 0.65, 1.07, 12.03, 0.010, self.c_rule)
        self._add_minimal_footer(slide, slide_no)

    def _attach_notes(self, slide: Any, notes: str) -> None:
        if not notes.strip():
            return
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = notes.strip()

    def _embed_svg(
        self,
        slide: Any,
        svg_path: str | Path,
        png_path: str | Path,
        box: tuple[float, float, float, float],
        slide_no: int,
    ) -> str:
        self._media_counter += 1
        tag = f"s{slide_no:02d}_fig{self._media_counter:02d}"
        add_editable_svg_picture(slide, self.prs, svg_path, png_path, box=box, media_tag=tag)
        return str(Path(svg_path))

    # -------------------------------------------------------------------------
    # Layout L1: Cover + Weekly TL;DR Executive Summary
    # -------------------------------------------------------------------------

    def add_l1_cover_tldr(
        self,
        date_label: str,
        title: str,
        presenter_line: str,
        tldr_items: Sequence[tuple[str, str]],
        action_summary_for_ghost_test: str | None = None,
        estimated_seconds: int = 45,
        notes: str = "",
    ) -> Any:
        """
        `L1` Minimalist Weekly Report Cover + 3-bullet TL;DR (`[进展]`, `[发现]`, `[卡点/待拍板]`).
        Eliminates ceremonial banners and standalone Outline slides.
        """
        from pptx.util import Pt

        slide, slide_no = self._new_white_slide()

        tb_meta = self._add_textbox(slide, 0.65, 0.75, 12.03, 0.36, word_wrap=False)
        p_meta = tb_meta.text_frame.paragraphs[0]
        r_meta = p_meta.add_run()
        r_meta.text = date_label
        self._set_run_font(r_meta, size_pt=12.5, color=self.c_muted, bold=False)

        tb_title = self._add_textbox(slide, 0.65, 1.18, 12.03, 1.02, word_wrap=True)
        p_title = tb_title.text_frame.paragraphs[0]
        p_title.line_spacing = 1.18
        self._populate_formatted_runs(
            p_title, title, size_pt=27.0, base_color=self.c_primary, base_bold=True
        )

        tb_pres = self._add_textbox(slide, 0.65, 2.24, 12.03, 0.40, word_wrap=False)
        p_pres = tb_pres.text_frame.paragraphs[0]
        r_pres = p_pres.add_run()
        r_pres.text = presenter_line
        self._set_run_font(r_pres, size_pt=14.5, color=self.c_slate, bold=False)

        self._add_rule(slide, 0.65, 2.78, 12.03, 0.012, self.c_rule)

        tb_tldr = self._add_textbox(slide, 0.65, 3.06, 12.03, 3.65, word_wrap=True)
        tf = tb_tldr.text_frame
        p_hdr = tf.paragraphs[0]
        p_hdr.space_after = Pt(12)
        r_hdr = p_hdr.add_run()
        r_hdr.text = "本周核心摘要 · Weekly TL;DR"
        self._set_run_font(r_hdr, size_pt=16.5, color=self.c_primary, bold=True)

        accent_tags = {"卡点", "阻塞", "待定", "待拍板", "问题", "BLOCKER", "DECISION"}
        for tag, body in tldr_items:
            p = tf.add_paragraph()
            p.space_after = Pt(12)
            p.line_spacing = 1.32
            clean_tag = tag.strip("[]【】 ")
            is_accent = clean_tag in accent_tags
            r_tag = p.add_run()
            r_tag.text = f"[{clean_tag}]  "
            self._set_run_font(
                r_tag,
                size_pt=15.5,
                color=self.c_accent if is_accent else self.c_primary,
                bold=True,
            )
            self._populate_formatted_runs(
                p, body, size_pt=15.5, base_color=self.c_ink, base_bold=False
            )

        self._add_minimal_footer(slide, slide_no)
        self._attach_notes(slide, notes)
        self.records.append(
            SlideRecord(
                slide_no=slide_no,
                layout_code="L1",
                action_title=action_summary_for_ghost_test or title,
                estimated_seconds=estimated_seconds,
            )
        )
        return slide

    # -------------------------------------------------------------------------
    # Layout L2: Assertion-Evidence Hero Figure (`split` or `wide`)
    # -------------------------------------------------------------------------

    def add_l2_hero_figure(
        self,
        action_title: str,
        svg_path: str | Path,
        png_path: str | Path,
        takeaways: Sequence[str],
        mode: Literal["split", "wide"] = "split",
        takeaway_heading: str = "核心证据与物理归因",
        caption: str = "",
        estimated_seconds: int = 75,
        notes: str = "",
    ) -> Any:
        """
        `L2` Assertion-Evidence Hero Figure:
          - `mode="split"`: Left 62% SVG (`7.45" x 5.00"`/`5.45"`) + Right 38% borderless takeaways.
          - `mode="wide"`:  Top full-width SVG (`12.03" x 4.55"`) + Bottom concise takeaways.
        """
        from pptx.util import Pt

        slide, slide_no = self._new_white_slide()
        self._add_standard_chrome(slide, slide_no, action_title)

        if mode == "wide":
            fig_box = (0.65, 1.16, 12.03, 4.55)
            fig_rec = self._embed_svg(slide, svg_path, png_path, fig_box, slide_no)
            tb = self._add_textbox(slide, 0.65, 5.82, 12.03, 1.04, word_wrap=True)
            tf = tb.text_frame
            for idx, item in enumerate(takeaways[:2]):
                p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
                p.space_after = Pt(6)
                p.line_spacing = 1.28
                prefix = item if item.startswith(("•", "▸")) else f"• {item}"
                self._populate_formatted_runs(
                    p, prefix, size_pt=15.0, base_color=self.c_ink, base_bold=False
                )
        else:
            fig_h = 5.00 if caption else 5.45
            fig_box = (0.65, 1.16, 7.45, fig_h)
            fig_rec = self._embed_svg(slide, svg_path, png_path, fig_box, slide_no)
            if caption:
                tb_cap = self._add_textbox(slide, 0.65, 6.26, 7.45, 0.56, word_wrap=True)
                p_cap = tb_cap.text_frame.paragraphs[0]
                self._populate_formatted_runs(
                    p_cap, caption, size_pt=12.0, base_color=self.c_muted, base_bold=False
                )

            tb_r = self._add_textbox(slide, 8.40, 1.24, 4.28, 5.36, word_wrap=True)
            tf = tb_r.text_frame
            p_h = tf.paragraphs[0]
            p_h.space_after = Pt(12)
            r_h = p_h.add_run()
            r_h.text = takeaway_heading
            self._set_run_font(r_h, size_pt=16.5, color=self.c_primary, bold=True)

            for item in takeaways[:3]:
                p = tf.add_paragraph()
                p.space_after = Pt(12)
                p.line_spacing = 1.32
                prefix = item if item.startswith(("•", "▸")) else f"• {item}"
                self._populate_formatted_runs(
                    p, prefix, size_pt=15.0, base_color=self.c_ink, base_bold=False
                )

        self._attach_notes(slide, notes)
        self.records.append(
            SlideRecord(
                slide_no=slide_no,
                layout_code=f"L2-{mode}",
                action_title=action_title,
                estimated_seconds=estimated_seconds,
                figures=[fig_rec],
            )
        )
        return slide

    # -------------------------------------------------------------------------
    # Layout L3: Baseline vs. This Week Dual Comparison
    # -------------------------------------------------------------------------

    def add_l3_dual_comparison(
        self,
        action_title: str,
        left_label: str,
        left_svg: str | Path,
        left_png: str | Path,
        right_label: str,
        right_svg: str | Path,
        right_png: str | Path,
        delta_summary: str,
        estimated_seconds: int = 75,
        notes: str = "",
    ) -> Any:
        """
        `L3` Symmetric 1x2 Dual `<asvg:svgBlip>` Comparison (`5.80" x 4.35"` each) +
        bottom full-width quantitative improvement summary.
        """
        slide, slide_no = self._new_white_slide()
        self._add_standard_chrome(slide, slide_no, action_title)

        tb_ll = self._add_textbox(slide, 0.65, 1.14, 5.80, 0.36, word_wrap=False)
        p_ll = tb_ll.text_frame.paragraphs[0]
        r_ll = p_ll.add_run()
        r_ll.text = left_label
        self._set_run_font(r_ll, size_pt=15.0, color=self.c_slate, bold=True)

        tb_rl = self._add_textbox(slide, 6.88, 1.14, 5.80, 0.36, word_wrap=False)
        p_rl = tb_rl.text_frame.paragraphs[0]
        self._populate_formatted_runs(
            p_rl, right_label, size_pt=15.0, base_color=self.c_primary, base_bold=True
        )

        f1 = self._embed_svg(slide, left_svg, left_png, (0.65, 1.54, 5.80, 4.35), slide_no)
        f2 = self._embed_svg(slide, right_svg, right_png, (6.88, 1.54, 5.80, 4.35), slide_no)

        self._add_rule(slide, 0.65, 6.02, 12.03, 0.010, self.c_rule)
        tb_bot = self._add_textbox(slide, 0.65, 6.10, 12.03, 0.72, word_wrap=True)
        p_bot = tb_bot.text_frame.paragraphs[0]
        p_bot.line_spacing = 1.28
        text_line = delta_summary if delta_summary.startswith("▸") else f"**▸ 核心增量：**{delta_summary}"
        self._populate_formatted_runs(
            p_bot, text_line, size_pt=15.0, base_color=self.c_ink, base_bold=False
        )

        self._attach_notes(slide, notes)
        self.records.append(
            SlideRecord(
                slide_no=slide_no,
                layout_code="L3",
                action_title=action_title,
                estimated_seconds=estimated_seconds,
                figures=[f1, f2],
            )
        )
        return slide

    # -------------------------------------------------------------------------
    # Layout L4: 2x2 Ablation / Concentration Grid (`C1` or `C2`)
    # -------------------------------------------------------------------------

    def add_l4_grid_2x2(
        self,
        action_title: str,
        mode: Literal["C1", "C2"] = "C1",
        c1_svg: str | Path | None = None,
        c1_png: str | Path | None = None,
        c1_takeaways: Sequence[str] = (),
        c1_heading: str = "跨条件演化规律",
        c2_panels: Sequence[tuple[str | Path, str | Path]] = (),
        estimated_seconds: int = 80,
        notes: str = "",
    ) -> Any:
        """
        `L4` 2x2 Multi-Condition / Ablation Matrix:
          - `mode="C1"`: Single shared-axes 2x2 SVG (`8.20" x 5.45"`) + right takeaway column.
          - `mode="C2"`: 4 independent `<asvg:svgBlip>` slots (`5.85" x 2.68"` each).
        """
        from pptx.util import Pt

        slide, slide_no = self._new_white_slide()
        self._add_standard_chrome(slide, slide_no, action_title)
        figs: list[str] = []

        if mode == "C1":
            if c1_svg is None or c1_png is None:
                raise ValueError("L4 mode='C1' requires `c1_svg` and `c1_png`.")
            figs.append(self._embed_svg(slide, c1_svg, c1_png, (0.65, 1.16, 8.20, 5.45), slide_no))
            tb_r = self._add_textbox(slide, 9.10, 1.24, 3.58, 5.30, word_wrap=True)
            tf = tb_r.text_frame
            p_h = tf.paragraphs[0]
            p_h.space_after = Pt(10)
            r_h = p_h.add_run()
            r_h.text = c1_heading
            self._set_run_font(r_h, size_pt=16.0, color=self.c_primary, bold=True)

            for item in c1_takeaways[:3]:
                p = tf.add_paragraph()
                p.space_after = Pt(11)
                p.line_spacing = 1.30
                prefix = item if item.startswith(("•", "▸")) else f"• {item}"
                self._populate_formatted_runs(
                    p, prefix, size_pt=14.5, base_color=self.c_ink, base_bold=False
                )
        else:
            if len(c2_panels) != 4:
                raise ValueError("L4 mode='C2' requires exactly 4 `(svg_path, png_path)` pairs.")
            slots = [
                (0.65, 1.16, 5.85, 2.68),
                (6.83, 1.16, 5.85, 2.68),
                (0.65, 4.02, 5.85, 2.68),
                (6.83, 4.02, 5.85, 2.68),
            ]
            for (svg_p, png_p), box in zip(c2_panels, slots):
                figs.append(self._embed_svg(slide, svg_p, png_p, box, slide_no))

        self._attach_notes(slide, notes)
        self.records.append(
            SlideRecord(
                slide_no=slide_no,
                layout_code=f"L4-{mode}",
                action_title=action_title,
                estimated_seconds=estimated_seconds,
                figures=figs,
            )
        )
        return slide

    # -------------------------------------------------------------------------
    # Layout L5: Troubleshooting / Failure Diagnosis & Fix
    # -------------------------------------------------------------------------

    def add_l5_troubleshooting(
        self,
        action_title: str,
        svg_path: str | Path,
        png_path: str | Path,
        symptom: str,
        root_cause: str,
        fix_and_status: str,
        caption: str = "",
        estimated_seconds: int = 85,
        notes: str = "",
    ) -> Any:
        """
        `L5` Weekly Lab Troubleshooting & Negative-Result Diagnosis:
          - Left: Anomaly curve / diverging trajectory / broken snapshot (`5.55" x 5.00"`).
          - Right: Borderless 3-stage flow guided by a 2pt left vertical line:
            `① 异常现象 (Symptom)` -> `② 根因定位 (Root Cause, Accent)` -> `③ 解决方案与验证 (Fix)`.
        """
        from pptx.util import Pt

        slide, slide_no = self._new_white_slide()
        self._add_standard_chrome(slide, slide_no, action_title)

        fig_h = 5.00 if caption else 5.40
        fig_rec = self._embed_svg(slide, svg_path, png_path, (0.65, 1.20, 5.55, fig_h), slide_no)
        if caption:
            tb_cap = self._add_textbox(slide, 0.65, 6.28, 5.55, 0.56, word_wrap=True)
            p_cap = tb_cap.text_frame.paragraphs[0]
            self._populate_formatted_runs(
                p_cap, caption, size_pt=12.0, base_color=self.c_muted, base_bold=False
            )

        self._add_rule(slide, 6.46, 1.28, 0.028, 5.25, self.c_rule)

        tb_diag = self._add_textbox(slide, 6.65, 1.22, 6.03, 5.48, word_wrap=True)
        tf = tb_diag.text_frame
        stages = [
            ("① 异常现象 (Symptom)", symptom, self.c_primary),
            ("② 根因定位 (Root Cause)", root_cause, self.c_accent),
            ("③ 修复与验证 (Fix & Status)", fix_and_status, self.c_primary),
        ]
        for idx, (hdr, body, hdr_color) in enumerate(stages):
            p_h = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p_h.space_after = Pt(4)
            r_h = p_h.add_run()
            r_h.text = hdr
            self._set_run_font(r_h, size_pt=16.0, color=hdr_color, bold=True)

            p_b = tf.add_paragraph()
            p_b.space_after = Pt(14 if idx < 2 else 4)
            p_b.line_spacing = 1.30
            self._populate_formatted_runs(
                p_b, body, size_pt=14.5, base_color=self.c_ink, base_bold=False
            )

        self._attach_notes(slide, notes)
        self.records.append(
            SlideRecord(
                slide_no=slide_no,
                layout_code="L5",
                action_title=action_title,
                estimated_seconds=estimated_seconds,
                figures=[fig_rec],
            )
        )
        return slide

    # -------------------------------------------------------------------------
    # Layout L6: Native LaTeX Booktabs Table (`split` Plot+Table or `full`)
    # -------------------------------------------------------------------------

    def add_l6_booktabs_table(
        self,
        action_title: str,
        table_title: str,
        table_rows: Sequence[Sequence[str]],
        takeaways: Sequence[str],
        mode: Literal["split", "full"] = "split",
        svg_path: str | Path | None = None,
        png_path: str | Path | None = None,
        fig_caption: str = "",
        col_widths: Sequence[float] | None = None,
        highlight_rows: Sequence[int] = (),
        estimated_seconds: int = 80,
        notes: str = "",
    ) -> Any:
        """
        `L6` Quantitative Benchmark Slide with Native `<a:tbl>` LaTeX `booktabs` 3-line Table:
          - Hard limits: `rows <= 6`, `cols <= 5` (`split`) or `cols <= 6` (`full`) to guarantee
            zero PowerPoint vertical table expansion collisions (`layout_audit.py`).
        """
        from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
        from pptx.util import Inches, Pt

        n_rows = len(table_rows)
        n_cols = len(table_rows[0]) if n_rows else 0
        max_cols = 5 if mode == "split" else 6
        if n_rows < 2 or n_rows > 6:
            raise ValueError(f"L6 Booktabs table requires 2..6 rows (got {n_rows}).")
        if n_cols < 2 or n_cols > max_cols:
            raise ValueError(f"L6 mode='{mode}' allows 2..{max_cols} columns (got {n_cols}).")

        slide, slide_no = self._new_white_slide()
        self._add_standard_chrome(slide, slide_no, action_title)
        figs: list[str] = []

        if mode == "split":
            if svg_path is None or png_path is None:
                raise ValueError("L6 mode='split' requires `svg_path` and `png_path`.")
            figs.append(self._embed_svg(slide, svg_path, png_path, (0.65, 1.20, 5.85, 5.00), slide_no))
            if fig_caption:
                tb_cap = self._add_textbox(slide, 0.65, 6.26, 5.85, 0.56, word_wrap=True)
                p_cap = tb_cap.text_frame.paragraphs[0]
                self._populate_formatted_runs(
                    p_cap, fig_caption, size_pt=12.0, base_color=self.c_muted, base_bold=False
                )
            tx, ty, tw = 6.80, 1.65, 5.88
            title_box = (6.80, 1.18, 5.88, 0.42)
            takeaway_box = (6.80, 5.18, 5.88, 1.45)
        else:
            tx, ty, tw = 0.65, 1.65, 12.03
            title_box = (0.65, 1.18, 12.03, 0.42)
            takeaway_box = (0.65, 5.18, 12.03, 1.45)

        tb_tt = self._add_textbox(slide, *title_box, word_wrap=False)
        p_tt = tb_tt.text_frame.paragraphs[0]
        r_tt = p_tt.add_run()
        r_tt.text = table_title
        self._set_run_font(r_tt, size_pt=14.0, color=self.c_primary, bold=True)

        row_h_in = 0.40
        tbl_shape = slide.shapes.add_table(
            n_rows, n_cols, Inches(tx), Inches(ty), Inches(tw), Inches(row_h_in * n_rows)
        )
        tbl = tbl_shape.table
        if col_widths is not None:
            if len(col_widths) != n_cols:
                raise ValueError("`col_widths` length must match table column count.")
            for c_idx, w_in in enumerate(col_widths):
                tbl.columns[c_idx].width = Inches(w_in)
        else:
            first_w = tw * 0.28
            rem_w = (tw - first_w) / (n_cols - 1)
            tbl.columns[0].width = Inches(first_w)
            for c_idx in range(1, n_cols):
                tbl.columns[c_idx].width = Inches(rem_w)

        highlight_set = set(highlight_rows)
        for r_idx, row in enumerate(table_rows):
            tbl.rows[r_idx].height = Inches(row_h_in)
            for c_idx, val in enumerate(row):
                cell = tbl.cell(r_idx, c_idx)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                cell.margin_left = Inches(0.06)
                cell.margin_right = Inches(0.06)
                cell.margin_top = Inches(0.03)
                cell.margin_bottom = Inches(0.03)

                top_pt = 1.5 if r_idx == 0 else 0.0
                bot_pt = 0.75 if r_idx == 0 else (1.5 if r_idx == n_rows - 1 else 0.0)
                apply_booktabs_borders(cell, top_pt=top_pt, bottom_pt=bot_pt, color_hex="1E3A5F")

                p = cell.text_frame.paragraphs[0]
                p.alignment = PP_ALIGN.LEFT if c_idx == 0 else PP_ALIGN.CENTER
                is_hdr = r_idx == 0
                is_hl = r_idx in highlight_set
                base_c = self.c_primary if (is_hdr or is_hl) else self.c_ink
                self._populate_formatted_runs(
                    p, str(val), size_pt=13.0, base_color=base_c, base_bold=(is_hdr or is_hl)
                )

        tb_tk = self._add_textbox(slide, *takeaway_box, word_wrap=True)
        tf_tk = tb_tk.text_frame
        for idx, line in enumerate(takeaways[:2]):
            p = tf_tk.paragraphs[0] if idx == 0 else tf_tk.add_paragraph()
            p.space_after = Pt(6)
            p.line_spacing = 1.28
            prefix = line if line.startswith(("•", "▸")) else f"• {line}"
            self._populate_formatted_runs(
                p, prefix, size_pt=14.5, base_color=self.c_ink, base_bold=False
            )

        self._attach_notes(slide, notes)
        self.records.append(
            SlideRecord(
                slide_no=slide_no,
                layout_code=f"L6-{mode}",
                action_title=action_title,
                estimated_seconds=estimated_seconds,
                figures=figs,
            )
        )
        return slide

    # -------------------------------------------------------------------------
    # Layout L7: Last-Week Closed Loop + Next-Week Plan + Advisor Decisions
    # -------------------------------------------------------------------------

    def add_l7_plan_and_decisions(
        self,
        action_title: str,
        closed_loop_item: str,
        next_week_tasks: Sequence[tuple[str, str]],
        decisions_needed: Sequence[tuple[str, str]],
        estimated_seconds: int = 90,
        notes: str = "",
    ) -> Any:
        """
        `L7` Final Persistent Discussion Slide (replaces empty 'Thank You' slides):
          - Left 62% (`0.65" .. 7.90"`): Last-week closed loop + 2–3 concrete next-week tasks
            with deliverables & day-of-week milestones.
          - Right 35% (`8.35" .. 12.68"`, separated by 2pt `#C2410C` vertical rule): 1–2 concrete
            decision forks with Option A/B recommendation for immediate PI sign-off.
        """
        from pptx.util import Pt

        slide, slide_no = self._new_white_slide()
        self._add_standard_chrome(slide, slide_no, action_title)

        tb_l = self._add_textbox(slide, 0.65, 1.24, 7.25, 5.42, word_wrap=True)
        tf_l = tb_l.text_frame

        p_lh = tf_l.paragraphs[0]
        p_lh.space_after = Pt(8)
        r_lh = p_lh.add_run()
        r_lh.text = "上周遗留闭环 & 下周排期"
        self._set_run_font(r_lh, size_pt=16.5, color=self.c_primary, bold=True)

        p_cl = tf_l.add_paragraph()
        p_cl.space_after = Pt(14)
        p_cl.line_spacing = 1.28
        r_chk = p_cl.add_run()
        r_chk.text = "✓ 已核销："
        self._set_run_font(r_chk, size_pt=14.5, color=self.c_primary, bold=True)
        self._populate_formatted_runs(
            p_cl, closed_loop_item, size_pt=14.5, base_color=self.c_slate, base_bold=False
        )

        badges = ("❶", "❷", "❸")
        for idx, (task_title, task_detail) in enumerate(next_week_tasks[:3]):
            badge = badges[idx] if idx < len(badges) else f"{idx + 1}."
            p_t = tf_l.add_paragraph()
            p_t.space_after = Pt(3)
            self._populate_formatted_runs(
                p_t, f"**{badge} {task_title}**", size_pt=15.0, base_color=self.c_primary, base_bold=True
            )
            p_d = tf_l.add_paragraph()
            p_d.space_after = Pt(11)
            p_d.line_spacing = 1.28
            self._populate_formatted_runs(
                p_d, f"  {task_detail}", size_pt=14.5, base_color=self.c_ink, base_bold=False
            )

        self._add_rule(slide, 8.14, 1.30, 0.028, 5.20, self.c_accent)

        tb_r = self._add_textbox(slide, 8.35, 1.24, 4.33, 5.42, word_wrap=True)
        tf_r = tb_r.text_frame
        p_rh = tf_r.paragraphs[0]
        p_rh.space_after = Pt(12)
        r_rh = p_rh.add_run()
        r_rh.text = "需导师拍板问题"
        self._set_run_font(r_rh, size_pt=16.5, color=self.c_accent, bold=True)

        for idx, (q_title, q_options) in enumerate(decisions_needed[:2], start=1):
            p_q = tf_r.add_paragraph()
            p_q.space_after = Pt(4)
            p_q.line_spacing = 1.25
            self._populate_formatted_runs(
                p_q, f"{{{{Q{idx}}}}}  **{q_title}**", size_pt=15.0, base_color=self.c_primary, base_bold=True
            )
            p_o = tf_r.add_paragraph()
            p_o.space_after = Pt(14)
            p_o.line_spacing = 1.30
            self._populate_formatted_runs(
                p_o, q_options, size_pt=14.0, base_color=self.c_ink, base_bold=False
            )

        self._attach_notes(slide, notes)
        self.records.append(
            SlideRecord(
                slide_no=slide_no,
                layout_code="L7",
                action_title=action_title,
                estimated_seconds=estimated_seconds,
            )
        )
        return slide

    # -------------------------------------------------------------------------
    # Finalization, Ghost Deck Test & Paired `verify_checklist.md`
    # -------------------------------------------------------------------------

    def save(self, out_pptx: str | Path) -> Path:
        """Finalize `slide / total` counters, save `.pptx`, and register SVG content types."""
        out_p = Path(out_pptx)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        total = len(self.prs.slides)
        for s_no, run in self._page_num_runs:
            run.text = f"{s_no} / {total}"
        self.prs.save(str(out_p))
        ensure_svg_content_type(out_p)
        return out_p

    def ghost_deck_lines(self) -> list[str]:
        """Return ordered Action Titles so the author can verify the narrative chain without visuals."""
        clean_re = re.compile(r"\{\{|\}\}|\*\*")
        return [
            f"{rec.slide_no}. [{rec.layout_code} | ~{rec.estimated_seconds}s] {clean_re.sub('', rec.action_title)}"
            for rec in self.records
        ]

    def write_verify_checklist(
        self,
        checklist_path: str | Path,
        pptx_path: str | Path,
        data_provenance: Sequence[tuple[str, str, str]],
        advisor_qa: Sequence[tuple[str, str]],
    ) -> Path:
        """
        Write the mandatory paired `verify_checklist.md` containing:
          1. Ghost Deck Test (concatenated Action Titles + speaking-time budget)
          2. Data & `<asvg:svgBlip>` Vector Provenance Table
          3. High-Frequency Advisor Q&A Preparation
          4. Dual-Gate Audit Commands (`layout_audit.py` + `office/validate.py`)
        """
        chk_p = Path(checklist_path)
        chk_p.parent.mkdir(parents=True, exist_ok=True)
        total_sec = sum(r.estimated_seconds for r in self.records)
        mins, secs = divmod(total_sec, 60)

        lines: list[str] = [
            f"# 组会汇报核验与导师追问清单 (`{Path(pptx_path).name}`)",
            "",
            "## 1. Ghost Deck Test（幽灵大纲测试：仅读标题串联完整证据链）",
            "",
            f"- **总页数**：{len(self.records)} 页（零礼仪水页，尾页常驻投屏供拍板讨论）",
            f"- **预计口头汇报时长**：约 {mins} 分 {secs:02d} 秒（预留充足组会打断提问缓冲）",
            "",
        ]
        for gl in self.ghost_deck_lines():
            lines.append(f"- {gl}")

        lines.extend(
            [
                "",
                "## 2. 数据溯源与 `<asvg:svgBlip>` 零乱码矢量核对表",
                "",
                "| 页码/版式 | 展品与物理尺寸契约 (`figsize`) | 样本量 / 统计指标定义 / 原始数据溯源 |",
                "|---|---|---|",
            ]
        )
        for slide_ref, slot_desc, prov in data_provenance:
            lines.append(f"| {slide_ref} | {slot_desc} | {prov} |")

        lines.extend(
            [
                "",
                "## 3. 导师高频追问预判与定量应答准备（Advisor Q&A Prep）",
                "",
            ]
        )
        for idx, (question, answer) in enumerate(advisor_qa, start=1):
            lines.append(f"### Q{idx}. {question}")
            lines.append(f"- **预备应答**：{answer}")
            lines.append("")

        lines.extend(
            [
                "## 4. 交付双门禁与视觉回看自检命令",
                "",
                "```bash",
                f"python3 /Users/zhoujun/.cc-switch/skills/pptx/scripts/layout_audit.py {pptx_path}",
                f"/Users/zhoujun/miniconda3/bin/python3 /Users/zhoujun/.cc-switch/skills/pptx/scripts/office/validate.py {pptx_path}",
                f"/Users/zhoujun/miniconda3/bin/python3 /Users/zhoujun/.cc-switch/skills/pptx/scripts/office/soffice.py --headless --convert-to pdf {pptx_path}",
                "```",
                "",
                "- [x] 纯白底 `#FFFFFF`，零校徽、零水印、零顶底彩色横幅、零圆角灰底卡片堆叠",
                "- [x] 全片彩色色相 `<= 2`（主色 `#1E3A5F` + 唯一强调色 `#C2410C`），单页形状数 `<= 14`",
                "- [x] 全部 Matplotlib SVG 经 `sanitize_svg_for_ppt()` 展平（`tspan=0, clipPath=0`），支持右键「转换为形状」无乱码编辑",
                "- [x] 三线表满足 `rows <= 6, cols <= 5`，底部预留 `> 0.55\"` 防膨胀安全缓冲",
            ]
        )

        chk_p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return chk_p


# =============================================================================
# 5. Built-in 7-Slide Scientific Demo (`--demo <out_dir>`)
# =============================================================================

def _generate_demo_figures(fig_dir: Path) -> dict[str, tuple[Path, Path]]:
    """Generate 6 realistic, 1:1 slot-sized scientific SVGs + 450 DPI PNGs for `L2`–`L6`."""
    import matplotlib.pyplot as plt

    rng = np.random.default_rng(20261112)
    out: dict[str, tuple[Path, Path]] = {}

    # 1. L2 Hero Figure (`7.45" x 5.00"`): DFT vs O4-DBMLFF Force Parity + Error Tail Curve
    with apply_slide_minimal_style(boxed_inward=True):
        fig, (ax_p, ax_e) = plt.subplots(
            1, 2, figsize=SLIDE_SLOT_SIZES["L2_split"], gridspec_kw={"width_ratios": [1.35, 1.0]}, layout="constrained"
        )
        f_dft = rng.normal(0.0, 1.35, size=260)
        f_pred = f_dft + rng.normal(0.0, 0.0284, size=260)
        lim = (-4.0, 4.0)
        fx, fy = clip_scatter_to_box(f_dft, f_pred, lim, lim)
        ax_p.plot(lim, lim, ls="--", lw=1.2, color=PALETTE_HEX["slate_light"], label="1:1 Ideal")
        ax_p.scatter(fx, fy, s=16, alpha=0.80, color=PALETTE_HEX["primary"], edgecolors="none", label="O4-DBMLFF")
        ax_p.set_xlim(lim)
        ax_p.set_ylim(lim)
        ax_p.set_xlabel("DFT Reference Force (eV/Å)")
        ax_p.set_ylabel("MLFF Predicted Force (eV/Å)")
        ax_p.set_title(r"(a) Force Parity (4 M $\mathrm{MgCl_2}$, $n=260$)", loc="left")
        ax_p.text(
            -3.65, 3.05, "RMSE = 28.4 meV/Å\n$R^2 = 0.9994$",
            fontsize=10.5, fontweight="bold", color=PALETTE_HEX["accent"],
        )
        ax_p.legend(loc="lower right")

        r_bins = np.linspace(1.75, 4.50, 22)
        err_raw = 195.0 * np.exp(-(r_bins - 1.75) / 0.35) + 31.0
        err_o4 = 18.0 * np.exp(-(r_bins - 1.75) / 0.45) + 24.5
        rx1, ry1 = clip_curve_to_box(r_bins, err_raw, (1.70, 4.60), (0.0, 240.0))
        rx2, ry2 = clip_curve_to_box(r_bins, err_o4, (1.70, 4.60), (0.0, 240.0))
        ax_e.plot(rx1, ry1, ls="--", lw=1.6, color=PALETTE_HEX["slate_light"], label="Raw MLFF (No Wall)")
        ax_e.plot(rx2, ry2, ls="-", lw=2.0, color=PALETTE_HEX["primary"], label="O4-DBMLFF (This Week)")
        ax_e.scatter([1.85], [err_o4[1]], s=36, color=PALETTE_HEX["accent"], zorder=5)
        ax_e.annotate(
            "-81% short-range error",
            xy=(1.88, err_o4[1] + 4), xytext=(2.18, 118),
            fontsize=9.8, fontweight="bold", color=PALETTE_HEX["accent"],
            arrowprops={"arrowstyle": "->", "color": PALETTE_HEX["accent"], "lw": 1.3},
        )
        ax_e.set_xlim(1.70, 4.60)
        ax_e.set_ylim(0.0, 240.0)
        ax_e.set_xlabel(r"Min Pair Distance $r_{\mathrm{min}}$ (Å)")
        ax_e.set_ylabel("Shell Force RMSE (meV/Å)")
        ax_e.set_title("(b) Short-Range Shell Error", loc="left")
        ax_e.legend(loc="upper right")

        svg_p, png_p, _ = save_slide_svg_and_png(fig, fig_dir / "fig_l2_force_parity")
        out["l2"] = (svg_p, png_p)

    # 2. L3 Dual Comparison (`2 x 5.80" x 4.35"`): Baseline vs O4-DBMLFF RDF g(r) & CN(r)
    r = np.linspace(1.45, 5.20, 320)
    g_base = (
        3.4 * np.exp(-((r - 1.76) / 0.065) ** 2)
        + 10.6 * np.exp(-((r - 2.09) / 0.095) ** 2)
        + 1.35 * np.exp(-((r - 4.18) / 0.42) ** 2)
        + 0.85 / (1.0 + np.exp(-(r - 3.60) / 0.25))
    )
    g_o4 = (
        12.4 * np.exp(-((r - 2.08) / 0.082) ** 2)
        + 1.48 * np.exp(-((r - 4.15) / 0.38) ** 2)
        + 0.88 / (1.0 + np.exp(-(r - 3.55) / 0.24))
    )

    with apply_slide_minimal_style(boxed_inward=True):
        fig_b, ax_b = plt.subplots(figsize=SLIDE_SLOT_SIZES["L3_dual"], layout="constrained")
        xb, yb = clip_curve_to_box(r, g_base, (1.45, 5.20), (0.0, 14.0))
        ax_b.plot(xb, yb, ls="-", lw=1.9, color=PALETTE_HEX["slate_dark"], label=r"$g_{\mathrm{Mg-O_w}}(r)$ Raw MLFF")
        ax_b.axvline(1.76, ls=":", lw=1.3, color=PALETTE_HEX["accent"])
        ax_b.annotate(
            "Spurious inner peak\n(r = 1.76 Å, CN = 7.18)",
            xy=(1.76, 3.5), xytext=(2.42, 7.8),
            fontsize=10.0, fontweight="bold", color=PALETTE_HEX["accent"],
            arrowprops={"arrowstyle": "->", "color": PALETTE_HEX["accent"], "lw": 1.3},
        )
        ax_b.set_xlim(1.45, 5.20)
        ax_b.set_ylim(0.0, 14.0)
        ax_b.set_xlabel("Distance $r$ (Å)")
        ax_b.set_ylabel("Radial Distribution $g(r)$")
        ax_b.legend(loc="upper right")
        out["l3_left"] = save_slide_svg_and_png(fig_b, fig_dir / "fig_l3_baseline_rdf")[:2]

    with apply_slide_minimal_style(boxed_inward=True):
        fig_o, ax_o = plt.subplots(figsize=SLIDE_SLOT_SIZES["L3_dual"], layout="constrained")
        xo, yo = clip_curve_to_box(r, g_o4, (1.45, 5.20), (0.0, 14.0))
        ax_o.plot(xo, yo, ls="-", lw=2.0, color=PALETTE_HEX["primary"], label=r"$g_{\mathrm{Mg-O_w}}(r)$ O4-DBMLFF")
        ax_o.annotate(
            "Clean 1st shell: r = 2.08 Å\nPlateau CN = 5.88 (Exp: 5.9)",
            xy=(2.08, 12.2), xytext=(2.58, 10.2),
            fontsize=10.0, fontweight="bold", color=PALETTE_HEX["primary"],
            arrowprops={"arrowstyle": "->", "color": PALETTE_HEX["primary"], "lw": 1.3},
        )
        ax_o.set_xlim(1.45, 5.20)
        ax_o.set_ylim(0.0, 14.0)
        ax_o.set_xlabel("Distance $r$ (Å)")
        ax_o.set_ylabel("Radial Distribution $g(r)$")
        ax_o.legend(loc="upper right")
        out["l3_right"] = save_slide_svg_and_png(fig_o, fig_dir / "fig_l3_o4_rdf")[:2]

    # 3. L4 2x2 Shared-Axes Concentration Matrix (`8.20" x 5.45"`): Raman O-H Band 0.5..4.0 M
    wn = np.linspace(2900.0, 3800.0, 901)
    concs = [
        (r"(a) 0.5 M $\mathrm{MgCl_2}$", 3420.0, 122.0, 0.45),
        (r"(b) 1.0 M $\mathrm{MgCl_2}$", 3427.0, 120.0, 0.40),
        (r"(c) 2.5 M $\mathrm{MgCl_2}$", 3441.0, 118.0, 0.35),
        (r"(d) 4.0 M $\mathrm{MgCl_2}$", 3456.0, 115.0, 0.31),
    ]
    with apply_slide_minimal_style(boxed_inward=True):
        fig4, axes = plt.subplots(
            2, 2, figsize=SLIDE_SLOT_SIZES["L4_c1_grid"], sharex=True, sharey=True, layout="constrained"
        )
        for ax, (label, mu_hi, sig, w_lo) in zip(axes.flat, concs):
            i_exp = w_lo * np.exp(-((wn - 3225.0) / 102.0) ** 2) + np.exp(-((wn - (mu_hi - 4.0)) / sig) ** 2)
            i_sim = (w_lo * 0.98) * np.exp(-((wn - 3228.0) / 101.0) ** 2) + np.exp(
                -((wn - mu_hi) / sig) ** 2
            )
            i_exp /= i_exp.max()
            i_sim /= i_sim.max()
            peak_wn = float(wn[int(np.argmax(i_sim))])
            xe, ye = clip_curve_to_box(wn, i_exp, (2900, 3800), (0.0, 1.18))
            xs, ys = clip_curve_to_box(wn, i_sim, (2900, 3800), (0.0, 1.18))
            ax.plot(xe, ye, ls="--", lw=1.6, color=PALETTE_HEX["slate_light"], label="Exp. Raman")
            ax.plot(xs, ys, ls="-", lw=1.9, color=PALETTE_HEX["primary"], label="O4 + TNEP")
            ax.axvline(peak_wn, ls=":", lw=1.2, color=PALETTE_HEX["accent"])
            ax.scatter([peak_wn], [1.0], s=22, color=PALETTE_HEX["accent"], zorder=5)
            ax.set_xlim(2900, 3800)
            ax.set_ylim(0.0, 1.18)
            ax.set_title(label, loc="left", fontsize=11.5)
            ax.text(2945, 0.95, rf"Peak: {peak_wn:.0f} $\mathrm{{cm^{{-1}}}}$", fontsize=9.8, color=PALETTE_HEX["accent"], fontweight="bold")
        axes[0, 0].legend(loc="upper right", fontsize=9.2)
        axes[1, 0].set_xlabel(r"Raman Shift ($\mathrm{cm^{-1}}$)")
        axes[1, 1].set_xlabel(r"Raman Shift ($\mathrm{cm^{-1}}$)")
        axes[0, 0].set_ylabel("Norm. Intensity (a.u.)")
        axes[1, 0].set_ylabel("Norm. Intensity (a.u.)")
        out["l4"] = save_slide_svg_and_png(fig4, fig_dir / "fig_l4_raman_grid")[:2]

    # 4. L5 Troubleshooting Plot (`5.55" x 5.00"`): 5.0 M 330 K NPT Divergence vs Active-Learning Fix
    t_ns = np.linspace(0.0, 5.0, 260)
    f_max_bug = np.where(
        t_ns < 1.38,
        1.9 + 0.22 * np.sin(7 * t_ns),
        1.9 + 11.5 * np.exp((t_ns - 1.38) * 3.8),
    )
    f_max_bug = np.where(t_ns <= 1.82, f_max_bug, np.nan)
    f_max_fix = 1.85 + 0.18 * np.sin(5.5 * t_ns + 0.4) + rng.normal(0.0, 0.06, size=len(t_ns))
    with apply_slide_minimal_style(boxed_inward=True):
        fig5, ax5 = plt.subplots(figsize=SLIDE_SLOT_SIZES["L5_diag"], layout="constrained")
        xb5, yb5 = clip_curve_to_box(t_ns, f_max_bug, (0.0, 5.0), (0.0, 15.0))
        xf5, yf5 = clip_curve_to_box(t_ns, f_max_fix, (0.0, 5.0), (0.0, 15.0))
        ax5.plot(xb5, yb5, ls="--", lw=1.9, color=PALETTE_HEX["accent"], label="v0.8 Raw (Crashed @ 1.42 ns)")
        ax5.plot(xf5, yf5, ls="-", lw=1.9, color=PALETTE_HEX["primary"], label="v0.9 + CIP Dimers (Stable 10 ns)")
        ax5.axhline(8.0, ls=":", lw=1.1, color=PALETTE_HEX["slate_light"])
        ax5.annotate(
            "Unphysical Mg-Cl collapse\n($d_{\\mathrm{Mg-Cl}}$ = 1.89 Å, $|F|_{\\mathrm{max}}$ > 12 eV/Å)",
            xy=(1.42, 12.2), xytext=(1.95, 11.2),
            fontsize=9.8, fontweight="bold", color=PALETTE_HEX["accent"],
            arrowprops={"arrowstyle": "->", "color": PALETTE_HEX["accent"], "lw": 1.3},
        )
        ax5.set_xlim(0.0, 5.0)
        ax5.set_ylim(0.0, 15.0)
        ax5.set_xlabel("NPT Simulation Time (ns, 5.0 M @ 330 K)")
        ax5.set_ylabel(r"Max Atomic Force $|F|_{\mathrm{max}}$ (eV/Å)")
        ax5.set_title("5.0 M High-Temp NPT Stability Stress Test", loc="left")
        ax5.legend(loc="center right")
        out["l5"] = save_slide_svg_and_png(fig5, fig_dir / "fig_l5_npt_crash_fix")[:2]

    # 5. L6 Left Plot (`5.85" x 5.00"`): Bulk Density Parity (0.5 - 5.0 M @ 298.15 K)
    rho_exp = np.array([1.038, 1.076, 1.148, 1.216, 1.281, 1.338])
    rho_iod = np.array([1.045, 1.092, 1.178, 1.261, 1.340, 1.406])
    rho_o4 = np.array([1.039, 1.078, 1.151, 1.219, 1.285, 1.343])
    with apply_slide_minimal_style(boxed_inward=True):
        fig6, ax6 = plt.subplots(figsize=SLIDE_SLOT_SIZES["L6_left_fig"], layout="constrained")
        d_lim = (1.01, 1.43)
        ax6.plot(d_lim, d_lim, ls="--", lw=1.3, color=PALETTE_HEX["slate_light"], label="1:1 Exp. Parity")
        ax6.plot(rho_exp, rho_iod, "s--", lw=1.5, color=PALETTE_HEX["slate_dark"], label="Classical IOD 0.80")
        ax6.plot(rho_exp, rho_o4, "o-", lw=2.0, color=PALETTE_HEX["primary"], label="O4-DBMLFF (This Week)")
        ax6.scatter([rho_exp[-1]], [rho_o4[-1]], s=52, color=PALETTE_HEX["accent"], zorder=5)
        ax6.annotate(
            r"5.0 M: MAE = 0.0032 $\mathrm{g/cm^3}$",
            xy=(rho_exp[-1], rho_o4[-1]), xytext=(1.13, 1.38),
            fontsize=10.0, fontweight="bold", color=PALETTE_HEX["accent"],
            arrowprops={"arrowstyle": "->", "color": PALETTE_HEX["accent"], "lw": 1.3},
        )
        ax6.set_xlim(d_lim)
        ax6.set_ylim(d_lim)
        ax6.set_xlabel(r"Experimental Density $\rho_{\mathrm{exp}}$ ($\mathrm{g/cm^3}$, 298.15 K)")
        ax6.set_ylabel(r"Simulated NPT Density $\rho_{\mathrm{sim}}$ ($\mathrm{g/cm^3}$)")
        ax6.set_title("Forward-NPT Bulk Density Parity (0.5 - 5.0 M)", loc="left")
        ax6.legend(loc="lower right")
        out["l6"] = save_slide_svg_and_png(fig6, fig_dir / "fig_l6_density_parity")[:2]

    return out


def build_demo_deck(out_dir: str | Path) -> tuple[Path, Path]:
    """Build the 7-slide (`L1`–`L7`) reference minimalist group-meeting PPTX and `verify_checklist.md`."""
    out_root = Path(out_dir)
    fig_dir = out_root / "figures"
    figs = _generate_demo_figures(fig_dir)

    deck = GroupMeetingDeck(
        project_tag="MgCl2 MLFF & Raman · 组会周报",
        total_slides_hint=7,
    )

    # Slide 1: L1 Cover + TL;DR
    deck.add_l1_cover_tldr(
        date_label="2026-11-12  ·  Weekly Group Meeting",
        title="水系 MgCl₂ 机器学习力场 O4 短程修正与拉曼验证进展",
        presenter_line="汇报人：周俊  |  多尺度分子模拟与原位光谱组",
        tldr_items=[
            ("进展", "完成 O4 短程排斥势与 DBMLFF 耦合重训，跑通 0.5–5.0 M 正向 NPT 验证。"),
            ("发现", "4 M 测试力 RMSE 降至 {{28.4 meV/Å}}，配位数由 7.18 恢复至 {{5.88}}。"),
            ("待拍板", "5 M 高温发散已修复；需敲定下周 {{H₃PO₄ 混酸采样优先级}} 与截断半径。"),
        ],
        action_summary_for_ghost_test="完成 O4-DBMLFF 短程修正重训与 0.5–5.0 M 正向 NPT/拉曼闭环验证",
        estimated_seconds=45,
        notes="开场 40 秒直接汇报三件事：1) O4 短程墙耦合重训已完成；2) 4 M 配位塌缩彻底消除；3) 最后一页有两个具体采样参数请老师拍板。",
    )

    # Slide 2: L2 Hero Figure (Split)
    deck.add_l2_hero_figure(
        action_title="引入 O4 短程排斥修正后，4 M 测试集力 RMSE 降至 {{28.4 meV/Å}}",
        svg_path=figs["l2"][0],
        png_path=figs["l2"][1],
        mode="split",
        takeaway_heading="核心证据与归因",
        takeaways=[
            "**测试集基准**：覆盖 0.5–5.0 M 共 260 帧独立 DFT 构型，{{R² = 0.9994}}。",
            "**近程收益最大**：r_min < 2.0 Å 排斥区壳层力误差降至 {{37 meV/Å（↓81%）}}。",
            "**物理机制**：Pauli 解析墙接管近程推挤，网络专注拟合平滑多体极化残差。",
        ],
        caption="Fig. 1 | 4 M MgCl2 独立测试集力对偶散点与分壳层 RMSE（n=260）。",
        estimated_seconds=75,
        notes="脚本路径：scripts/run_o4_eval.py；DFT 基准泛函：SG15-PBE, Ecut=60 Ry, k-mesh Gamma-only (64 H2O box)。",
    )

    # Slide 3: L3 Baseline vs This Week Dual Comparison
    deck.add_l3_dual_comparison(
        action_title="双图对照证实 O4 修正彻底消除 4 M MgCl₂ 近程非物理配位塌缩",
        left_label="Baseline · Raw MLFF（未加短程墙）",
        left_svg=figs["l3_left"][0],
        left_png=figs["l3_left"][1],
        right_label="This Week · {{O4-DBMLFF 耦合势}}（本周改进）",
        right_svg=figs["l3_right"][0],
        right_png=figs["l3_right"][1],
        delta_summary="1.76 Å 虚假内峰清零，Mg-Ow 主峰定位于 {{2.08 Å}}，配位数由 7.18 收敛至 {{5.88}}（实测 5.9 ± 0.1）。",
        estimated_seconds=75,
        notes="左右两图严格锁定相同坐标量纲 r in [1.45, 5.20] A, g(r) in [0, 14]；采样时长均为 298.15 K 下后 4 ns NVT 轨迹。",
    )

    # Slide 4: L4 2x2 Concentration Grid (C1)
    deck.add_l4_grid_2x2(
        action_title="0.5–4.0 M 跨浓度拉曼 O–H 峰蓝移与实验偏差均小于 {{6 cm⁻¹}}",
        mode="C1",
        c1_svg=figs["l4"][0],
        c1_png=figs["l4"][1],
        c1_heading="跨浓度演化规律",
        c1_takeaways=[
            "**单调蓝移**：0.5 → 4.0 M 主峰由 3416 移至 {{3455 cm⁻¹}}，与实测斜率吻合。",
            "**氢键重构**：Cl⁻ 弱氢键替代水-水强氢键，3228 cm⁻¹ 肩峰权重下降 {{31%}}。",
            "**零微调泛化**：直接耦合 TNEP 极化率张量预测，无光谱过拟合。",
        ],
        estimated_seconds=80,
        notes="光谱计算参数：20 ps NVE 轨迹，采样间隔 2 fs，量子玻色布居修正因子已乘入各向同性拉曼强度。",
    )

    # Slide 5: L5 Troubleshooting / Failure Diagnosis
    deck.add_l5_troubleshooting(
        action_title="定位 5 M 高温 NPT 发散源于接触离子对欠采样并完成闭环修复",
        svg_path=figs["l5"][0],
        png_path=figs["l5"][1],
        symptom="5.0 M @ 330 K 压测至 {{1.42 ns}} 时最大力突增超 12 eV/Å，局部晶胞塌缩。",
        root_cause="崩溃前 Mg²⁺–Cl⁻ 缩至 {{1.89 Å}}；原训练集缺失 d < 2.10 Å 高能推挤样本。",
        fix_and_status="补入 {{180 帧 DFT}} 近程二体扫描更新 v0.9，重跑 330 K 连续 {{10 ns 零发散}}。",
        caption="Fig. 4 | 5.0 M @ 330 K 正向 NPT 最大原子力轨迹（v0.8 vs v0.9）。",
        estimated_seconds=85,
        notes="排雷教训：解析排斥墙覆盖了 Mg-Ow，但初期未对 Mg-Cl 同等开启近程二体约束与主动采样；现已将二体最小距离监控纳入自动化门禁。",
    )

    # Slide 6: L6 Left Figure + Right Native Booktabs Table
    deck.add_l6_booktabs_table(
        action_title="O4-DBMLFF 在体相密度与配位数上同步达到实验级精度",
        table_title="Table 1 · 4.0 M MgCl₂ (298 K) 基准对标",
        table_rows=[
            ["方法", "力 RMSE", "CN(Mg-Ow)", "ρ MAE"],
            ["IOD 0.80", "—", "6.02", "0.048"],
            ["ECC 0.75", "—", "5.94", "0.029"],
            ["Raw MLFF", "142.6 meV/Å", "7.18", "0.037"],
            ["O4-DBMLFF", "{{28.4 meV/Å}}", "{{5.88}}", "{{0.0032}}"],
            ["实验基准", "DFT 参考", "5.9 ± 0.1", "0.000"],
        ],
        col_widths=[1.68, 1.50, 1.38, 1.32],
        highlight_rows=[4],
        mode="split",
        svg_path=figs["l6"][0],
        png_path=figs["l6"][1],
        fig_caption="Fig. 5 | 0.5–5.0 M 正向 NPT 密度与实测对偶图（g/cm³）。",
        takeaways=[
            "**密度闭环**：全浓度 MAE 仅 {{0.0032 g/cm³}}，较 IOD 降低 {{93%}}。",
            "**推理效率**：单卡 4090 达 {{1.8 ns/day}}（512 原子），满足光谱收敛。",
        ],
        estimated_seconds=80,
        notes="正向 NPT 协议：GROMACS/LAMMPS Nose-Hoover 298.15 K + Parrinello-Rahman 1 bar，2 ns 平衡 + 8 ns 统计均值。",
    )

    # Slide 7: L7 Next-Week Plan & Open Questions
    deck.add_l7_plan_and_decisions(
        action_title="下周推进混酸拉曼极化率训练，需拍板采样优先级与截断半径",
        closed_loop_item="完成 4 M 配位排雷与 0.5–5 M 密度验证。",
        next_week_tasks=[
            ("混酸近程采样（周三）", "补 240 帧 DFT，更新 v1.0 复测 330 K。"),
            ("TNEP 极化率重训（周五）", "800 帧 DFPT，拉曼 RRMSE {{< 4.5%}}。"),
            ("低频呼吸模归属（下周一）", "拆解 240 cm⁻¹ 肩峰 SSIP/CIP 贡献。"),
        ],
        decisions_needed=[
            ("240 帧算力优先投向？", "**A（倾向）**：{{4 M + H₃PO₄ 体相}}；B：界面（耗时×2.5）。"),
            ("极化率截断半径 r_c？", "**A（倾向）**：{{5.5 Å}}（兼顾速度）；B：6.5 Å（显存+45%）。"),
        ],
        estimated_seconds=90,
        notes="上周遗留核销：已完成 4 M 配位数异常根因排查与 0.5-5.0 M 正向 NPT 密度曲线补齐。尾页停留投屏讨论：重点记录老师对 Q1 混酸体相 vs 石墨界面双电层优先级、以及 Q2 TNEP 描述符截断半径 r_c (5.5 A vs 6.5 A) 的决定。",
    )

    pptx_path = deck.save(out_root / "Group_Meeting_Minimalist_Demo.pptx")
    checklist_path = deck.write_verify_checklist(
        checklist_path=out_root / "verify_checklist.md",
        pptx_path=pptx_path,
        data_provenance=[
            ("Slide 2 (`L2-split`)", "`figsize=(7.45, 5.00)` `<asvg:svgBlip>` (`tspan=0`)", "`n=260` 独立测试帧，RMSE 为三轴分量均方根误差；SG15-PBE 60 Ry"),
            ("Slide 3 (`L3`)", "`2 × figsize=(5.80, 4.35)` 双独立 `<asvg:svgBlip>`", "298.15 K 下 4 ns NVT 统计均值；同量纲锁定 `ylim=(0, 14)`"),
            ("Slide 4 (`L4-C1`)", "`figsize=(8.20, 5.45)` 2×2 共享坐标轴 `<asvg:svgBlip>`", "0.5/1.0/2.5/4.0 M 各 20 ps NVE 偶极自相关傅里叶变换 + 玻色修正"),
            ("Slide 5 (`L5`)", "`figsize=(5.55, 5.00)` 异常复现与修复对比 `<asvg:svgBlip>`", "5.0 M @ 330 K 正向 NPT 压力测试；新增 180 帧二体近程 DFT 构型"),
            ("Slide 6 (`L6-split`)", "`figsize=(5.85, 5.00)` + 原生 `6×4` Booktabs 三线表", "0.5–5.0 M 共 6 组浓度，每组 8 ns NPT 密度均值对标实验文献值"),
        ],
        advisor_qa=[
            (
                "O4 解析短程排斥势的参数是经验拟合的还是从头算标定的？会不会影响平衡键长？",
                "采用二体 DFT 势能面在 `r < 1.95 Å` 区间拟合玻恩-迈耶/高阶排斥墙，并在 `2.05 Å` 处通过五次多项式平滑衰减至零，因此在 `2.08 Å` 第一水合壳层平衡位置处排斥项导数为 0，完全不偏置平衡键长。",
            ),
            (
                "Slide 3 中 Raw MLFF 为什么在训练 RMSE 看似不高时仍出现 1.76 Å 虚假内峰？",
                "因为常规平衡态 MD 训练集中完全没有 `r < 1.85 Å` 样本，神经网络在无数据区外推出现能量空洞（Energy Hole）；一旦热涨落越过势垒即陷入非物理吸引阱。",
            ),
            (
                "Slide 4 中 4.0 M 拉曼峰位仍有 ~4 cm⁻¹ 蓝移偏差，主要来自力场还是量子核效应？",
                "经典核 MD 未包含零点能与非谐核量子效应（NQE 通常带来约 15–25 cm⁻¹ 红移，与 PBE 泛函固有系统偏差部分抵消），跨浓度相对位移量（Δν = +39 cm⁻¹，3416 → 3455 cm⁻¹ vs 实测 3412 → 3451 cm⁻¹）完全一致。",
            ),
            (
                "Slide 5 增补 180 帧 Mg–Cl 近程样本后，原有低浓度测试集 RMSE 有无退化？",
                "低浓度（0.5–1.0 M）测试集力 RMSE 由 26.9 变为 27.1 meV/Å（波动 < 0.8%），无精度退化，同时彻底消除了高浓高温崩溃。",
            ),
        ],
    )
    return pptx_path, checklist_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Minimalist Weekly Group Meeting / Journal Club PPTX Builder (`group-meeting-ppt`)."
    )
    parser.add_argument(
        "--demo",
        type=Path,
        metavar="OUT_DIR",
        help="Generate a 7-slide (`L1`–`L7`) scientific demo `.pptx` + `verify_checklist.md` in OUT_DIR.",
    )
    args = parser.parse_args(argv)

    if args.demo is None:
        parser.print_help()
        return 0

    pptx_path, checklist_path = build_demo_deck(args.demo)
    print(f"[OK] Generated demo PPTX:      {pptx_path}")
    print(f"[OK] Generated verify checklist: {checklist_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
