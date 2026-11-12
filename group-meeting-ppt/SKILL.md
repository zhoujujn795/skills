---
name: group-meeting-ppt
description: "Minimalist, zero-clutter academic weekly group/lab meeting (组会周报 / Weekly Progress), literature review (文献精读 / Journal Club), and experimental troubleshooting (踩坑排雷讨论) PowerPoint (.pptx) skill. Trigger whenever the user asks to create or update a weekly research progress deck, lab meeting slides, journal club report, failure/ablation discussion slides, or explicitly wants a clean minimalist academic PPT without university logos, institutional banners, or AI-card clutter. Do NOT use for formal thesis defenses, opening reports (开题/中期/答辩), or official university-branded VI templates — use `scientific-slides` or `pptx` (`build_sues_2025_template.py`) for those."
license: MIT
---

# Minimalist Weekly Group Meeting & Journal Club PPT Skill (`group-meeting-ppt`)

专为**课题组日常高频组会（Weekly Group / Lab Meeting）**、**文献精读（Journal Club）**与**阶段实验排雷讨论**打造的极简原生可编辑 `.pptx` 生成体系。砍掉全部仪式性礼仪边框与水页，将 **~80% 垂直画布高度** 100% 让渡给高信息密度的定量图表、原生三线表与导师拍板讨论。

---

## 一、与正式答辩类 Skills 的职责边界

| 维度 | 高校正式答辩风 (`scientific-slides` / `SUES 2025 VI`) | 本 Skill：日常组会极简风 (`group-meeting-ppt`) |
|---|---|---|
| **典型场景** | 开题报告、中期考核、硕博学位论文答辩、对外大会报告 | **每周科研进展汇报、文献精读 JC、负结果/跑崩实验排雷** |
| **页面外框 (Chrome)** | 顶栏章节导航条 + 校徽 + 右下徽标水印 + 底部双色状态栏 | **纯白画布 `#FFFFFF` 零制度装饰**：无校徽、无水印、无顶底横幅 |
| **首尾页结构** | 大色块封面 + 独立 `Outline` 页 + 独立 `Thank You` 致谢页 | **零礼仪水页**：首页直出 `TL;DR` 三句话摘要；尾页常驻「下周排期 + 需导师拍板问题」 |
| **叙事重心** | 宏大背景 → 文献综述 → 完整方法体系 → 正向成果总结 | **增量与问题导向**：上周核销 → Baseline 对照增量 → **踩坑排雷根因** → 分岔口拍板 |

---

## 二、五大核心设计纪律（融合学术叙事与反 AI 味准则）

1. **Ghost Deck Test（幽灵大纲测试）**
   - 仅按顺序提取全片 `Slide 1..N` 的顶部标题（Action Title），不看任何图片与正文，必须能连贯读出完整论证链：`本周全貌 → 核心定量突破 → 前后对照增益 → 跨条件鲁棒性 → 异常排雷闭环 → 基准对标 → 下周拍板项`。
   - **严禁主题词标题**（如 ❌ *“本周实验结果（一）”*、❌ *“拉曼光谱分析”*）；必须是 **1–2 行完整结论陈述句**（如 ✅ *“引入 O4 短程排斥修正后，4 M 测试集力 RMSE 降至 28.4 meV/Å”*）。
2. **Exhibit Discipline（展品纪律）**
   - 一页仅承载 **1 个核心视觉证据**（单主图、对称双对照图、同构 `2×2` 矩阵或左图右表）。
   - 关键增量必须在图内直接给出 1 处指针微注（如 `-81% short-range error`），并在文字中用 `{{...}}` 标出关键数值，拒绝二级项目符号废话墙。
3. **Anti-AI-Slop 减法母版铁律**
   - 全篇统一纯白底 `#FFFFFF`；左右安全边距 `0.65"`（内容宽 `12.03"`），页面开放留白 `≥ 45%`，单页形状总数控制在 **`4–10` 个**（硬上限 `≤ 14`），单页总字数 **`≤ 320` 字**（算例路径、泛函参数与推导细节一律写入 `Speaker Notes`）。
   - **严禁**：圆角灰底卡片堆叠、彩色编号胶囊徽章、均分三栏空洞套话、底部感叹号警告横幅。
