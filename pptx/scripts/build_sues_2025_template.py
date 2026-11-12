#!/usr/bin/env python3
"""Build the SUES (上海工程技术大学) 2025 VI figure-dominant academic deck (.pptx).

Preserves the classic SUES 2025 VI institutional chrome (cover slide, top section
navigation bar with white SUES logo, subtle right-bottom three-rotor watermark,
two-tone bottom status bar, and closing slide) while upgrading all interior slides
to a figure-dominant, optically balanced academic layout system:

  1. Cover               (`add_sues_cover`)
  2. 2×2 Balanced Outline (`add_sues_outline_2x2` — zero right-side empty hole)
  3. Wide Diagram + 3 Takeaways (`add_sues_wide_figure` — replaces text-only 3 columns)
  4. 62% Hero Figure + Balanced Right Column (`add_sues_hero_split`)
  5. Dual A/B Comparison Figures + Delta Strip (`add_sues_dual_comparison`)
  6. 2×2 Multi-Panel Grid + Right Summary (`add_sues_grid_2x2`)
  7. Left Figure + Right Booktabs Table (`add_sues_fig_table`)
  8. Visual Milestone Gantt + Deliverables (`add_sues_plan_gantt`)
  9. Closing             (`add_sues_closing`)

Usage:
    python3 scripts/build_sues_2025_template.py                      # rebuild bundled template
    python3 scripts/build_sues_2025_template.py -o my_deck.pptx --config deck.json
    python3 build_deck.py -o talk.pptx --config deck.json --assets <skill>/assets/sues_2025_vi

Colors: primary 探索蓝 #0A2F99, one warm accent #C2410C, neutrals.
Fonts: Arial + Microsoft YaHei (explicit DrawingML <a:ea> on every run).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

# Official 2025 SUES VI Palette
C_EXPLORE_BLUE = RGBColor(10, 47, 153)     # #0A2F99 探索蓝 (Primary)
C_ENVISION_BLUE = RGBColor(46, 116, 255)   # #2E74FF 展望蓝 (Chart series only)
C_ACCENT = RGBColor(194, 65, 12)           # #C2410C 暖橙强调色 (1-2 focal elements/slide)
C_TINT = RGBColor(244, 246, 250)           # #F4F6FA 底栏右半浅冷灰底
C_NAV_MUTED = RGBColor(150, 175, 230)      # #96AFE6 顶栏非当前章节淡蓝字
C_INK = RGBColor(31, 41, 55)               # #1F2937 正文深炭灰
C_MUTED = RGBColor(95, 95, 95)             # #5F5F5F 图注/辅助灰字
C_COOL_GREY = RGBColor(199, 199, 199)      # #C7C7C7 官方冷灰分割线 (PANTONE 427C)
C_WHITE = RGBColor(255, 255, 255)          # #FFFFFF 纯白背景

FONT_CN = "Microsoft YaHei"
FONT_EN = "Arial"

SIZE_TITLE = 26
SIZE_HEAD = 17
SIZE_BODY = 15
SIZE_TABLE = 13
SIZE_CAPTION = 12
SIZE_CHROME = 10.5

# Exact 1:1 physical figure slot sizes (w_in, h_in) for Matplotlib `figsize`
SUES_SLOT_SIZES: dict[str, tuple[float, float]] = {
    "wide_top": (12.03, 4.10),     # Slide 3: Wide workflow / spectrum top slot
    "hero_left": (7.35, 4.85),     # Slide 4: 62% Hero figure left slot
    "dual_ab": (5.80, 4.15),       # Slide 5: Symmetric A/B comparison single slot
    "grid_2x2": (7.95, 5.30),      # Slide 6: 2x2 multi-panel matrix left slot
    "table_left": (5.70, 4.80),    # Slide 7: Figure paired with right booktabs table
    "gantt_left": (7.55, 4.80),    # Slide 8: Milestone Gantt chart left slot
}

DEFAULT_CONFIG = {
    "title": "论文或课题题目（不超过两行）",
    "subtitle": "硕士学位论文开题报告 / 阶段进展汇报",
    "short_title": "课题简称",
    "presenter": "姓名",
    "advisor": "指导教师：导师姓名 教授",
    "school": "学院名称",
    "date": "20XX 年 XX 月",
    "sections": ["课题背景", "研究方案", "阶段进展", "工作计划"],
}

_INLINE_TOKEN_RE = re.compile(r"(\{\{.+?\}\}|\*\*.+?\*\*)")


def set_run_font(run, size_pt: float, color: RGBColor = C_INK, bold: bool = False, italic: bool = False) -> None:
    """Bind Latin Arial + East Asian Microsoft YaHei in valid OOXML schema order."""
    run.font.name = FONT_EN
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    latin = rPr.find(qn("a:latin"))
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = parse_xml(f'<a:ea xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" typeface="{FONT_CN}"/>')
        if latin is not None:
            latin.addnext(ea)
        else:
            rPr.append(ea)
    else:
        ea.set("typeface", FONT_CN)


def populate_formatted_runs(
    paragraph,
    text: str,
    size_pt: float,
    base_color: RGBColor = C_INK,
    base_bold: bool = False,
) -> None:
    """Support `{{warm orange bold}}` and `**explore blue bold**` inline highlights."""
    parts = _INLINE_TOKEN_RE.split(text)
    for part in parts:
        if not part:
            continue
        r = paragraph.add_run()
        if part.startswith("{{") and part.endswith("}}"):
            r.text = part[2:-2]
            set_run_font(r, size_pt=size_pt, color=C_ACCENT, bold=True)
        elif part.startswith("**") and part.endswith("**"):
            r.text = part[2:-2]
            set_run_font(r, size_pt=size_pt, color=C_EXPLORE_BLUE, bold=True)
        else:
            r.text = part
            set_run_font(r, size_pt=size_pt, color=base_color, bold=base_bold)


def add_textbox(
    slide,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str = "",
    size_pt: float = SIZE_BODY,
    color: RGBColor = C_INK,
    bold: bool = False,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    line_spacing: float = 1.32,
    space_after_pt: float = 4,
):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.04)
    tf.margin_right = Inches(0.04)
    tf.margin_top = Inches(0.03)
    tf.margin_bottom = Inches(0.03)
    if text:
        lines = text.split("\n")
        for idx, line in enumerate(lines):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p.alignment = align
            p.line_spacing = line_spacing
            p.space_after = Pt(space_after_pt if idx < len(lines) - 1 else 0)
            populate_formatted_runs(p, line, size_pt=size_pt, base_color=color, base_bold=bold)
    return tb


def add_paragraph(
    tf,
    text: str,
    size_pt: float = SIZE_BODY,
    color: RGBColor = C_INK,
    bold: bool = False,
    align=PP_ALIGN.LEFT,
    space_after_pt: float = 6,
    line_spacing: float = 1.32,
    is_first: bool = False,
):
    p = tf.paragraphs[0] if is_first else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(space_after_pt)
    p.line_spacing = line_spacing
    populate_formatted_runs(p, text, size_pt=size_pt, base_color=color, base_bold=bold)
    return p


def add_rect(slide, x: float, y: float, w: float, h: float, fill_color: RGBColor | None = None, line_color: RGBColor | None = None, line_pt: float = 0.75):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill_color is not None:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill_color
    else:
        sh.fill.background()
    if line_color is not None:
        sh.line.color.rgb = line_color
        sh.line.width = Pt(line_pt)
    else:
        sh.line.fill.background()
    sh.text_frame.word_wrap = True
    sh.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    sh.text_frame.margin_left = Inches(0.14)
    sh.text_frame.margin_right = Inches(0.14)
    sh.text_frame.margin_top = Inches(0.03)
    sh.text_frame.margin_bottom = Inches(0.03)
    return sh


def apply_booktabs_borders(cell, top_pt: float = 0, bottom_pt: float = 0, color_hex: str = "0A2F99") -> None:
    """Authentic LaTeX booktabs cell borders (zero vertical lines)."""
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("lnL", "lnR", "lnT", "lnB", "lnTlToBr", "lnBlToTr"):
        el = tcPr.find(qn(f"a:{tag}"))
        if el is not None:
            tcPr.remove(el)

    def _make_ln(tag_name: str, width_pt: float):
        if width_pt <= 0:
            return parse_xml(f'<a:{tag_name} xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" w="0" cap="flat"><a:noFill/></a:{tag_name}>')
        w_emu = int(round(width_pt * 12700))
        return parse_xml(
            f'<a:{tag_name} xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" w="{w_emu}" cap="flat" cmpd="sng" algn="ctr">'
            f'<a:solidFill><a:srgbClr val="{color_hex}"/></a:solidFill>'
            f'<a:prstDash val="solid"/>'
            f'</a:{tag_name}>'
        )

    tcPr.append(_make_ln("lnL", 0))
    tcPr.append(_make_ln("lnR", 0))
    tcPr.append(_make_ln("lnT", top_pt))
    tcPr.append(_make_ln("lnB", bottom_pt))


def _place_figure(slide, prs, fig_source, box: tuple[float, float, float, float], media_tag: str) -> None:
    """Place `(svg_path, png_path)` via `<asvg:svgBlip>`, or a single `.png` path, or a clean frame."""
    x, y, w, h = box
    if isinstance(fig_source, (tuple, list)) and len(fig_source) == 2:
        svg_p, png_p = Path(fig_source[0]), Path(fig_source[1])
        if svg_p.is_file() and png_p.is_file():
            group_script = Path(__file__).resolve().parents[2] / "group-meeting-ppt" / "scripts"
            if group_script.is_dir() and str(group_script) not in sys.path:
                sys.path.insert(0, str(group_script))
            from group_meeting_builder import add_editable_svg_picture
            add_editable_svg_picture(slide, prs, svg_p, png_p, box=box, media_tag=media_tag)
            return
    if fig_source and os.path.isfile(str(fig_source)):
        from PIL import Image
        with Image.open(str(fig_source)) as im:
            iw, ih = im.size
        aspect = iw / max(ih, 1)
        if w / h > aspect:
            draw_h = h
            draw_w = h * aspect
        else:
            draw_w = w
            draw_h = w / aspect
        px = x + (w - draw_w) / 2.0
        py = y + (h - draw_h) / 2.0
        slide.shapes.add_picture(str(fig_source), Inches(px), Inches(py), width=Inches(draw_w), height=Inches(draw_h))
        return
    frame = add_rect(slide, x, y, w, h, fill_color=C_TINT, line_color=C_COOL_GREY, line_pt=0.75)
    add_paragraph(frame.text_frame, "[ 插入 1:1 槽位原寸科研矢量图 ]", size_pt=14, color=C_MUTED, align=PP_ALIGN.CENTER, space_after_pt=0, is_first=True)


# =============================================================================
# SUES 2025 Institutional Chrome (Preserved Cover, Closing & Background Frame)
# =============================================================================
def add_chrome(slide, cfg: dict, active_sec_idx: int, slide_title: str, logo_dir: str) -> None:
    """Watermark + Exploration Blue top nav bar + white SUES logo + 26pt Action Title + rule (only 3 <p:sp>)."""
    watermark = os.path.join(logo_dir, "sues_mark_watermark.png")
    if os.path.exists(watermark):
        slide.shapes.add_picture(watermark, Inches(10.55), Inches(4.35), height=Inches(2.55))

    nav_bar = add_rect(slide, 0.0, 0.0, 13.333, 0.46, fill_color=C_EXPLORE_BLUE)
    p_nav = nav_bar.text_frame.paragraphs[0]
    p_nav.alignment = PP_ALIGN.LEFT
    sections = cfg["sections"]
    for idx, sec_name in enumerate(sections):
        r = p_nav.add_run()
        sep = "      " if idx < len(sections) - 1 else ""
        is_active = idx == active_sec_idx
        r.text = f"{idx + 1:02d} {sec_name}{sep}"
        set_run_font(r, size_pt=12.0, color=C_WHITE if is_active else C_NAV_MUTED, bold=is_active)

    logo_white = os.path.join(logo_dir, "sues_logo_white.png")
    if os.path.exists(logo_white):
        slide.shapes.add_picture(logo_white, Inches(11.15), Inches(0.07), height=Inches(0.32))

    add_textbox(
        slide, 0.65, 0.50, 12.03, 0.68,
        text=slide_title, size_pt=SIZE_TITLE, color=C_EXPLORE_BLUE, bold=True, line_spacing=1.18,
    )
    add_rect(slide, 0.65, 1.22, 12.03, 0.015, fill_color=C_COOL_GREY)


def add_footers(prs: Presentation, cfg: dict) -> None:
    """Add two-tone SUES footer with auto page numbering across all slides (only 2 <p:sp>/slide)."""
    total = len(prs.slides)
    for page, slide in enumerate(prs.slides, 1):
        left = add_rect(slide, 0.0, 7.14, 6.20, 0.36, fill_color=C_EXPLORE_BLUE)
        add_paragraph(
            left.text_frame, f"{cfg['presenter']}  |  上海工程技术大学 {cfg['school']}",
            size_pt=SIZE_CHROME, color=C_WHITE, space_after_pt=0, is_first=True,
        )
        right = add_rect(slide, 6.20, 7.14, 7.133, 0.36, fill_color=C_TINT)
        right.text_frame.margin_right = Inches(0.28)
        p_r = right.text_frame.paragraphs[0]
        p_r.alignment = PP_ALIGN.RIGHT
        r_title = p_r.add_run()
        r_title.text = f"{cfg['short_title']}          "
        set_run_font(r_title, size_pt=SIZE_CHROME, color=C_MUTED, bold=False)
        r_pg = p_r.add_run()
        r_pg.text = f"{page} / {total}"
        set_run_font(r_pg, size_pt=SIZE_CHROME, color=C_EXPLORE_BLUE, bold=True)


# =============================================================================
# Reusable SUES 2025 Figure-Dominant Page Builders
# =============================================================================
def add_sues_cover(prs: Presentation, cfg: dict, logo_dir: str):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    logo_blue = os.path.join(logo_dir, "sues_logo_blue.png")
    logo_white = os.path.join(logo_dir, "sues_logo_white.png")
    watermark = os.path.join(logo_dir, "sues_mark_watermark.png")

    if os.path.exists(watermark):
        s.shapes.add_picture(watermark, Inches(9.80), Inches(3.20), height=Inches(3.65))
    add_rect(s, 0.0, 0.0, 13.333, 0.52, fill_color=C_EXPLORE_BLUE)
    if os.path.exists(logo_white):
        s.shapes.add_picture(logo_white, Inches(10.95), Inches(0.09), height=Inches(0.34))
    if os.path.exists(logo_blue):
        s.shapes.add_picture(logo_blue, Inches(0.95), Inches(0.95), height=Inches(0.58))

    banner = add_rect(s, 0.95, 1.90, 11.43, 2.08, fill_color=C_EXPLORE_BLUE)
    banner.text_frame.margin_left = Inches(0.35)
    banner.text_frame.margin_right = Inches(0.35)
    add_paragraph(banner.text_frame, cfg["title"], size_pt=28, color=C_WHITE, bold=True, space_after_pt=8, is_first=True)
    add_paragraph(banner.text_frame, cfg["subtitle"], size_pt=14, color=C_NAV_MUTED, space_after_pt=0)

    advisor_line = cfg["advisor"] if "：" in cfg["advisor"] else f"指导教师：{cfg['advisor']}"
    add_textbox(
        s, 0.95, 4.36, 9.8, 2.20,
        text=(
            f"汇 报 人：{cfg['presenter']}\n"
            f"{advisor_line}\n"
            f"所在学院：{cfg['school']}\n"
            f"汇报日期：{cfg['date']}"
        ),
        size_pt=18, color=C_INK, line_spacing=1.42, space_after_pt=6,
    )
    return s


def add_sues_outline_2x2(
    prs: Presentation,
    cfg: dict,
    logo_dir: str,
    section_details: list[tuple[str, str]],
    slide_title: str = "汇报提纲与研究脉络",
):
    """Balanced 2x2 TOC grid that eliminates right-side blank holes."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(s, cfg, 0, slide_title, logo_dir)

    # Subtle crosshair hairlines dividing 4 balanced quadrants
    add_rect(s, 6.66, 1.56, 0.012, 5.12, fill_color=C_COOL_GREY)
    add_rect(s, 0.85, 4.10, 11.63, 0.012, fill_color=C_COOL_GREY)

    coords = [
        (0.85, 1.58),
        (7.02, 1.58),
        (0.85, 4.34),
        (7.02, 4.34),
    ]
    for idx, (sec_head, sec_desc) in enumerate(section_details[:4]):
        qx, qy = coords[idx]
        is_focus = idx == 2  # highlight core progress section with single warm accent
        tf = add_textbox(s, qx, qy, 5.46, 2.22, anchor=MSO_ANCHOR.MIDDLE).text_frame
        head_color = C_ACCENT if is_focus else C_EXPLORE_BLUE
        add_paragraph(
            tf, f"{idx + 1:02d}  {sec_head}",
            size_pt=20, color=head_color, bold=True, space_after_pt=8, is_first=True,
        )
        add_paragraph(
            tf, sec_desc,
            size_pt=15.5, color=C_INK, space_after_pt=0, line_spacing=1.38,
        )
    return s


