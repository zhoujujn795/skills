#!/usr/bin/env python3
"""
Build the Shanghai University of Engineering Science (SUES / 上海工程技术大学)
2025 New Visual Identity (VI) Academic Presentation Template (.pptx),
synthesizing the classic Chinese university defense slide architecture from:
  1. Zhejiang University (ZJU-Beamer-Template / ZJU-PPT):
     - Top navigation bar with live section indicator + top-right white university logo
     - Subtle right-side university emblem watermark (6% opacity on white canvas)
     - Split two-tone bottom institutional status bar (Author/School | Short Title | Page #)
  2. Tsinghua & SUES Beamer Themes (THU / suesbeamer.sty):
     - Beamer `show/shaded` section transition page (active section highlighted, others dimmed)
     - Direct-on-white-canvas itemize typography (no gray card stacking)
     - Authentic LaTeX `booktabs` three-line table (toprule, midrule, bottomrule, no solid fills)
  3. SUES 2025 Official VI System (designed by Prof. Wang Min, CAFA):
     - Primary: 探索蓝 Exploration Blue #0A2F99 (RGB: 10, 47, 153 | PANTONE 2146C)
     - Accent:  展望蓝 Envision Blue    #2E74FF (RGB: 46, 116, 255 | PANTONE 2727C)
     - Neutral: Ink #1B1B1B, Muted #595959, Cool Grey #C7C7C7 (PANTONE 427C), White #FFFFFF
"""

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
C_ENVISION_BLUE = RGBColor(46, 116, 255)   # #2E74FF 展望蓝 (Accent)
C_NAV_MUTED = RGBColor(150, 175, 230)      # #96AFE6 顶栏非当前章节淡蓝字 (同色系 225° hue)
C_INK = RGBColor(27, 27, 27)               # #1B1B1B 正文深黑
C_MUTED = RGBColor(95, 95, 95)             # #5F5F5F 辅助灰字
C_SHADED = RGBColor(180, 184, 190)         # #B4B8BE Beamer show/shaded 浅灰字
C_COOL_GREY = RGBColor(199, 199, 199)      # #C7C7C7 官方冷灰线 (PANTONE 427C)
C_WHITE = RGBColor(255, 255, 255)          # #FFFFFF 纯白

FONT_CN = "PingFang SC"
FONT_EN = "Arial"

NAV_SECTIONS = ["01 课题背景", "02 研究方法", "03 阶段进展", "04 工作计划"]


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


def add_zju_sues_chrome(slide, active_sec_idx, slide_title, page_num, total_pages, logo_dir):
    """
    ZJU + THU/SUES Beamer Chrome (only 6 shapes + 2 images):
      1. Watermark: Subtle 6%-opacity SUES 2025 three-rotor emblem on right canvas (like ZJU Beamer)
      2. Top Navigation Bar (0.00"-0.46", Exploration Blue #0A2F99):
         - Section progress links (active section in bold white, others dimmed)
         - Top-right white SUES 2025 logo (`sues_logo_white.png`)
      3. Slide Title (0.54"-1.02", Exploration Blue #0A2F99 Bold) + thin Cool Grey rule at y=1.06"
      4. Two-tone Bottom Status Bar (7.14"-7.50", like ZJU & SUES Beamer footline):
         - Left bar (#0A2F99): Presenter & Affiliation
         - Right bar (#2E74FF): Short Report Title & Page Number
    """
    # 1. Right-side subtle watermark (placed first so it stays behind everything)
    watermark = os.path.join(logo_dir, "sues_mark_watermark.png")
    if os.path.exists(watermark):
        slide.shapes.add_picture(watermark, Inches(10.55), Inches(4.35), height=Inches(2.55))

    # 2. Top Navigation Bar (#0A2F99)
    nav_bar = add_rect(slide, 0.0, 0.0, 13.333, 0.46, fill_color=C_EXPLORE_BLUE)
    tf_nav = nav_bar.text_frame
    p_nav = tf_nav.paragraphs[0]
    p_nav.alignment = PP_ALIGN.LEFT
    for idx, sec_name in enumerate(NAV_SECTIONS):
        r = p_nav.add_run()
        sep = "      " if idx < len(NAV_SECTIONS) - 1 else ""
        is_active = (idx == active_sec_idx)
        prefix = "● " if is_active else "○ "
        r.text = f"{prefix}{sec_name}{sep}"
        set_run_font(
            r,
            size_pt=12.0,
            color=C_WHITE if is_active else C_NAV_MUTED,
            bold=is_active
        )

    # Top-right white SUES 2025 horizontal logo inside the navigation bar
    logo_white = os.path.join(logo_dir, "sues_logo_white.png")
    if os.path.exists(logo_white):
        slide.shapes.add_picture(logo_white, Inches(11.15), Inches(0.07), height=Inches(0.32))

    # 3. Slide Action Title + Hairline Rule
    add_textbox(
        slide, 0.65, 0.50, 12.0, 0.62,
        text=slide_title, size_pt=22, color=C_EXPLORE_BLUE, bold=True
    )
    add_rect(slide, 0.65, 1.14, 12.03, 0.015, fill_color=C_COOL_GREY)

    # 4. Bottom Two-Tone Beamer Footline (y = 7.14" to 7.50")
    foot_left = add_rect(slide, 0.0, 7.14, 6.20, 0.36, fill_color=C_EXPLORE_BLUE)
    add_paragraph(
        foot_left.text_frame,
        "周 俊  |  上海工程技术大学 材料科学与工程学院",
        size_pt=10.5, color=C_WHITE, bold=False, align=PP_ALIGN.LEFT, space_after_pt=0, is_first=True
    )

    foot_right = add_rect(slide, 6.20, 7.14, 7.133, 0.36, fill_color=C_ENVISION_BLUE)
    add_paragraph(
        foot_right.text_frame,
        f"水系镁离子电池电解液多尺度模拟与振动光谱研究          {page_num} / {total_pages}",
        size_pt=10.5, color=C_WHITE, bold=True, align=PP_ALIGN.RIGHT, space_after_pt=0, is_first=True
    )


