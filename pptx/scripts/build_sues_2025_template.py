#!/usr/bin/env python3
"""Build the SUES (上海工程技术大学) 2025 VI academic deck skeleton as an editable .pptx.

The deck has 7 fixed page types: cover, outline, text + figure, three columns,
figure + three-line table, plan, closing. All body text is placeholder text.

Usage:
    python3 scripts/build_sues_2025_template.py                      # rebuild the bundled template
    python3 scripts/build_sues_2025_template.py -o my_deck.pptx --config deck.json
    python3 build_deck.py -o talk.pptx --config deck.json --assets <skill>/assets/sues_2025_vi  # a copy elsewhere

deck.json overrides any key of DEFAULT_CONFIG (title, subtitle, short_title, presenter,
advisor, school, date, sections). For a real talk, copy this script, keep the helper
functions and `add_chrome` / `add_footers`, and replace the slide bodies in `build_deck`.
Page numbers and the navigation bar are generated, so adding or removing a slide needs
no manual renumbering.

Colors: primary 探索蓝 #0A2F99, one warm accent #C2410C, neutrals. 展望蓝 #2E74FF is a
chart-series color only. Fonts: Arial + Microsoft YaHei (present on Windows; substituted
on a Mac without Office, so every text box keeps >=15% width slack).
Sizes follow ../SKILL.md: slide title 28 pt, headings 18 pt, body 16 pt, table 13 pt,
captions 12 pt, footer 10.5 pt.

Requires: python-pptx (pip install python-pptx).
"""

import argparse
import json
import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.oxml import parse_xml

# Official 2025 SUES VI Palette
C_EXPLORE_BLUE = RGBColor(10, 47, 153)     # #0A2F99 探索蓝 (Primary)
C_ENVISION_BLUE = RGBColor(46, 116, 255)   # #2E74FF 展望蓝 (仅用于图表第二序列,不用于文字)
C_ACCENT = RGBColor(194, 65, 12)           # #C2410C 暖橙强调色 (每页最多 1–2 处)
C_TINT = RGBColor(244, 246, 250)           # #F4F6FA 浅灰底
C_NAV_MUTED = RGBColor(150, 175, 230)      # #96AFE6 顶栏非当前章节淡蓝字 (同色系 225° hue)
C_INK = RGBColor(31, 41, 55)               # #1F2937 正文深灰
C_MUTED = RGBColor(95, 95, 95)             # #5F5F5F 辅助灰字
C_SHADED = RGBColor(180, 184, 190)         # #B4B8BE Beamer show/shaded 浅灰字
C_COOL_GREY = RGBColor(199, 199, 199)      # #C7C7C7 官方冷灰线 (PANTONE 427C)
C_WHITE = RGBColor(255, 255, 255)          # #FFFFFF 纯白

FONT_CN = "Microsoft YaHei"
FONT_EN = "Arial"

DEFAULT_CONFIG = {
    "title": "论文或课题题目（不超过两行）",
    "subtitle": "硕士学位论文开题报告 / 阶段进展汇报",
    "short_title": "课题简称",
    "presenter": "姓名",
    "advisor": "导师姓名 教授",
    "school": "学院名称",
    "date": "20XX 年 XX 月",
    "sections": ["课题背景", "研究方法", "阶段进展", "工作计划"],
}

SIZE_TITLE = 28
SIZE_HEAD = 18
SIZE_BODY = 16
SIZE_TABLE = 13
SIZE_CAPTION = 12
SIZE_CHROME = 10.5


def set_run_font(run, size_pt, color=C_INK, bold=False, italic=False):
    """Apply unified Latin + East Asian font settings to a run."""
    run.font.name = FONT_EN
    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = parse_xml(f'<a:ea xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" typeface="{FONT_CN}"/>')
        rPr.append(ea)
    else:
        ea.set("typeface", FONT_CN)


def add_paragraph(tf, text, size_pt=16, color=C_INK, bold=False, align=PP_ALIGN.LEFT,
                  space_after_pt=8, line_spacing=1.30, is_first=False):
    """Add a formatted paragraph to an existing text frame."""
    p = tf.paragraphs[0] if is_first else tf.add_paragraph()
    p.alignment = align
    p.line_spacing = line_spacing
    p.space_after = Pt(space_after_pt)
    r = p.add_run()
    r.text = text
    set_run_font(r, size_pt=size_pt, color=color, bold=bold)
    return p