def add_sues_wide_figure(
    prs: Presentation,
    cfg: dict,
    logo_dir: str,
    sec_idx: int,
    slide_title: str,
    fig_source,
    bottom_columns: list[tuple[str, str]],
    media_tag: str = "sues_wide",
):
    """L2-wide: Top 12.03"x4.10" figure/diagram + 3 compact aligned bottom columns."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(s, cfg, sec_idx, slide_title, logo_dir)
    _place_figure(s, prs, fig_source, (0.65, 1.36, 12.03, 4.10), media_tag=media_tag)

    for idx, (col_head, col_text) in enumerate(bottom_columns[:3]):
        cx = 0.65 + idx * 4.10
        bar_c = C_ACCENT if idx == 1 else C_EXPLORE_BLUE
        add_rect(s, cx, 5.62, 3.83, 0.035, fill_color=bar_c)
        tf = add_textbox(s, cx, 5.71, 3.83, 1.18).text_frame
        add_paragraph(tf, col_head, size_pt=15.5, color=bar_c, bold=True, space_after_pt=3, is_first=True)
        add_paragraph(tf, col_text, size_pt=14.0, color=C_INK, space_after_pt=0, line_spacing=1.28)
    return s


def add_sues_hero_split(
    prs: Presentation,
    cfg: dict,
    logo_dir: str,
    sec_idx: int,
    slide_title: str,
    fig_source,
    caption: str,
    takeaways: list[tuple[str, str]],
    media_tag: str = "sues_hero",
):
    """L2-split: Left 62% Hero Figure (7.35"x4.85") + Optically Centered Right Takeaways."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(s, cfg, sec_idx, slide_title, logo_dir)
    _place_figure(s, prs, fig_source, (0.65, 1.38, 7.35, 4.85), media_tag=media_tag)
    add_textbox(s, 0.65, 6.30, 7.35, 0.42, text=caption, size_pt=SIZE_CAPTION, color=C_MUTED, align=PP_ALIGN.CENTER)

    add_rect(s, 8.22, 1.44, 0.015, 5.18, fill_color=C_COOL_GREY)
    tf_r = add_textbox(s, 8.42, 1.40, 4.26, 5.26, anchor=MSO_ANCHOR.MIDDLE).text_frame
    for idx, (head, body) in enumerate(takeaways):
        is_last = idx == len(takeaways) - 1
        h_color = C_ACCENT if is_last else C_EXPLORE_BLUE
        add_paragraph(tf_r, head, size_pt=SIZE_HEAD, color=h_color, bold=True, space_after_pt=4, is_first=(idx == 0))
        add_paragraph(tf_r, body, size_pt=SIZE_BODY, color=C_INK, space_after_pt=0 if is_last else 18, line_spacing=1.34)
    return s