4. **单主色 + 唯一语义强调色（`MAX_CHROMATIC_HUES <= 2`）**
   - **主色 Primary Slate Navy (`#1E3A5F`)**：Action Title、栏小标题、Booktabs 三线表顶底线、本周主方法曲线。
   - **唯一强调色 Semantic Accent (`#C2410C` 焦糖深橙)**：每页至多点睛 1–2 处，专用于「关键增益数值 / 崩溃根因 / 待导师拍板分岔」。
   - **冷灰中性阶**：正文炭黑 `#1F2937`、对照组深灰 `#475569` / 浅灰虚线 `#94A3B8`、图注与页码 `#6B7280`、极细分割线 `#D1D5DB` (`0.5 pt`)。
5. **跨平台双端零错位字体绑定**
   - 西文与数字统一 `Arial`，中文显式写入 DrawingML `<a:ea typeface="Microsoft YaHei"/>`（Windows / macOS 双端原生安全，严格遵守 `<a:rPr>` 中 `solidFill → latin → ea` 的 XSD 顺序）。
   - 字号铁律：Action Title `24.5 pt Bold`（满足 `layout_audit.py` `>= 24pt` 门禁）；栏标题 `16–16.5 pt Bold`；正文要点 `14.5–15.5 pt`；三线表单元格 `13.0 pt`；图注 `12.0 pt`（主画布区严禁 `< 12 pt`）；仅底部 `y = 6.98"` 极简页码可用 `10.5 pt`。

---

## 三、`L1`–`L7` 七大固定坐标版式规格（`13.333" × 7.500"`）

所有版式均封装于 [`scripts/group_meeting_builder.py`](scripts/group_meeting_builder.py) 的 `GroupMeetingDeck` 类中（文本内支持 `{{重点橙色加粗}}` 与 `**深海蓝加粗**` 行内标记）：

| 版式代号 | 方法签名 | 适用场景 | 固定几何槽位契约 (`x, y, w, h` 英寸) |
|---|---|---|---|
| **`L1`** | `add_l1_cover_tldr()` | **极简周报首页 + 本周 TL;DR**：开场 30 秒交代全貌，取代封面+目录 | 顶部日期微标 `(0.65, 0.75)` → 主标题 `27pt Bold` `(0.65, 1.18)` → 汇报人 `(0.65, 2.24)` → `y=2.78"` 细线 → 下半区无框 3 条 `[进展]` / `[发现]` / `[待拍板]` |
| **`L2`** | `add_l2_hero_figure(mode="split"\|"wide")` | **一页一结论核心主图页**：机理图、对偶误差图、宽幅谱图/时间序列 | `split`：左图 `(0.65, 1.16, 7.45, 5.00)` + 图注 `(0.65, 6.26, 7.45, 0.56)` + 右栏 3 条解读 `(8.40, 1.24, 4.28, 5.36)`<br>`wide`：上图 `(0.65, 1.16, 12.03, 4.55)` + 下结论 `(0.65, 5.82, 12.03, 1.04)` |
| **`L3`** | `add_l3_dual_comparison()` | **Baseline vs. 本周改进 A/B 对照页**：力场修正前后、实验 vs 模拟 | 左槽 `(0.65, 1.54, 5.80, 4.35)` + 右槽 `(6.88, 1.54, 5.80, 4.35)`（**双独立 `<asvg:svgBlip>`，强制锁定相同 `ylim`**）+ 底部贯穿增量条 `(0.65, 6.10, 12.03, 0.72)` |
| **`L4`** | `add_l4_grid_2x2(mode="C1"\|"C2")` | **2×2 消融 / 浓度或温度演化矩阵页** | `C1`（首选同构共享轴）：左单张 `2×2` SVG `(0.65, 1.16, 8.20, 5.45)` + 右侧规律栏 `(9.10, 1.24, 3.58, 5.30)`<br>`C2`（异构四图）：4 个独立 `5.85"×2.68"` SVG 槽，子标题绘入 SVG 内 |
| **`L5`** | `add_l5_troubleshooting()` | **踩坑排雷与负结果诊断页**：跑崩轨迹、发散曲线、反常负结果排查 | 左异常复现图 `(0.65, 1.20, 5.55, 5.00)` + `x=6.46"` 竖向细导引线 + 右侧三段排雷流 `(6.65, 1.22, 6.03, 5.48)`：`① 异常现象` → `② 根因定位 (#C2410C)` → `③ 修复与验证` |
| **`L6`** | `add_l6_booktabs_table(mode="split"\|"full")` | **原生 LaTeX Booktabs 三线表基准页**（严禁截图贴表，严禁同列上下叠放大图与多行表） | `split`：左图 `(0.65, 1.20, 5.85, 5.00)` + 右表题 `(6.80, 1.18)` + 原生 `<a:tbl>` `(6.80, 1.65, 5.88, <=2.40)`（**硬约束 `rows <= 6, cols <= 5`**）+ 表下结论 `(6.80, 5.18, 5.88, 1.45)`，留足 `> 0.70"` 防膨胀安全缓冲 |
| **`L7`** | `add_l7_plan_and_decisions()` | **常驻尾页：上周闭环 + 下周排期 + 需导师拍板问题**（取代 Thank You 页） | 左栏 `(0.65, 1.24, 7.25, 5.42)`：`✓ 已核销` + 2–3 项带具体节点任务；`x=8.14"` 强调色竖线；右栏 `(8.35, 1.24, 4.33, 5.42)`：1–2 个技术分岔口及倾向方案 A/B 利弊 |