def add_textbox(slide, left, top, width, height, text="", size_pt=16, color=C_INK,
                bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.28, space_after_pt=6):
    """Add a clean text box directly on the white canvas."""
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.05)
    tf.margin_right = Inches(0.05)
    tf.margin_top = Inches(0.04)
    tf.margin_bottom = Inches(0.04)
    if text:
        for i, line in enumerate(text.split("\n")):
            add_paragraph(
                tf, line, size_pt=size_pt, color=color, bold=bold,
                align=align, space_after_pt=space_after_pt, line_spacing=line_spacing, is_first=(i == 0)
            )
    return tb


def add_rect(slide, left, top, width, height, fill_color=None, line_color=None, line_pt=0.75):
    """Add a rectangular bar or frame."""
    sh = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height)
    )
    if fill_color is not None:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill_color
    else:
        sh.fill.background()
    if line_color is not None and line_pt > 0:
        sh.line.color.rgb = line_color
        sh.line.width = Pt(line_pt)
    else:
        sh.line.fill.background()
    sh.text_frame.word_wrap = True
    sh.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    sh.text_frame.margin_left = Inches(0.15)
    sh.text_frame.margin_right = Inches(0.15)
    sh.text_frame.margin_top = Inches(0.02)
    sh.text_frame.margin_bottom = Inches(0.02)
    return sh


def apply_booktabs_borders(cell, top_pt=0, bottom_pt=0, color_hex="0A2F99"):
    """Apply authentic LaTeX booktabs horizontal rules (toprule/midrule/bottomrule) with no vertical borders."""
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("lnL", "lnR", "lnT", "lnB"):
        old = tcPr.find(qn(f"a:{tag}"))
        if old is not None:
            tcPr.remove(old)

    def _make_ln(tag, pt_val):
        if pt_val <= 0:
            return parse_xml(f'<a:{tag} xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:noFill/></a:{tag}>')
        w_emu = int(pt_val * 12700)
        return parse_xml(
            f'<a:{tag} xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" w="{w_emu}">'
            f'<a:solidFill><a:srgbClr val="{color_hex}"/></a:solidFill>'
            f'</a:{tag}>'
        )

    tcPr.append(_make_ln("lnL", 0))
    tcPr.append(_make_ln("lnR", 0))
    tcPr.append(_make_ln("lnT", top_pt))
    tcPr.append(_make_ln("lnB", bottom_pt))


def add_chrome(slide, cfg, active_sec_idx, slide_title, logo_dir):
    """Watermark, navigation bar with the current section, logo, slide title and rule."""
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

    # One line only: about 26 Chinese characters fit at 28 pt with slack.
    add_textbox(slide, 0.65, 0.50, 12.0, 0.72, text=slide_title, size_pt=SIZE_TITLE, color=C_EXPLORE_BLUE, bold=True)
    add_rect(slide, 0.65, 1.24, 12.03, 0.015, fill_color=C_COOL_GREY)


def add_footers(prs, cfg):
    """Add the footer to every slide. Call once, after all slides exist, so page numbers are right."""
    total = len(prs.slides)
    for page, slide in enumerate(prs.slides, 1):
        left = add_rect(slide, 0.0, 7.14, 6.20, 0.36, fill_color=C_EXPLORE_BLUE)
        add_paragraph(left.text_frame, f"{cfg['presenter']}  |  上海工程技术大学 {cfg['school']}",
                      size_pt=SIZE_CHROME, color=C_WHITE, space_after_pt=0, is_first=True)
        right = add_rect(slide, 6.20, 7.14, 7.133, 0.36, fill_color=C_TINT)
        add_paragraph(right.text_frame, cfg["short_title"],
                      size_pt=SIZE_CHROME, color=C_MUTED, space_after_pt=0, is_first=True)
        add_textbox(slide, 11.75, 7.17, 1.40, 0.30, text=f"{page} / {total}", size_pt=SIZE_CHROME,
                    color=C_MUTED, bold=True, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE, space_after_pt=0)


