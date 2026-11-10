#!/usr/bin/env python3
"""
Build the official Shanghai University of Engineering Science (SUES / 上海工程技术大学)
2025 New Visual Identity (VI) Minimalist Academic Presentation Template (.pptx).

Official 2025 SUES VI Specification:
- Primary Color (探索蓝 Exploration Blue): #0A2F99 (RGB: 10, 47, 153 | PANTONE 2146C)
- Secondary Accent (展望蓝 Envision Blue): #2E74FF (RGB: 46, 116, 255 | PANTONE 2727C)
- Neutral Ink (标准黑 / 深灰黑):           #1B1B1B (RGB: 27, 27, 27)
- Muted Text (次要灰字):                   #595959 (RGB: 89, 89, 89)
- Cool Grey Rule (冷灰边框 PANTONE 427C):  #C7C7C7 (RGB: 199, 199, 199)
- Subtle Surface Tint (极浅冷灰底):        #F4F6FA (RGB: 244, 246, 250)
- Background (纯白背景):                   #FFFFFF (RGB: 255, 255, 255)
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
C_INK = RGBColor(27, 27, 27)               # #1B1B1B 正文深黑
C_MUTED = RGBColor(89, 89, 89)             # #595959 辅助灰字
C_COOL_GREY = RGBColor(199, 199, 199)      # #C7C7C7 官方冷灰线 (PANTONE 427C)
C_SURFACE = RGBColor(244, 246, 250)        # #F4F6FA 极浅蓝灰容器底色
C_WHITE = RGBColor(255, 255, 255)          # #FFFFFF 纯白

FONT_CN = "PingFang SC"
FONT_EN = "Arial"


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


def add_paragraph(tf, text, size_pt=15, color=C_INK, bold=False, align=PP_ALIGN.LEFT,
                  space_after_pt=6, line_spacing=1.28, is_first=False):
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
                bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.25):
    """Add a clean text box with generous height and consistent CJK/Latin fonts."""
    tb = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.06)
    tf.margin_right = Inches(0.06)
    tf.margin_top = Inches(0.05)
    tf.margin_bottom = Inches(0.05)
    if text:
        for i, line in enumerate(text.split("\n")):
            add_paragraph(
                tf, line, size_pt=size_pt, color=color, bold=bold,
                align=align, space_after_pt=4, line_spacing=line_spacing, is_first=(i == 0)
            )
    return tb


def add_rect(slide, left, top, width, height, fill_color=None, line_color=None, line_pt=0.75):
    """Add a sharp rectangular shape (no rounded corners) and return it."""
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
    sh.text_frame.vertical_anchor = MSO_ANCHOR.TOP
    sh.text_frame.margin_left = Inches(0.18)
    sh.text_frame.margin_right = Inches(0.18)
    sh.text_frame.margin_top = Inches(0.14)
    sh.text_frame.margin_bottom = Inches(0.14)
    return sh


def add_header_and_footer(slide, section_tag, slide_title, page_num, total_pages, logo_dir):
    """
    Minimalist SUES 2025 VI Academic Header & Footer (only 5 shapes total).
    """
    tb = slide.shapes.add_textbox(Inches(0.65), Inches(0.24), Inches(10.0), Inches(0.68))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p0 = tf.paragraphs[0]
    r_tag = p0.add_run()
    r_tag.text = f"{section_tag}  |  "
    set_run_font(r_tag, size_pt=13, color=C_ENVISION_BLUE, bold=True)

    r_title = p0.add_run()
    r_title.text = slide_title
    set_run_font(r_title, size_pt=21, color=C_EXPLORE_BLUE, bold=True)

    # Top-right SUES 2025 horizontal logo
    logo_blue = os.path.join(logo_dir, "sues_logo_blue.png")
    if os.path.exists(logo_blue):
        slide.shapes.add_picture(logo_blue, Inches(10.85), Inches(0.30), height=Inches(0.36))

    # Single clean header rule (Exploration Blue)
    add_rect(slide, 0.65, 0.96, 12.03, 0.02, fill_color=C_EXPLORE_BLUE)

    # Single footer rule + unified footer bar
    add_rect(slide, 0.65, 7.00, 12.03, 0.01, fill_color=C_COOL_GREY)
    add_textbox(
        slide, 0.65, 7.04, 12.03, 0.36,
        text=f"上海工程技术大学 · 2025 新版 VI 极简学术汇报模板                                                                                                    {page_num} / {total_pages}",
        size_pt=10.5, color=C_MUTED, align=PP_ALIGN.LEFT
    )


def build_template(output_paths, logo_dir):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]
    total_pages = 7

    logo_blue = os.path.join(logo_dir, "sues_logo_blue.png")
    mark_blue = os.path.join(logo_dir, "sues_mark_blue.png")

    # =========================================================================
    # SLIDE 1: 封面页 (SUES 2025 New VI Swiss-Modernist Academic Cover)
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    add_rect(s1, 0.0, 0.0, 0.26, 5.25, fill_color=C_EXPLORE_BLUE)
    add_rect(s1, 0.0, 5.25, 0.26, 2.25, fill_color=C_ENVISION_BLUE)

    if os.path.exists(logo_blue):
        s1.shapes.add_picture(logo_blue, Inches(0.85), Inches(0.65), height=Inches(0.62))

    # Main Title + Subtitle + Report Type in one clean typography frame
    tb1 = add_textbox(s1, 0.85, 1.85, 11.2, 2.75)
    tf1 = tb1.text_frame
    add_paragraph(tf1, "研究生开题 / 阶段进展汇报", size_pt=14, color=C_ENVISION_BLUE, bold=True, space_after_pt=10, is_first=True)
    add_paragraph(tf1, "水系镁离子电池电解液溶剂化结构演化的\n多尺度模拟与振动光谱研究", size_pt=31, color=C_EXPLORE_BLUE, bold=True, space_after_pt=12, line_spacing=1.22)
    add_paragraph(tf1, "Multiscale Simulation and Vibrational Spectroscopy of Aqueous Mg-Ion Electrolytes", size_pt=14, color=C_MUTED, space_after_pt=4)

    add_rect(s1, 0.85, 4.78, 11.6, 0.015, fill_color=C_COOL_GREY)

    add_textbox(
        s1, 0.85, 5.05, 10.2, 1.65,
        text=(
            "汇报人：周 俊（硕士研究生）          导   师：XXX 教授\n"
            "学   院：材料科学与工程学院          研究方向：计算电化学与分子动力学模拟\n"
            "汇报日期：2026 年 11 月"
        ),
        size_pt=15, color=C_INK, line_spacing=1.42
    )

    if os.path.exists(mark_blue):
        s1.shapes.add_picture(mark_blue, Inches(11.65), Inches(5.85), height=Inches(0.95))

    # =========================================================================
    # SLIDE 2: 目录页 (Agenda / 4-Part Academic Structure, <= 9 shapes)
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header_and_footer(s2, "CONTENTS", "汇报提纲与研究脉络", 1, total_pages, logo_dir)

    sections = [
        ("01  课题背景与核心科学问题", "水系镁电界面脱溶剂化能垒瓶颈、阴离子竞争配位争议与课题切入点"),
        ("02  研究内容与多尺度模拟方案", "经典 MD + DFT + 机器学习力场 (MLFF) 跨尺度耦合与拉曼光谱计算"),
        ("03  阶段进展与核心数据发现", "第一溶剂化壳层重构规律、自由水活性调控与特征振动峰位移指认"),
        ("04  工作计划与预期学术成果", "后续自由能面计算排期、实验验证闭环及学位论文章节规划"),
    ]
    for idx, (title, desc) in enumerate(sections):
        y = 1.32 + idx * 1.32
        box = add_rect(s2, 0.85, y, 11.6, 1.08, fill_color=C_SURFACE, line_color=C_COOL_GREY, line_pt=0.75)
        tf = box.text_frame
        add_paragraph(tf, title, size_pt=17, color=C_EXPLORE_BLUE, bold=True, space_after_pt=4, is_first=True)
        add_paragraph(tf, desc, size_pt=13.5, color=C_MUTED, space_after_pt=0)

    # =========================================================================
    # SLIDE 3: 课题背景与科学问题 (Two-Column Split: Left Points + Right Visual)
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header_and_footer(s3, "01 BACKGROUND", "二价镁离子强水合作用受限与溶剂化调控思路", 2, total_pages, logo_dir)

    left_box = add_rect(s3, 0.65, 1.25, 5.55, 5.45, fill_color=C_SURFACE, line_color=C_COOL_GREY, line_pt=0.75)
    tf_l = left_box.text_frame
    add_paragraph(tf_l, "1. 高电荷密度引起强水合束缚", size_pt=16, color=C_EXPLORE_BLUE, bold=True, space_after_pt=4, is_first=True)
    add_paragraph(tf_l, "Mg²⁺ 第一水合壳层 [Mg(H₂O)₆]²⁺ 结合能高 (~1900 kJ/mol)，界面脱溶剂化动力学迟缓。", size_pt=14, color=C_INK, space_after_pt=14)
    add_paragraph(tf_l, "2. 氢键网络与析氢副反应 (HER)", size_pt=16, color=C_EXPLORE_BLUE, bold=True, space_after_pt=4)
    add_paragraph(tf_l, "高活性自由水在负极表面优先还原析氢，限制电化学稳定窗口 (< 2.0 V)。", size_pt=14, color=C_INK, space_after_pt=14)
    add_paragraph(tf_l, "3. 课题切入点：配位演化 — 光谱映射", size_pt=16, color=C_ENVISION_BLUE, bold=True, space_after_pt=4)
    add_paragraph(tf_l, "引入阴离子/共溶剂重构第一配位壳层，建立微观溶剂化构型与拉曼光谱的定量关系。", size_pt=14, color=C_INK, space_after_pt=0)

    right_box = add_rect(s3, 6.45, 1.25, 6.23, 5.45, fill_color=C_WHITE, line_color=C_EXPLORE_BLUE, line_pt=1.0)
    tf_r = right_box.text_frame
    add_paragraph(tf_r, "图 1  [Mg(H₂O)₆₋ₓAₓ] 溶剂化壳层竞争配位与脱溶剂化机理图", size_pt=14, color=C_EXPLORE_BLUE, bold=True, space_after_pt=90, is_first=True)
    add_paragraph(tf_r, "[ 此处插入高分辨率科研机理图 / 溶剂化结构演化示意图 ]\n建议尺寸：1800 × 1200 px (300 DPI PNG/SVG)", size_pt=14, color=C_MUTED, align=PP_ALIGN.CENTER, space_after_pt=0)

    s3.notes_slide.notes_text_frame.text = (
        "详细讲解备注：二价 Mg2+ 离子半径仅 0.72 Å，表面电荷密度极高，导致水分子与其形成牢固的六配位八面体结构。"
        "传统经验力场忽略了电子极化效应，难以准确描述高浓度或混合溶剂下的阴离子配位竞争过程。"
    )

    # =========================================================================
    # SLIDE 4: 技术路线与多尺度方法 (3-Stage Horizontal Pipeline, <= 8 shapes)
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header_and_footer(s4, "02 METHODOLOGY", "DFT、经典 MD 与机器学习力场 (MLFF) 跨尺度框架", 3, total_pages, logo_dir)

    stages = [
        (
            "STAGE 01 · 电子结构 (DFT)",
            "• 团簇构型优化与结合能计算\n"
            "• 静电势与自然键轨道电荷分析\n"
            "• 显式溶剂化振动频率与极化率\n"
            "• 构建高精度能量/力训练集"
        ),
        (
            "STAGE 02 · 介观动力学 (MLFF)",
            "• 主动学习训练机器学习势函数\n"
            "• 纳秒级大体系体相与界面采样\n"
            "• 径向分布函数 g(r) 与配位数统计\n"
            "• 伞形采样计算脱溶剂化自由能面"
        ),
        (
            "STAGE 03 · 光谱指认与验证",
            "• 自相关函数计算红外/拉曼光谱\n"
            "• 解耦 SSIP / CIP / AGG 特征峰\n"
            "• 水分子 O–H 伸缩振动分峰拟合\n"
            "• 原位光谱与电化学窗口交叉验证"
        ),
    ]
    for idx, (st_title, st_body) in enumerate(stages):
        x = 0.65 + idx * 4.10
        card = add_rect(s4, x, 1.30, 3.83, 5.35, fill_color=C_SURFACE, line_color=C_EXPLORE_BLUE if idx != 1 else C_ENVISION_BLUE, line_pt=1.2)
        tf = card.text_frame
        add_paragraph(tf, st_title, size_pt=15.5, color=C_EXPLORE_BLUE if idx != 1 else C_ENVISION_BLUE, bold=True, space_after_pt=14, is_first=True)
        for line in st_body.split("\n"):
            add_paragraph(tf, line, size_pt=14, color=C_INK, space_after_pt=8, line_spacing=1.35)

    # =========================================================================
    # SLIDE 5: 阶段进展与三线表数据对标 (Plot Container + Standard Three-Line Table)
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header_and_footer(s5, "03 RESULTS", "阴离子进入内溶剂化壳层显著降低脱溶剂化能垒", 4, total_pages, logo_dir)

    plot_box = add_rect(s5, 0.65, 1.25, 5.80, 5.40, fill_color=C_WHITE, line_color=C_COOL_GREY, line_pt=0.75)
    tf_p = plot_box.text_frame
    add_paragraph(tf_p, "图 2  Mg–O 径向分布函数 g(r) 与配位数演化", size_pt=14, color=C_EXPLORE_BLUE, bold=True, space_after_pt=4, is_first=True)

    sample_plot = os.path.join(logo_dir, "sues_sample_rdf_plot.png")
    if os.path.exists(sample_plot):
        s5.shapes.add_picture(sample_plot, Inches(0.82), Inches(1.82), width=Inches(5.46))

    add_textbox(
        s5, 6.70, 1.25, 5.95, 0.50,
        text="表 1  不同电解液体系第一壳层配位数与能垒对比",
        size_pt=14, color=C_EXPLORE_BLUE, bold=True
    )
    rows, cols = 5, 4
    tbl_shape = s5.shapes.add_table(rows, cols, Inches(6.70), Inches(1.82), Inches(5.95), Inches(3.25))
    tbl = tbl_shape.table
    col_widths = [1.65, 1.35, 1.40, 1.55]
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
            cell.fill.fore_color.rgb = C_EXPLORE_BLUE if r_idx == 0 else (C_WHITE if r_idx % 2 == 1 else C_SURFACE)
            p = cell.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER if c_idx > 0 else PP_ALIGN.LEFT
            run = p.add_run()
            run.text = val
            set_run_font(
                run,
                size_pt=13.5,
                color=C_WHITE if r_idx == 0 else (C_EXPLORE_BLUE if r_idx == 3 else C_INK),
                bold=(r_idx == 0 or r_idx == 3)
            )

    add_textbox(
        s5, 6.70, 5.25, 5.95, 1.35,
        text="核心结论：形成 CIP/AGG 团簇后，Mg²⁺ 脱溶剂化能垒降低 36.7%，与原位拉曼位移定量吻合。",
        size_pt=14, color=C_EXPLORE_BLUE, bold=True, line_spacing=1.35
    )

    # =========================================================================
    # SLIDE 6: 下一步工作计划与排期 (Clean Milestones, <= 8 shapes)
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header_and_footer(s6, "04 WORK PLAN", "后续研究计划与预期学术成果", 5, total_pages, logo_dir)

    milestones = [
        ("阶段一 · 2026.11 – 2027.02  |  多浓度梯度 AIMD 与 MLFF 势函数训练", "完成主动学习迭代与体相输运性质（自扩散系数、离子电导率、粘度）标定。"),
        ("阶段二 · 2027.03 – 2027.06  |  电极/电解液界面双电层增强采样模拟", "构建完整界面脱溶剂化自由能面 (PMF)，解析振动光谱分峰与配位态定量关系。"),
        ("阶段三 · 2027.07 – 2027.12  |  原位光谱实验对标与学位论文撰写", "结合原位拉曼/红外光谱与电化学测试完成闭环验证，撰写 SCI 论文及学位论文。"),
    ]
    for idx, (m_title, m_desc) in enumerate(milestones):
        y = 1.40 + idx * 1.72
        box = add_rect(s6, 0.65, y, 12.03, 1.42, fill_color=C_SURFACE, line_color=C_EXPLORE_BLUE if idx < 2 else C_ENVISION_BLUE, line_pt=1.0)
        tf = box.text_frame
        add_paragraph(tf, m_title, size_pt=16, color=C_EXPLORE_BLUE if idx < 2 else C_ENVISION_BLUE, bold=True, space_after_pt=6, is_first=True)
        add_paragraph(tf, m_desc, size_pt=14.5, color=C_INK, space_after_pt=0)

    # =========================================================================
    # SLIDE 7: 致谢页 (Closing & Q&A)
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_rect(s7, 0.0, 0.0, 0.26, 5.25, fill_color=C_EXPLORE_BLUE)
    add_rect(s7, 0.0, 5.25, 0.26, 2.25, fill_color=C_ENVISION_BLUE)

    if os.path.exists(logo_blue):
        s7.shapes.add_picture(logo_blue, Inches(0.85), Inches(0.70), height=Inches(0.62))

    add_textbox(
        s7, 0.85, 2.35, 11.0, 2.15,
        text="敬请各位专家、老师批评指正！\nThank You for Your Attention · Questions & Discussion",
        size_pt=32, color=C_EXPLORE_BLUE, bold=True, line_spacing=1.35
    )
    add_rect(s7, 0.85, 4.65, 11.6, 0.015, fill_color=C_COOL_GREY)
    add_textbox(
        s7, 0.85, 4.95, 9.5, 1.25,
        text="汇报人：周 俊   |   上海工程技术大学 (Shanghai University of Engineering Science)\n三旋翼交叉创新 · 探索蓝 (#0A2F99) & 展望蓝 (#2E74FF) 2025 新版视觉形象识别系统",
        size_pt=14, color=C_MUTED, line_spacing=1.45
    )
    if os.path.exists(mark_blue):
        s7.shapes.add_picture(mark_blue, Inches(11.65), Inches(5.85), height=Inches(0.95))

    for out_path in output_paths:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        prs.save(out_path)
        print(f"Saved SUES 2025 VI Academic Template -> {out_path}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    logo_dir = os.path.abspath(os.path.join(script_dir, "..", "assets", "sues_2025_vi"))
    default_outputs = [
        os.path.join(logo_dir, "SUES_2025_Academic_Template.pptx"),
        "/Users/zhoujun/Documents/科研/01_开题报告/上海工程技术大学_2025新版VI_极简学术汇报模板.pptx",
    ]
    outputs = sys.argv[1:] if len(sys.argv) > 1 else default_outputs
    build_template(outputs, logo_dir)