---

## 四、`tueplots` 式 1:1 槽位绘图契约与 `<asvg:svgBlip>` 零乱码嵌入

### 1. Slot-Driven 1:1 原寸绘图（拒绝缩放字号失真）
绘图脚本直接从 `SLIDE_SLOT_SIZES` 读取目标插槽英寸尺寸作为 `figsize`，配合 `apply_slide_minimal_style()`（`axes.labelsize=11.5`, `xtick/ytick=10.5`, `legend=10.0`, `mathtext.fontset="custom"` `Arial`），确保图像以 **100% 原始比例** 贴入幻灯片：

| 插槽键名 (`SLIDE_SLOT_SIZES`) | 物理英寸尺寸 `(w_in, h_in)` | 对应版式槽位 |
|---|---|---|
| `"L2_wide"` | `(12.03, 4.55)` | `L2` 宽幅谱图/时间序列上槽 |
| `"L2_split"` / `"L2_split_nocap"` | `(7.45, 5.00)` / `(7.45, 5.45)` | `L2` 左图右结论主槽（含/不含图注） |
| `"L3_dual"` | `(5.80, 4.35)` | `L3` 左右对称双对照单槽 |
| `"L4_c1_grid"` | `(8.20, 5.45)` | `L4-C1` 共享坐标轴 `2×2` 矩阵槽 |
| `"L4_c2_cell"` | `(5.85, 2.68)` | `L4-C2` 独立四宫格单格槽 |
| `"L5_diag"` | `(5.55, 5.00)` | `L5` 左侧异常复现/排雷曲线槽 |
| `"L6_left_fig"` | `(5.85, 5.00)` | `L6-split` 左图右三线表配图槽 |

### 2. 双轨 `<asvg:svgBlip>` 零乱码矢量流水线
`save_slide_svg_and_png(fig, out_stem)` 自动串联同级 `../electrolyte-raman-mlff/scripts/ppt_origin_export.py`（若独立运行则自动启用内置无依赖 fallback）：
1. **数据预裁剪**：绘图期调用 `clip_curve_to_box()` / `clip_scatter_to_box()` 将数据严格裁剪至坐标轴框内。
2. **SVG 展平净化 (`sanitize_svg_for_ppt`)**：按 `x` 坐标重排 Matplotlib 公式 `<tspan>` 并合并展平为 **0 个 `<tspan>`** 的独立 `<text>`，归一化 `Arial.ttf` 缺失数学符号（`\u2212 -> '-'` 等），剥离全部 `<clipPath>` 黑色遮罩块。
3. **兼容性硬断言 (`audit_svg_ppt_compatibility`)**：强制验证 `tspan_count == 0`、`clip_path_count == 0`、`bad_fonts == []`、`missing_arial_glyphs == []`。
4. **双轨矢量注入 (`add_editable_svg_picture` + `ensure_svg_content_type`)**：在单个 `<p:pic>` 节点内同时挂载 `450 DPI .png` 兜底位图与 `{96DAC541-7B7A-43D3-8B79-37D633B846F1}` `<asvg:svgBlip>` 原生矢量，并在 `[Content_Types].xml` 幂等注册 `Extension="svg"`。用户在 PowerPoint 中右键 **「转换为形状 (Convert to Shape)」** 即可一键无损解组编辑，且单张图仅消耗 `1` 个形状配额。