def add_sues_dual_comparison(
    prs: Presentation,
    cfg: dict,
    logo_dir: str,
    sec_idx: int,
    slide_title: str,
    left_label: str,
    left_fig,
    right_label: str,
    right_fig,
    delta_summary: str,
    media_tag: str = "sues_dual",
):
    """L3: Symmetric A/B Figure Comparison (two 5.80"x4.15" slots) + Bottom Quantitative Strip."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(s, cfg, sec_idx, slide_title, logo_dir)

    add_textbox(s, 0.65, 1.36, 5.80, 0.36, text=left_label, size_pt=15.5, color=C_EXPLORE_BLUE, bold=True, align=PP_ALIGN.CENTER)
    _place_figure(s, prs, left_fig, (0.65, 1.76, 5.80, 4.15), media_tag=f"{media_tag}_L")

    add_textbox(s, 6.88, 1.36, 5.80, 0.36, text=right_label, size_pt=15.5, color=C_ACCENT, bold=True, align=PP_ALIGN.CENTER)
    _place_figure(s, prs, right_fig, (6.88, 1.76, 5.80, 4.15), media_tag=f"{media_tag}_R")

    add_rect(s, 0.65, 6.06, 12.03, 0.015, fill_color=C_COOL_GREY)
    add_textbox(
        s, 0.65, 6.14, 12.03, 0.68,
        text=delta_summary, size_pt=15.0, color=C_INK, anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.30,
    )
    return s


def add_sues_grid_2x2(
    prs: Presentation,
    cfg: dict,
    logo_dir: str,
    sec_idx: int,
    slide_title: str,
    grid_fig,
    takeaways: list[tuple[str, str]],
    media_tag: str = "sues_grid",
):
    """L4: Left 7.95"x5.30" 2x2 Multi-Panel Figure + Optically Centered Right Takeaways."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(s, cfg, sec_idx, slide_title, logo_dir)
    _place_figure(s, prs, grid_fig, (0.65, 1.38, 7.95, 5.30), media_tag=media_tag)

    add_rect(s, 8.80, 1.44, 0.015, 5.18, fill_color=C_COOL_GREY)
    tf_r = add_textbox(s, 9.00, 1.40, 3.68, 5.26, anchor=MSO_ANCHOR.MIDDLE).text_frame
    for idx, (head, body) in enumerate(takeaways):
        is_last = idx == len(takeaways) - 1
        h_color = C_ACCENT if is_last else C_EXPLORE_BLUE
        add_paragraph(tf_r, head, size_pt=16.5, color=h_color, bold=True, space_after_pt=4, is_first=(idx == 0))
        add_paragraph(tf_r, body, size_pt=14.5, color=C_INK, space_after_pt=0 if is_last else 18, line_spacing=1.34)
    return s