def build_template(output_paths, logo_dir):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    total_pages = 7

    logo_blue = os.path.join(logo_dir, "sues_logo_blue.png")
    logo_white = os.path.join(logo_dir, "sues_logo_white.png")
    watermark = os.path.join(logo_dir, "sues_mark_watermark.png")

    # =========================================================================
    # SLIDE 1: 封面页 (ZJU + SUES Beamer Classic Academic Cover with 2025 VI)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    if os.path.exists(watermark):
        s1.shapes.add_picture(watermark, Inches(9.80), Inches(3.20), height=Inches(3.65))

    # Top bar with white SUES logo (like ZJU Beamer cover)
    add_rect(s1, 0.0, 0.0, 13.333, 0.52, fill_color=C_EXPLORE_BLUE)
    if os.path.exists(logo_white):
        s1.shapes.add_picture(logo_white, Inches(10.95), Inches(0.09), height=Inches(0.34))

    # Left SUES 2025 Official Horizontal Logo on white canvas
    if os.path.exists(logo_blue):
        s1.shapes.add_picture(logo_blue, Inches(0.95), Inches(0.95), height=Inches(0.58))

    # Center-left Exploration Blue Banner for Main Title (classic ZJU/SUES Beamer cover banner)
    title_banner = add_rect(s1, 0.95, 1.90, 11.43, 2.05, fill_color=C_EXPLORE_BLUE)
    title_banner.text_frame.margin_left = Inches(0.35)
    title_banner.text_frame.margin_right = Inches(0.35)
    add_paragraph(
        title_banner.text_frame,
        "水系镁离子电池电解液溶剂化结构演化的多尺度模拟与振动光谱研究",
        size_pt=25, color=C_WHITE, bold=True, align=PP_ALIGN.LEFT, space_after_pt=10, is_first=True
    )
    add_paragraph(
        title_banner.text_frame,
        "—— 硕士学位论文开题 / 阶段进展汇报 (Multiscale Simulation & Vibrational Spectroscopy)",
        size_pt=14, color=C_NAV_MUTED, bold=False, align=PP_ALIGN.LEFT, space_after_pt=0
    )

    # Presenter & Advisor Metadata directly on white canvas (like ZJU/SUES Beamer)
    add_textbox(
        s1, 0.95, 4.35, 9.5, 2.20,
        text=(
            "汇 报 人：周 俊（硕士研究生）\n"
            "指导教师：XXX 教授\n"
            "所在学院：材料科学与工程学院 / 化学化工学院\n"
            "汇报日期：2026 年 11 月"
        ),
        size_pt=16, color=C_INK, line_spacing=1.42, space_after_pt=6
    )

    # Bottom two-tone footline
    f1_l = add_rect(s1, 0.0, 7.14, 6.20, 0.36, fill_color=C_EXPLORE_BLUE)
    add_paragraph(f1_l.text_frame, "上海工程技术大学 · SUES 2025 新版视觉形象系统", size_pt=10.5, color=C_WHITE, is_first=True)
    f1_r = add_rect(s1, 6.20, 7.14, 7.133, 0.36, fill_color=C_ENVISION_BLUE)
    add_paragraph(f1_r.text_frame, "研究生学术汇报模板          1 / 7", size_pt=10.5, color=C_WHITE, bold=True, align=PP_ALIGN.RIGHT, is_first=True)

    # =========================================================================
    # SLIDE 2: 目录与章节过渡页 (THU / SUES Beamer `show/shaded` TOC Style)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_zju_sues_chrome(s2, active_sec_idx=0, slide_title="汇报提纲 (Outline)", page_num=2, total_pages=total_pages, logo_dir=logo_dir)

    # Direct on white canvas — no gray card boxes! Active section highlighted, others clean
    tb_toc = add_textbox(s2, 1.15, 1.45, 10.5, 5.20)
    tf_toc = tb_toc.text_frame
    toc_items = [
        ("❶  01 课题背景与核心科学问题", "水系镁电界面脱溶剂化能垒瓶颈、阴离子竞争配位争议与研究切入点", True),
        ("❷  02 研究内容与多尺度模拟方案", "经典 MD + DFT + 机器学习力场 (MLFF) 跨尺度耦合与拉曼光谱计算", False),
        ("❸  03 阶段进展与核心数据发现", "第一溶剂化壳层重构规律、自由水活性调控与特征振动峰位移指认", False),
        ("❹  04 工作计划与预期学术成果", "后续自由能面计算排期、实验验证闭环及学位论文章节规划", False),
    ]
    for i, (head, sub, is_cur) in enumerate(toc_items):
        add_paragraph(
            tf_toc, head,
            size_pt=20, color=C_EXPLORE_BLUE if is_cur else C_INK,
            bold=True, space_after_pt=3, is_first=(i == 0)
        )
        add_paragraph(
            tf_toc, f"      {sub}",
            size_pt=14.5, color=C_ENVISION_BLUE if is_cur else C_MUTED,
            bold=False, space_after_pt=18
        )

    # =========================================================================
    # SLIDE 3: 课题背景与科学问题 (Direct White Canvas Left + Schematic Right)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_zju_sues_chrome(s3, active_sec_idx=0, slide_title="二价镁离子强水合作用受限与溶剂化调控思路", page_num=3, total_pages=total_pages, logo_dir=logo_dir)

    tb_l = add_textbox(s3, 0.65, 1.32, 5.65, 5.40)
    tf_l = tb_l.text_frame
    add_paragraph(tf_l, "❶ 高电荷密度引起强水合束缚", size_pt=17, color=C_EXPLORE_BLUE, bold=True, space_after_pt=4, is_first=True)
    add_paragraph(tf_l, "Mg²⁺ 第一水合壳层 [Mg(H₂O)₆]²⁺ 结合能高达 ~1900 kJ/mol，界面脱溶剂化动力学迟缓。", size_pt=14.5, color=C_INK, space_after_pt=16)
    add_paragraph(tf_l, "❷ 氢键网络与析氢副反应 (HER)", size_pt=17, color=C_EXPLORE_BLUE, bold=True, space_after_pt=4)
    add_paragraph(tf_l, "高活性自由水在负极表面优先还原析氢，限制电化学稳定窗口 (< 2.0 V)。", size_pt=14.5, color=C_INK, space_after_pt=16)
    add_paragraph(tf_l, "❸ 核心切入点：配位演化 — 光谱映射", size_pt=17, color=C_ENVISION_BLUE, bold=True, space_after_pt=4)
    add_paragraph(tf_l, "引入阴离子/共溶剂重构第一配位壳层，建立微观溶剂化构型与拉曼光谱的定量关系。", size_pt=14.5, color=C_INK, space_after_pt=0)

    # Right figure frame (thin cool-grey border on white canvas)
    fig_frame = add_rect(s3, 6.55, 1.32, 6.13, 5.30, fill_color=C_WHITE, line_color=C_COOL_GREY, line_pt=0.75)
    fig_frame.text_frame.vertical_anchor = MSO_ANCHOR.TOP
    add_paragraph(fig_frame.text_frame, "图 1  [Mg(H₂O)₆₋ₓAₓ] 溶剂化竞争配位与脱溶剂化机理图", size_pt=14, color=C_EXPLORE_BLUE, bold=True, space_after_pt=90, is_first=True)
    add_paragraph(fig_frame.text_frame, "[ 插入 300 DPI 科研机理示意图 ]", size_pt=14, color=C_MUTED, align=PP_ALIGN.CENTER, space_after_pt=0)

    # =========================================================================
    # SLIDE 4: 研究方法与多尺度路线 (Clean 3-Column Open Layout, Top Rule Only)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_zju_sues_chrome(s4, active_sec_idx=1, slide_title="DFT、经典 MD 与机器学习力场 (MLFF) 跨尺度框架", page_num=4, total_pages=total_pages, logo_dir=logo_dir)

    stages = [
        (
            "尺度一 · 电子结构计算 (DFT)",
            "• 团簇构型优化与结合能精确计算\n"
            "• 静电势 (ESP) 与自然键轨道电荷\n"
            "• 显式溶剂化振动频率与极化率\n"
            "• 构建高精度能量与原子力训练集"
        ),
        (
            "尺度二 · 介观动力学采样 (MLFF)",
            "• 主动学习训练机器学习势函数\n"
            "• 纳秒级大体系体相与界面采样\n"
            "• 径向分布函数 g(r) 与配位数统计\n"
            "• 伞形采样计算脱溶剂化自由能面"
        ),
        (
            "尺度三 · 光谱指认与实验闭环",
            "• 自相关函数计算红外/拉曼光谱\n"
            "• 解耦 SSIP / CIP / AGG 特征峰\n"
            "• 水分子 O–H 伸缩振动分峰拟合\n"
            "• 原位光谱与电化学窗口交叉验证"
        ),
    ]
    for idx, (st_title, st_body) in enumerate(stages):
        x = 0.65 + idx * 4.10
        # Top accent line only (no bulky box around the column!)
        add_rect(s4, x, 1.40, 3.83, 0.05, fill_color=C_EXPLORE_BLUE if idx != 1 else C_ENVISION_BLUE)
        tb_col = add_textbox(s4, x, 1.55, 3.83, 5.10)
        tf_col = tb_col.text_frame
        add_paragraph(
            tf_col, st_title,
            size_pt=16.5, color=C_EXPLORE_BLUE if idx != 1 else C_ENVISION_BLUE,
            bold=True, space_after_pt=14, is_first=True
        )
        for line in st_body.split("\n"):
            add_paragraph(tf_col, line, size_pt=14.5, color=C_INK, space_after_pt=10, line_spacing=1.35)

    # =========================================================================
    # SLIDE 5: 阶段进展与 LaTeX Booktabs 纯三线表 (SUES Beamer Page 25 Style)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_zju_sues_chrome(s5, active_sec_idx=2, slide_title="阴离子进入内溶剂化壳层显著降低脱溶剂化能垒", page_num=5, total_pages=total_pages, logo_dir=logo_dir)

    sample_plot = os.path.join(logo_dir, "sues_sample_rdf_plot.png")
    if os.path.exists(sample_plot):
        s5.shapes.add_picture(sample_plot, Inches(0.65), Inches(1.30), width=Inches(5.65))
    add_textbox(
        s5, 0.65, 5.95, 5.65, 0.55,
        text="图 2  Mg–O 径向分布函数 g(r) 与第一配位壳层截断半径",
        size_pt=13, color=C_EXPLORE_BLUE, bold=True, align=PP_ALIGN.CENTER
    )

    add_textbox(
        s5, 6.65, 1.30, 6.00, 0.48,
        text="表 1  不同电解液体系配位数与能垒对比",
        size_pt=14, color=C_EXPLORE_BLUE, bold=True, align=PP_ALIGN.CENTER
    )
    rows, cols = 5, 4
    tbl_shape = s5.shapes.add_table(rows, cols, Inches(6.65), Inches(1.85), Inches(6.00), Inches(3.15))
    tbl = tbl_shape.table
    col_widths = [1.70, 1.35, 1.40, 1.55]
    for c_idx, w_in in enumerate(col_widths):
        tbl.columns[c_idx].width = Inches(w_in)

    table_data = [
        ["电解液体系", "CN(Mg-Ow)", "CN(Mg-Oₐ)", "ΔG‡ (kJ/mol)"],
        ["0.5 M Mg(OTf)₂", "5.82", "0.18 (SSIP)", "78.4 ± 2.1"],
        ["2.0 M Mg(OTf)₂", "4.95", "1.05 (CIP)", "64.2 ± 1.8"],
        ["3.0 M + 共溶剂", "3.80", "1.65 (AGG)", "49.6 ± 1.5"],
        ["实验拉曼拟合", "3.92", "1.58 (AGG)", "48.1 (实测)"],
    ]
    for r_idx, row in enumerate(table_data):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.fill.solid()
            cell.fill.fore_color.rgb = C_WHITE
            # Authentic LaTeX booktabs rules: toprule (1.5pt), midrule (0.75pt), bottomrule (1.5pt)
            top_pt = 1.5 if r_idx == 0 else 0
            bot_pt = 0.75 if r_idx == 0 else (1.5 if r_idx == rows - 1 else 0)
            apply_booktabs_borders(cell, top_pt=top_pt, bottom_pt=bot_pt, color_hex="0A2F99")

            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT
            run = p.add_run()
            run.text = val
            set_run_font(
                run,
                size_pt=13.5,
                color=C_EXPLORE_BLUE if (r_idx == 0 or r_idx == 3) else C_INK,
                bold=(r_idx == 0 or r_idx == 3)
            )

    add_textbox(
        s5, 6.65, 5.25, 6.00, 1.25,
        text="• 结论：CIP/AGG 团簇使脱溶剂化能垒降低 36.7%，与原位拉曼位移吻合。",
        size_pt=14.5, color=C_EXPLORE_BLUE, bold=True, line_spacing=1.35
    )

    # =========================================================================
    # SLIDE 6: 下一步工作计划与排期 (SUES Beamer Page 28 Open Itemize Style)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_zju_sues_chrome(s6, active_sec_idx=3, slide_title="后续研究计划与预期学术成果", page_num=6, total_pages=total_pages, logo_dir=logo_dir)

    tb_plan = add_textbox(s6, 0.95, 1.50, 11.2, 5.10)
    tf_plan = tb_plan.text_frame
    milestones = [
        ("❶ 第一阶段（2026.11 – 2027.02）：多浓度梯度 AIMD 与机器学习势函数训练",
         "     完成主动学习迭代与体相输运性质（自扩散系数、离子电导率、粘度）标定。"),
        ("❷ 第二阶段（2027.03 – 2027.06）：电极/电解液界面双电层增强采样模拟",
         "     构建完整界面脱溶剂化自由能面 (PMF)，解析振动光谱分峰与配位态定量关系。"),
        ("❸ 第三阶段（2027.07 – 2027.12）：原位光谱实验对标与学位论文撰写",
         "     结合原位拉曼/红外光谱与电化学测试完成闭环验证，撰写 SCI 论文及硕士学位论文。"),
    ]
    for i, (m_title, m_desc) in enumerate(milestones):
        add_paragraph(
            tf_plan, m_title,
            size_pt=17.5, color=C_EXPLORE_BLUE if i < 2 else C_ENVISION_BLUE,
            bold=True, space_after_pt=4, is_first=(i == 0)
        )
        add_paragraph(
            tf_plan, m_desc,
            size_pt=15, color=C_INK, bold=False, space_after_pt=22
        )

    # =========================================================================
    # SLIDE 7: 致谢与问答页 (ZJU + SUES Beamer Closing Slide)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_zju_sues_chrome(s7, active_sec_idx=3, slide_title="致谢与提问 (Acknowledgments & Q&A)", page_num=7, total_pages=total_pages, logo_dir=logo_dir)

    if os.path.exists(logo_blue):
        s7.shapes.add_picture(logo_blue, Inches(4.45), Inches(2.05), height=Inches(0.68))

    add_textbox(
        s7, 1.0, 3.15, 11.33, 2.15,
        text="敬请各位专家、老师批评指正！\nThank You for Your Attention",
        size_pt=30, color=C_EXPLORE_BLUE, bold=True, align=PP_ALIGN.CENTER, line_spacing=1.38
    )

    for out_path in output_paths:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        prs.save(out_path)
        print(f"Saved SUES 2025 VI Academic Template -> {out_path}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_dir = os.path.abspath(os.path.join(script_dir, "..", "assets", "sues_2025_vi"))
    default_outputs = [
        os.path.join(logo_dir, "SUES_2025_Academic_Template.pptx"),
        "/Users/zhoujun/.cc-switch/skills/scientific-slides/assets/sues_2025_vi/SUES_2025_Academic_Template.pptx",
        "/Users/zhoujun/Documents/科研/01_开题报告/上海工程技术大学_2025新版VI_极简学术汇报模板.pptx",
    ]
    outputs = sys.argv[1:] if len(sys.argv) > 1 else default_outputs
    build_template(outputs, logo_dir)