---

## 五、标准构建代码示例与 CLI

### 1. 一键运行 7 页完整科研组会样片 (`L1`–`L7`)
```bash
python3 <skill_dir>/scripts/group_meeting_builder.py --demo /path/to/output_dir
```

### 2. 在自定义周报脚本中复用 `GroupMeetingDeck`
```python
from pathlib import Path
import matplotlib.pyplot as plt
import sys

sys.path.insert(0, "<skill_dir>/scripts")
from group_meeting_builder import (
    SLIDE_SLOT_SIZES,
    PALETTE_HEX,
    GroupMeetingDeck,
    apply_slide_minimal_style,
    clip_curve_to_box,
    save_slide_svg_and_png,
)

out_dir = Path("./weekly_20261112")
with apply_slide_minimal_style(boxed_inward=True):
    fig, ax = plt.subplots(figsize=SLIDE_SLOT_SIZES["L2_split"], layout="constrained")
    ax.plot([0, 1, 2], [0.42, 0.19, 0.08], "o-", color=PALETTE_HEX["primary"], label="This Week")
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Force RMSE (eV/Å)")
    svg_p, png_p, _ = save_slide_svg_and_png(fig, out_dir / "figures" / "hero")

deck = GroupMeetingDeck(project_tag="Project · 组会周报")
deck.add_l1_cover_tldr(
    date_label="2026-11-12 · Weekly Group Meeting",
    title="主动学习迭代收敛报告",
    presenter_line="汇报人：姓名 | 课题组",
    tldr_items=[("进展", "完成第 2 轮采样"), ("发现", "RMSE 降至 {{0.08 eV/Å}}"), ("待拍板", "下周体系优先级")],
)
deck.add_l2_hero_figure(
    action_title="两轮主动学习后测试集力误差下降 {{81%}}",
    svg_path=svg_p,
    png_path=png_p,
    takeaways=["**收敛速率**：第 2 轮即达 {{0.08 eV/Å}}。", "**泛化表现**：高温轨迹零发散。"],
    caption="Fig. 1 | 主动学习轮次与测试集力 RMSE 关系（n=200）。",
    notes="详细超参与数据路径写在此处 Speaker Notes。",
)
pptx_file = deck.save(out_dir / "Weekly_Report.pptx")
deck.write_verify_checklist(
    out_dir / "verify_checklist.md",
    pptx_path=pptx_file,
    data_provenance=[("Slide 2 (`L2`)", "`figsize=(7.45, 5.00)`", "`n=200` 独立测试集")],
    advisor_qa=[("为什么第 2 轮误差下降最快？", "首轮精准补齐了近程排斥高梯度区样本。")],
)
```

---

## 六、强制交付双门禁与配套清单（Delivery Gate）

每次生成或修改 `.pptx` 后，**必须依次通过以下全部门禁方可交付**：

1. **版面溢出、色相、字体与三线表防碰撞审计（必须 `exit 0` 且零 `[FAIL]`）**：
   ```bash
   python3 ../pptx/scripts/layout_audit.py path/to/deck.pptx
   ```
2. **OOXML XSD Schema、关系引用与母版主题合法性校验（必须 `All validations PASSED!`）**：
   ```bash
   python3 ../pptx/scripts/office/validate.py -v path/to/deck.pptx
   ```
3. **图表视觉回看巡检**：直接检视 `figures/*.png`（若环境安装了 LibreOffice，额外执行 `soffice.py --headless --convert-to pdf` + `pdftoppm -png -r 150` 查看整页合成图），确认无图例压线、无箭头指空、双图 `ylim` 一致。
4. **配套交付 `verify_checklist.md`**：与 `.pptx` 同目录输出，必须包含 **Ghost Deck 标题链与预计口头时长**、**数据/样本量/误差棒定义溯源表**，以及 **3–5 个导师高频追问预判与定量应答**。

---

## 七、参考生态指南

- 开源学术 PPTX Skills、AI 科研绘图 Skills 与 Python 尺寸控制库（`tueplots`、`SciencePlots`、`UltraPlot`、`svg_utils` 等）完整对照见 [`references/open_source_ecosystem.md`](references/open_source_ecosystem.md)。