def add_sues_fig_table(
    prs: Presentation,
    cfg: dict,
    logo_dir: str,
    sec_idx: int,
    slide_title: str,
    fig_source,
    fig_caption: str,
    table_title: str,
    table_data: list[list[str]],
    col_widths: list[float],
    key_row: int,
    summary_bullets: list[str],
    media_tag: str = "sues_tbl",
):
    """L6: Left Figure (5.70"x4.80") + Right Booktabs Table + Aligned Summary."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(s, cfg, sec_idx, slide_title, logo_dir)
    _place_figure(s, prs, fig_source, (0.65, 1.38, 5.70, 4.80), media_tag=media_tag)
    add_textbox(s, 0.65, 6.26, 5.70, 0.42, text=fig_caption, size_pt=SIZE_CAPTION, color=C_MUTED, align=PP_ALIGN.CENTER)

    add_textbox(s, 6.65, 1.38, 6.03, 0.40, text=table_title, size_pt=14.5, color=C_EXPLORE_BLUE, bold=True, align=PP_ALIGN.CENTER)
    rows, cols = len(table_data), len(table_data[0])
    tbl = s.shapes.add_table(rows, cols, Inches(6.65), Inches(1.84), Inches(6.03), Inches(2.92)).table
    for c_idx, w_in in enumerate(col_widths):
        tbl.columns[c_idx].width = Inches(w_in)
    for r_idx, row in enumerate(table_data):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = C_WHITE
            top_pt = 1.5 if r_idx == 0 else 0
            bot_pt = 0.75 if r_idx == 0 else (1.5 if r_idx == rows - 1 else 0)
            apply_booktabs_borders(cell, top_pt=top_pt, bottom_pt=bot_pt, color_hex="0A2F99")
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT
            run = p.add_run()
            run.text = val
            color = C_EXPLORE_BLUE if r_idx == 0 else (C_ACCENT if r_idx == key_row else C_INK)
            set_run_font(run, size_pt=SIZE_TABLE, color=color, bold=r_idx in (0, key_row))

    tf_b = add_textbox(s, 6.65, 5.06, 6.03, 1.62, anchor=MSO_ANCHOR.MIDDLE).text_frame
    for idx, line in enumerate(summary_bullets):
        add_paragraph(
            tf_b, line, size_pt=15.0, color=C_INK,
            space_after_pt=0 if idx == len(summary_bullets) - 1 else 8,
            line_spacing=1.32, is_first=(idx == 0),
        )
    return s


def add_sues_plan_gantt(
    prs: Presentation,
    cfg: dict,
    logo_dir: str,
    slide_title: str,
    gantt_fig,
    gantt_caption: str,
    deliverables: list[tuple[str, str]],
    media_tag: str = "sues_gantt",
):
    """Visual Gantt Roadmap Left (7.55"x4.80") + Concrete Deliverables Right."""
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(s, cfg, len(cfg["sections"]) - 1, slide_title, logo_dir)
    _place_figure(s, prs, gantt_fig, (0.65, 1.38, 7.55, 4.80), media_tag=media_tag)
    add_textbox(s, 0.65, 6.26, 7.55, 0.42, text=gantt_caption, size_pt=SIZE_CAPTION, color=C_MUTED, align=PP_ALIGN.CENTER)

    add_rect(s, 8.42, 1.44, 0.020, 5.18, fill_color=C_ACCENT)
    tf_r = add_textbox(s, 8.62, 1.40, 4.06, 5.26, anchor=MSO_ANCHOR.MIDDLE).text_frame
    for idx, (head, desc) in enumerate(deliverables):
        is_last = idx == len(deliverables) - 1
        add_paragraph(
            tf_r, head, size_pt=16.5, color=C_ACCENT if is_last else C_EXPLORE_BLUE,
            bold=True, space_after_pt=4, is_first=(idx == 0),
        )
        add_paragraph(
            tf_r, desc, size_pt=14.5, color=C_INK,
            space_after_pt=0 if is_last else 18, line_spacing=1.34,
        )
    return s


def add_sues_closing(prs: Presentation, cfg: dict, logo_dir: str):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_chrome(s, cfg, len(cfg["sections"]) - 1, "致谢与提问", logo_dir)
    logo_blue = os.path.join(logo_dir, "sues_logo_blue.png")
    if os.path.exists(logo_blue):
        s.shapes.add_picture(logo_blue, Inches(4.45), Inches(2.05), height=Inches(0.68))
    add_textbox(
        s, 1.0, 3.15, 11.33, 2.15,
        text="敬请各位专家、老师批评指正！\nThank You for Your Attention",
        size_pt=30, color=C_EXPLORE_BLUE, bold=True, align=PP_ALIGN.CENTER, line_spacing=1.38,
    )
    return s


# =============================================================================
# Sample 1:1 Figures for the Bundled SUES Template Skeleton
# =============================================================================
def _generate_template_sample_plots(tmp_dir: Path, sample_rdf_png: str) -> dict[str, str]:
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    import numpy as np

    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 1.1,
        "axes.edgecolor": "#1F2937",
        "axes.labelsize": 12.5,
        "xtick.labelsize": 11.0,
        "ytick.labelsize": 11.0,
        "legend.fontsize": 10.5,
    })
    out: dict[str, str] = {}

    # 1. Wide workflow schematic (12.03 x 4.10)
    fig, ax = plt.subplots(figsize=SUES_SLOT_SIZES["wide_top"], dpi=300)
    fig.subplots_adjust(left=0.0, right=1.0, bottom=0.0, top=1.0)
    ax.set_xlim(0, 12.03)
    ax.set_ylim(0, 4.10)
    ax.axis("off")
    boxes = [
        (0.10, 0.35, 3.38, 3.40, "#0A2F99", "Stage 1 · Theory / Model", "Input structures & baseline equations\nKey physical assumptions\nOutput: Reference dataset"),
        (4.32, 0.35, 3.38, 3.40, "#C2410C", "Stage 2 · Core Method (Ours)", "Key algorithmic / force-field fix\nCross-regime sampling & training\nOutput: Validated trajectory"),
        (8.54, 0.35, 3.38, 3.40, "#0A2F99", "Stage 3 · Observable & Check", "Quantitative property prediction\nExperimental benchmark closure\nOutput: Design rule"),
    ]
    for bx, by, bw, bh, col, title_s, body_s in boxes:
        rect = mpl.patches.FancyBboxPatch((bx, by), bw, bh, boxstyle="round,pad=0.03,rounding_size=0.08", facecolor="#FFFFFF", edgecolor=col, linewidth=1.8)
        ax.add_patch(rect)
        ax.plot([bx, bx + bw], [by + bh - 0.68, by + bh - 0.68], color="#E5E7EB", lw=1.0)
        ax.text(bx + bw / 2, by + bh - 0.36, title_s, ha="center", va="center", fontsize=12.0, fontweight="bold", color=col)
        ax.text(bx + bw / 2, by + 1.30, body_s, ha="center", va="center", fontsize=10.8, color="#1F2937", linespacing=1.60)
    for ax_x in (3.58, 7.80):
        ax.annotate("", xy=(ax_x + 0.64, 2.05), xytext=(ax_x, 2.05), arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#0A2F99"))
    p_wide = str(tmp_dir / "tpl_wide.png")
    fig.savefig(p_wide, dpi=300, facecolor="white")
    plt.close(fig)
    out["wide"] = p_wide

    # 2. Hero split figure (7.35 x 4.85)
    x = np.linspace(0, 5, 200)
    fig, ax = plt.subplots(figsize=SUES_SLOT_SIZES["hero_left"], dpi=300, layout="constrained")
    ax.plot(x, np.exp(-0.45 * x) + 0.12, "--", color="#94A3B8", lw=2.2, label="Baseline Method")
    ax.plot(x, 0.32 * np.exp(-0.95 * x) + 0.04, "-", color="#0A2F99", lw=2.6, label="Proposed Method (Ours)")
    ax.scatter([1.0, 2.5, 4.0], [0.16, 0.07, 0.047], color="#C2410C", s=48, zorder=5, label="Key Benchmark Points")
    ax.set_xlabel("Control Parameter x")
    ax.set_ylabel("Error Metric (arb. units)")
    ax.legend(frameon=False)
    p_hero = str(tmp_dir / "tpl_hero.png")
    fig.savefig(p_hero, dpi=300, facecolor="white")
    plt.close(fig)
    out["hero"] = p_hero

    # 3. Dual comparison A/B (5.80 x 4.15)
    for tag, col, scale, title_tag in [("dual_L", "#64748B", 1.0, "Baseline"), ("dual_R", "#C2410C", 0.35, "Improved")]:
        fig, ax = plt.subplots(figsize=SUES_SLOT_SIZES["dual_ab"], dpi=300, layout="constrained")
        r = np.linspace(1.5, 5.0, 300)
        y_true = np.exp(-((r - 2.2) / 0.25) ** 2) * 8.0
        y_pred = y_true + scale * 3.2 * np.exp(-((r - 1.85) / 0.14) ** 2)
        ax.plot(r, y_true, ":", color="#0F172A", lw=1.8, label="Reference")
        ax.plot(r, y_pred, "-", color=col, lw=2.4, label=title_tag)
        ax.set_ylim(0, 10.5)
        ax.set_xlabel("Coordinate r")
        ax.set_ylabel("Intensity")
        ax.legend(frameon=False, loc="upper right")
        p_d = str(tmp_dir / f"{tag}.png")
        fig.savefig(p_d, dpi=300, facecolor="white")
        plt.close(fig)
        out[tag] = p_d

    # 4. 2x2 Grid (7.95 x 5.30)
    fig, axes = plt.subplots(2, 2, figsize=SUES_SLOT_SIZES["grid_2x2"], dpi=300, sharex=True, sharey=True, layout="constrained")
    xx = np.linspace(0, 4, 150)
    for idx, ax in enumerate(axes.flat):
        ax.plot(xx, np.sin(xx + 0.4 * idx) * np.exp(-0.25 * xx), color="#0A2F99", lw=2.1, label="Sim.")
        ax.plot(xx, np.sin(xx + 0.4 * idx) * np.exp(-0.25 * xx) * 0.96, "--", color="#C2410C", lw=1.8, label="Exp.")
        ax.set_title(f"({chr(97 + idx)}) Condition {idx + 1}", loc="left", fontsize=11.5, fontweight="bold", color="#0A2F99")
        if idx == 0:
            ax.legend(frameon=False, loc="upper right")
    axes[1, 0].set_xlabel("Variable")
    axes[1, 1].set_xlabel("Variable")
    axes[0, 0].set_ylabel("Response")
    axes[1, 0].set_ylabel("Response")
    p_grid = str(tmp_dir / "tpl_grid.png")
    fig.savefig(p_grid, dpi=300, facecolor="white")
    plt.close(fig)
    out["grid"] = p_grid

    # 5. Table left plot
    out["table_left"] = sample_rdf_png

    # 6. Gantt chart (7.55 x 4.80)
    fig, ax = plt.subplots(figsize=SUES_SLOT_SIZES["gantt_left"], dpi=300, layout="constrained")
    tasks = ["Stage 4: Thesis & Defense", "Stage 3: Exp. Validation", "Stage 2: Core Modeling", "Stage 1: Baseline Audit"]
    starts = [7.5, 5.0, 2.0, 0.0]
    durs = [4.0, 3.5, 4.0, 2.5]
    cols = ["#94A3B8", "#0A2F99", "#C2410C", "#0A2F99"]
    for i, (t, st, du, c) in enumerate(zip(tasks, starts, durs, cols)):
        ax.barh(i, du, left=st, height=0.46, color=c, alpha=0.90)
    ax.set_yticks(range(len(tasks)), tasks)
    ax.set_xlim(0, 12)
    ax.set_xlabel("Timeline (Months)")
    ax.grid(axis="x", linestyle=":", color="#CBD5E1")
    p_gantt = str(tmp_dir / "tpl_gantt.png")
    fig.savefig(p_gantt, dpi=300, facecolor="white")
    plt.close(fig)
    out["gantt"] = p_gantt
    return out


def build_deck(cfg: dict, logo_dir: str) -> Presentation:
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    sample_rdf = os.path.join(logo_dir, "sues_sample_rdf_plot.png")
    with tempfile.TemporaryDirectory() as tmp:
        plots = _generate_template_sample_plots(Path(tmp), sample_rdf)
        secs = cfg["sections"]

        add_sues_cover(prs, cfg, logo_dir)

        add_sues_outline_2x2(
            prs, cfg, logo_dir,
            section_details=[
                (secs[0], "核心科学瓶颈、既有方法局限性与立项切入点"),
                (secs[1], "跨尺度理论建模路线、关键修正与验证指标"),
                (secs[2], "核心定量实验/模拟对比、多条件演化与误差基准"),
                (secs[3], "时间节点甘特排期、论文产出计划与预期目标"),
            ],
        )

        add_sues_wide_figure(
            prs, cfg, logo_dir, sec_idx=1,
            slide_title="页标题写完整结论句：用宽幅流程图取代干瘪纯文字分栏",
            fig_source=plots["wide"],
            bottom_columns=[
                ("阶段一 · 基准构建", "明确输入构型、参考精度与边界条件。"),
                ("阶段二 · 核心创新（重点）", "一句话点出本文改进与{{关键定量增益}}。"),
                ("阶段三 · 闭环验证", "关联可观测物理量，与实测数据交叉核验。"),
            ],
        )

        add_sues_hero_split(
            prs, cfg, logo_dir, sec_idx=2,
            slide_title="单主图页黄金比例：左侧 62% 大图主导，右侧要点垂直居中对齐",
            fig_source=plots["hero"],
            caption="图 1  主图说明：用 1:1 插槽尺寸出图，字号与线宽入片零缩放",
            takeaways=[
                ("1. 基准测试规模", "交代样本量、控制变量与独立验证集定义。"),
                ("2. 物理机制归因", "解释误差下降或性能提升背后的主导物理项。"),
                ("3. 核心定量突破", "全页仅此处使用强调色突出 {{关键指标降幅}}。"),
            ],
        )

        add_sues_dual_comparison(
            prs, cfg, logo_dir, sec_idx=2,
            slide_title="双图对照页：左右锁定同一坐标量纲，直观展示改进前后差异",
            left_label="Baseline · 传统基线方案",
            left_fig=plots["dual_L"],
            right_label="Ours · 本文改进方案（消除伪峰）",
            right_fig=plots["dual_R"],
            delta_summary="定量对比结论：虚假异常峰彻底消除，主峰位置与参考基准偏差降至 {{1.5% 以内}}。",
        )

        add_sues_grid_2x2(
            prs, cfg, logo_dir, sec_idx=2,
            slide_title="四宫格矩阵页：多浓度或多条件演化规律一屏完整呈现",
            grid_fig=plots["grid"],
            takeaways=[
                ("单调演化趋势", "跨四个条件区间响应曲线保持平滑一致规律。"),
                ("实验高度吻合", "全部子图预测值与实测虚线相对偏差 {{< 3%}}。"),
                ("零微调泛化", "同一套参数跨区间外推无需逐点重新拟合。"),
            ],
        )

        add_sues_fig_table(
            prs, cfg, logo_dir, sec_idx=2,
            slide_title="左图右三线表页：图形趋势与精确基准数字顶底齐平互证",
            fig_source=plots["table_left"],
            fig_caption="图 5  代表性径向分布函数与第一壳层截断位置",
            table_title="表 1  不同方案核心指标定量对比",
            table_data=[
                ["方法方案", "误差指标", "结构参数", "相对耗时"],
                ["传统基线 A", "0.87", "4.80", "1.0×"],
                ["改进基线 B", "0.70", "5.58", "1.1×"],
                ["本文方案", "0.35", "5.70", "1.1×"],
                ["实验参考", "—", "5.72 ± 0.1", "—"],
            ],
            col_widths=[1.75, 1.40, 1.50, 1.38],
            key_row=3,
            summary_bullets=[
                "• **精度突破**：本文方案将外部盲测误差降低 {{59.7%}}，结构参数落入实验误差带。",
                "• **效率保持**：推理开销与传统力场同量级，满足纳秒级采样需求。",
            ],
        )

        add_sues_plan_gantt(
            prs, cfg, logo_dir,
            slide_title="后续研究计划：甘特排期图取代大段稀疏文字列表",
            gantt_fig=plots["gantt"],
            gantt_caption="图 6  研究阶段推进时间轴与关键里程碑节点",
            deliverables=[
                ("1. 近期节点（3 个月内）", "完成核心修正重采样，整理阶段一独立论文初稿。"),
                ("2. 中期节点（6 个月内）", "打通跨尺度性质预测与实验表征闭环对标。"),
                ("3. 预期终期成果", "发表 {{1–2 篇高水平期刊论文}}，完成学位论文撰写与答辩。"),
            ],
        )

        add_sues_closing(prs, cfg, logo_dir)
        add_footers(prs, cfg)
    return prs


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_dir = os.path.abspath(os.path.join(script_dir, "..", "assets", "sues_2025_vi"))
    default_outputs = [os.path.join(logo_dir, "SUES_2025_Academic_Template.pptx")]
    sibling = os.path.abspath(os.path.join(script_dir, "..", "..", "scientific-slides", "assets", "sues_2025_vi"))
    if os.path.isdir(sibling):
        default_outputs.append(os.path.join(sibling, "SUES_2025_Academic_Template.pptx"))

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", action="append", help="output .pptx (repeatable); default: bundled template")
    ap.add_argument("--config", help="JSON file overriding keys of DEFAULT_CONFIG")
    ap.add_argument("--assets", help="directory holding SUES logo PNGs (default: ../assets/sues_2025_vi)")
    args = ap.parse_args()

    if args.assets:
        logo_dir = os.path.abspath(args.assets)
        if not os.path.isfile(os.path.join(logo_dir, "sues_logo_white.png")):
            sys.exit(f"No SUES logos in {logo_dir}")

    cfg = dict(DEFAULT_CONFIG)
    if args.config:
        with open(args.config, encoding="utf-8") as fh:
            user_cfg = json.load(fh)
        unknown = sorted(set(user_cfg) - set(DEFAULT_CONFIG))
        if unknown:
            sys.exit(f"Unknown config key(s): {', '.join(unknown)}")
        cfg.update(user_cfg)

    prs = build_deck(cfg, logo_dir)
    for out_path in args.output or default_outputs:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        prs.save(out_path)
        print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