def build_deck(cfg, logo_dir):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    sections = cfg["sections"]

    logo_blue = os.path.join(logo_dir, "sues_logo_blue.png")
    logo_white = os.path.join(logo_dir, "sues_logo_white.png")
    watermark = os.path.join(logo_dir, "sues_mark_watermark.png")

    # ---- Slide 1: cover -------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    if os.path.exists(watermark):
        s1.shapes.add_picture(watermark, Inches(9.80), Inches(3.20), height=Inches(3.65))
    add_rect(s1, 0.0, 0.0, 13.333, 0.52, fill_color=C_EXPLORE_BLUE)
    if os.path.exists(logo_white):
        s1.shapes.add_picture(logo_white, Inches(10.95), Inches(0.09), height=Inches(0.34))
    if os.path.exists(logo_blue):
        s1.shapes.add_picture(logo_blue, Inches(0.95), Inches(0.95), height=Inches(0.58))

    banner = add_rect(s1, 0.95, 1.90, 11.43, 2.05, fill_color=C_EXPLORE_BLUE)
    banner.text_frame.margin_left = Inches(0.35)
    banner.text_frame.margin_right = Inches(0.35)
    add_paragraph(banner.text_frame, cfg["title"], size_pt=30, color=C_WHITE, bold=True, space_after_pt=10, is_first=True)
    add_paragraph(banner.text_frame, cfg["subtitle"], size_pt=14, color=C_NAV_MUTED, space_after_pt=0)

    add_textbox(
        s1, 0.95, 4.35, 9.5, 2.20,
        text=(f"汇 报 人：{cfg['presenter']}\n"
              f"指导教师：{cfg['advisor']}\n"
              f"所在学院：{cfg['school']}\n"
              f"汇报日期：{cfg['date']}"),
        size_pt=18, color=C_INK, line_spacing=1.42, space_after_pt=6,
    )

    # ---- Slide 2: outline (current section in blue, its note in the accent) ----
    s2 = prs.slides.add_slide(blank_layout)
    add_chrome(s2, cfg, 0, "汇报提纲", logo_dir)
    tf_toc = add_textbox(s2, 1.15, 1.55, 10.5, 5.20).text_frame
    for i, sec in enumerate(sections):
        is_cur = i == 0
        add_paragraph(tf_toc, f"{i + 1:02d}  {sec}", size_pt=22, color=C_EXPLORE_BLUE if is_cur else C_INK,
                      bold=True, space_after_pt=3, is_first=(i == 0))
        add_paragraph(tf_toc, "这一部分要回答的问题，用一句话写清楚", size_pt=SIZE_BODY,
                      color=C_ACCENT if is_cur else C_MUTED, space_after_pt=18)

    # ---- Slide 3: three points on the left, one figure on the right -----------
    s3 = prs.slides.add_slide(blank_layout)
    add_chrome(s3, cfg, 0, "页标题写结论，不写话题（一行以内）", logo_dir)
    tf_l = add_textbox(s3, 0.65, 1.42, 5.65, 5.30).text_frame
    points = [
        ("1. 第一个要点（短语）", "用一到两行说明依据或数据，不要写成段落。", C_EXPLORE_BLUE),
        ("2. 第二个要点（短语）", "每条只讲一件事，细节放到备注或附录页。", C_EXPLORE_BLUE),
        ("3. 本页最重要的一点", "全页只有这一处用强调色，观众先看到它。", C_ACCENT),
    ]
    for i, (head, text, color) in enumerate(points):
        add_paragraph(tf_l, head, size_pt=SIZE_HEAD, color=color, bold=True, space_after_pt=4, is_first=(i == 0))
        add_paragraph(tf_l, text, size_pt=SIZE_BODY, color=C_INK, space_after_pt=16)

    fig_frame = add_rect(s3, 6.55, 1.42, 6.13, 4.70, fill_color=C_WHITE, line_color=C_COOL_GREY, line_pt=0.75)
    add_paragraph(fig_frame.text_frame, "[ 在此插入原图，删除本框 ]", size_pt=14, color=C_MUTED,
                  align=PP_ALIGN.CENTER, space_after_pt=0, is_first=True)
    add_textbox(s3, 6.55, 6.22, 6.13, 0.45, text="图 1  图题：说明图中看什么", size_pt=SIZE_CAPTION,
                color=C_MUTED, align=PP_ALIGN.CENTER)

    # ---- Slide 4: three open columns (top rule only, no boxes) ----------------
    s4 = prs.slides.add_slide(blank_layout)
    add_chrome(s4, cfg, 1, "三个步骤或三个尺度的方法路线", logo_dir)
    stages = [
        ("步骤一 · 名称", ["• 做了什么", "• 用什么方法或工具", "• 得到什么输入或输出", "• 关键参数"]),
        ("步骤二 · 名称（重点）", ["• 做了什么", "• 用什么方法或工具", "• 得到什么输入或输出", "• 关键参数"]),
        ("步骤三 · 名称", ["• 做了什么", "• 用什么方法或工具", "• 得到什么输入或输出", "• 关键参数"]),
    ]
    for idx, (st_title, st_lines) in enumerate(stages):
        x = 0.65 + idx * 4.10
        color = C_ACCENT if idx == 1 else C_EXPLORE_BLUE
        add_rect(s4, x, 1.48, 3.83, 0.05, fill_color=color)
        tf_col = add_textbox(s4, x, 1.63, 3.83, 5.00).text_frame
        add_paragraph(tf_col, st_title, size_pt=SIZE_HEAD, color=color, bold=True, space_after_pt=14, is_first=True)
        for line in st_lines:
            add_paragraph(tf_col, line, size_pt=SIZE_BODY, color=C_INK, space_after_pt=10, line_spacing=1.35)

    # ---- Slide 5: figure left, three-line table right, one conclusion ---------
    s5 = prs.slides.add_slide(blank_layout)
    add_chrome(s5, cfg, 2, "一句话结论：谁比谁好了多少", logo_dir)
    sample_plot = os.path.join(logo_dir, "sues_sample_rdf_plot.png")
    if os.path.exists(sample_plot):
        s5.shapes.add_picture(sample_plot, Inches(0.65), Inches(1.42), width=Inches(5.65))
    add_textbox(s5, 0.65, 6.05, 5.65, 0.45, text="图 2  图题（示例图，替换为自己的原图）", size_pt=SIZE_CAPTION,
                color=C_MUTED, align=PP_ALIGN.CENTER)
    add_textbox(s5, 6.65, 1.42, 6.00, 0.42, text="表 1  表题", size_pt=SIZE_CAPTION,
                color=C_MUTED, bold=True, align=PP_ALIGN.CENTER)

    table_data = [
        ["体系", "指标 A", "指标 B", "指标 C"],
        ["对照组", "0.00", "0.00", "0.0 ± 0.0"],
        ["基线方法", "0.00", "0.00", "0.0 ± 0.0"],
        ["本文方法", "0.00", "0.00", "0.0 ± 0.0"],
        ["实验参考", "0.00", "0.00", "0.0"],
    ]
    key_row = 3  # the one row the audience should read
    rows, cols = len(table_data), len(table_data[0])
    tbl = s5.shapes.add_table(rows, cols, Inches(6.65), Inches(1.90), Inches(6.00), Inches(3.15)).table
    for c_idx, w_in in enumerate([1.70, 1.35, 1.40, 1.55]):
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

    add_textbox(s5, 6.65, 5.30, 6.00, 1.20, text="结论：用一句话写出这页的发现，带上关键数字。",
                size_pt=SIZE_BODY, color=C_EXPLORE_BLUE, bold=True, line_spacing=1.35)

    # ---- Slide 6: plan --------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    add_chrome(s6, cfg, len(sections) - 1, "后续计划与预期成果", logo_dir)
    tf_plan = add_textbox(s6, 0.95, 1.60, 11.2, 5.00).text_frame
    milestones = [
        ("1. 第一阶段（起止年月）：阶段目标", "要完成的工作和可检查的产出。", C_EXPLORE_BLUE),
        ("2. 第二阶段（起止年月）：阶段目标", "要完成的工作和可检查的产出。", C_EXPLORE_BLUE),
        ("3. 第三阶段（起止年月）：论文撰写与答辩", "预期成果：论文、专利或学位论文章节。", C_ACCENT),
    ]
    for i, (head, text, color) in enumerate(milestones):
        add_paragraph(tf_plan, head, size_pt=SIZE_HEAD, color=color, bold=True, space_after_pt=4, is_first=(i == 0))
        add_paragraph(tf_plan, text, size_pt=SIZE_BODY, color=C_INK, space_after_pt=22)

    # ---- Slide 7: closing -----------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    add_chrome(s7, cfg, len(sections) - 1, "致谢与提问", logo_dir)
    if os.path.exists(logo_blue):
        s7.shapes.add_picture(logo_blue, Inches(4.45), Inches(2.05), height=Inches(0.68))
    add_textbox(s7, 1.0, 3.15, 11.33, 2.15, text="敬请各位专家、老师批评指正！\nThank You for Your Attention",
                size_pt=30, color=C_EXPLORE_BLUE, bold=True, align=PP_ALIGN.CENTER, line_spacing=1.38)

    add_footers(prs, cfg)
    return prs


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_dir = os.path.abspath(os.path.join(script_dir, "..", "assets", "sues_2025_vi"))
    # The bundled template lives in this skill and, when installed next to it, in scientific-slides.
    default_outputs = [os.path.join(logo_dir, "SUES_2025_Academic_Template.pptx")]
    sibling = os.path.abspath(os.path.join(script_dir, "..", "..", "scientific-slides", "assets", "sues_2025_vi"))
    if os.path.isdir(sibling):
        default_outputs.append(os.path.join(sibling, "SUES_2025_Academic_Template.pptx"))

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", action="append", help="output .pptx (repeatable); default: the bundled template")
    ap.add_argument("--config", help="JSON file overriding keys of DEFAULT_CONFIG")
    ap.add_argument("--assets", help="directory holding the SUES logo PNGs (default: ../assets/sues_2025_vi)")
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
        prs.save(out_path)
        print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
