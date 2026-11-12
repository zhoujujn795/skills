# 开源 PPTX 学术组会与科研绘图生态对照指南 (`open_source_ecosystem.md`)

本文档系统整理经 GitHub 实测核验的优秀开源 **PPTX / 学术组会 Skills**、**AI 科研绘图 Skills** 及 **Python 尺寸驱动绘图库**，明确各项目的技术路线、核心亮点，以及如何与本 `group-meeting-ppt` Skill 协同配合。

---

## 一、开源 PPTX 与学术组会 Skills 矩阵

| 项目 / 仓库 | GitHub 链接与社区热度 | 技术路线 | 核心设计亮点 | 与 `group-meeting-ppt` 的协同方式 |
|---|---|---|---|---|
| **1. `anthropics/skills` (`skills/pptx`)** | <https://github.com/anthropics/skills/tree/main/skills/pptx> | `PptxGenJS` + OOXML 解包 (`defusedxml`) | 工业级底层基建：`markitdown` 文本抽取、`thumbnail.py` 缩略图选版、`add_slide.py`/`clean.py` 安全复制清理、`office/validate.py` OOXML XSD 校验、`soffice + pdftoppm` 视觉巡检。 | 本 Skill 直接调用本地同源 `../pptx/scripts/office/validate.py` 与 `../pptx/scripts/layout_audit.py` 作为强制交付双门禁。 |
| **2. `Gabberflast/academic-pptx-skill`** | <https://github.com/Gabberflast/academic-pptx-skill> (★1,507) | 构建在 `pptx` 之上的学术叙事与排版纪律层 | ① **Ghost Deck Test（幽灵大纲测试）**：仅串联所有页面的 Action Title 即构成完整逻辑链；② **Exhibit Discipline（展品纪律）**：一页仅一个核心视觉证据 + 直接 Call-out 标注增量；③ 纯白底单字体靠字重/字号分层。 | 已内化为 `GroupMeetingDeck.ghost_deck_lines()` 与 `L2`–`L6` 的一页一结论硬约束。 |
| **3. `Zero-stargazer/group-meeting-ppt-skill`** | <https://github.com/Zero-stargazer/group-meeting-ppt-skill> | Python + `deck-spec.json` + 子图裁剪管线 | 中文课题组组会/Journal Club 专精：按「证据链 + 每页 `estimated_seconds`」动态组织页数；预裁剪文献子图（严禁残留 PDF 正文段落）；强制配套交付 `verify_checklist.md`（数据溯源 + **导师高频追问清单**）。 | 已内化为 `SlideRecord.estimated_seconds` 时长预算与 `write_verify_checklist()` 强制配套产物。 |
| **4. `K-Dense-AI/scientific-agent-skills` (`scientific-slides`)** | <https://github.com/K-Dense-AI/scientific-agent-skills> (★56.8k) | `PptxGenJS` / `python-pptx` / LaTeX Beamer | 完整科研演讲类型学（Conference / Seminar / Defense / Journal Club）、`fitImage()` 严格保长宽比几何居中、真实文献核验红线（零编造引用）。 | 正式答辩/对外大会用 `scientific-slides`；日常无校徽高频组会/文献精读用本 `group-meeting-ppt`。 |
| **5. `zLanqing/codex-claude-academic-skills`** | <https://github.com/zLanqing/codex-claude-academic-skills> (★5,894) | Python 科研仿真绘图 + `office-academic-skill` | 中文科研闭环范式：上游 `scientific-toolkit-skill` 产出标准尺寸数据图 → 下游学术 PPT 槽位直贴。 | 启发本 Skill 建立 `SLIDE_SLOT_SIZES` 1:1 槽位尺寸契约，无缝承接上游 Python 绘图脚本。 |
| **6. `icip-cas/PPTAgent`** | <https://github.com/icip-cas/PPTAgent> (★5,241, EMNLP'25) | 两阶段编辑生成 + 多模态 VLM 视觉审阅闭环 | **Reflective Generation**：代码生成 PPTX 后必须渲染为图像，交由视觉模型执行重叠、溢出、对比度多轮自检。 | 对应本工作流的渲染看图自检（`PNG` 原图巡检 + LibreOffice PDF/PNG 页面回看）。 |
| **7. `GordenSun/GordenPPTSkill` & `zouchenzhen/thesis-defense-pptx-skill`** | <https://github.com/GordenSun/GordenPPTSkill> (★4,065)<br><https://github.com/zouchenzhen/thesis-defense-pptx-skill> (★281) | `python-pptx` + 结构化 JSON 槽位注入 | 固定母版非破坏性 `run` 级文本替换与残留占位词扫描，杜绝直接覆盖 `text_frame.text` 导致样式丢失。 | 当用户明确要求套用课题组既有 `.pptx` 模板时，采用 OOXML/槽位级非破坏编辑；新建极简组会则走 `GroupMeetingDeck`。 |
| **8. `addsumtech/slides_maker`** | <https://github.com/addsumtech/slides_maker> (★662) | 代码/论文/实验记录 → 可复现脚本 + `.pptx` | 同时保留生成脚本与 `.pptx`，方便组会前 5 分钟重跑新实验曲线自动更新整套幻灯片。 | 推荐每次组会保留一个 `build_weekly_YYYYMMDD.py` 调用 `GroupMeetingDeck`，改数即可一键重出片。 |
| **9. `brycewang-stanford/many-ppt-skills`** | <https://github.com/brycewang-stanford/many-ppt-skills> (227 Skills 横评) | 提炼 30+ 团队独立收敛的 **8 条黄金原则** | **Principle 2 (Anti-AI-Slop)**：用明确减法禁令消除 AI 味（禁卡片堆叠、禁彩色胶囊、禁均分三栏套话）；**Principle 4 (Constraint Beats Freedom)**：锁死单套色板与 6–8 个固定坐标版式远胜自由发挥。 | 本 Skill 严格锁定 `#1E3A5F + #C2410C` 双色相与 `L1`–`L7` 七大固定坐标网格，单页形状数 `4–10` 个。 |
| **10. `hplgit/MAlley-slide-templates`** | <https://github.com/hplgit/MAlley-slide-templates> | Prof. Michael Alley (Penn State) **Assertion-Evidence** 范式 | 认知负荷实证最优结构：顶部 `21–25 pt` 完整陈述句结论标题（≤2 行）+ 下方纯视觉证据区（拒绝二级项目符号墙）+ 图内微注指针。 | 本 Skill `L2`–`L6` 全部强制采用 Assertion-Evidence 句式标题，严禁写 *“本周实验结果（一）”* 等主题词标题。 |

---

## 二、AI 科研绘图与机理示意图开源生态

| 项目 / 仓库 | GitHub 链接与热度 | 核心能力与可吸收方法论 | 与 `group-meeting-ppt` 配合建议 |
|---|---|---|---|
| **1. `K-Dense-AI/scientific-agent-skills` (`scientific-visualization` / `scientific-schematics`)** | <https://github.com/K-Dense-AI/scientific-agent-skills> (★56,850) | 数据真实性红线（严禁平滑/截断掩盖离群点，强制声明 SD/SE/95%CI 与样本量 $n$）、局部 `rc_context` 样式预设、WCAG 对比度与灰度可分性审计。 | 复杂多面板统计图或矢量机理框图可先参考本地 `../scientific-visualization/` 与 `../scientific-schematics/scripts/check_svg.py`，再经 `save_slide_svg_and_png()` 入库。 |
| **2. `dwzhu-pku/PaperBanana` & `PlutoLei/paperbanana-skill`** | <https://github.com/dwzhu-pku/PaperBanana> (★7,625)<br><https://github.com/PlutoLei/paperbanana-skill> | 多智能体协作流（Retriever → Planner → Stylist → Visualizer → Critic），其 **Stylist + Critic 视觉复盘检查单**专治图例压线、标签穿线与视觉重心失衡。 | 组会出图后执行 Critic 四问：图例是否遮挡峰值？箭头是否精准指在曲线特征点？左右对照图 `ylim` 是否统一？色相是否 `<= 2`？ |
| **3. `ResearAI/AutoFigure` & `AutoFigure-Edit`** | <https://github.com/ResearAI/AutoFigure> (★1,951)<br><https://github.com/ResearAI/AutoFigure-Edit> | 将算法/实验流程拆解为按语义分层（`<g id="module_a">`）的可编辑科研机理 SVG。 | 手写或生成的分层流程 SVG 经过 `sanitize_svg_for_ppt()` 展平 `<tspan>` 后嵌入 `L2` 槽位，导师在 PPT 中右键「转换为形状」即可单独拖动各模块。 |
| **4. `thunlp/MatPlotAgent`** | <https://github.com/thunlp/MatPlotAgent> (★120) | 代码绘图 + **渲染后多模态视觉反馈（Visual Feedback Loop）**，自动修复子图标题重叠与坐标轴截断。 | 每次调用 `save_slide_svg_and_png()` 后直接读取导出的 `450 DPI .png` 进行肉眼/多模态核查，确认无误再拼装 `.pptx`。 |

---

## 三、Python 精准尺寸控制与顶刊科研绘图工具库

1. **`pnkraemer/tueplots`**（★759，<https://github.com/pnkraemer/tueplots>）—— **本 Skill 绘图契约核心思想来源**
   - **核心机制**：**Slot-Size-Driven（目标槽位尺寸驱动）** 计算 `figsize` 与绝对字号。画布宽高直接等于目标版面插槽英寸宽高，以 **100% 原始比例**嵌入，彻底根治“同页两张图因缩放比不同导致坐标轴字号忽大忽小”。
   - **在本 Skill 中的实现**：`scripts/group_meeting_builder.py` 内置 `SLIDE_SLOT_SIZES`（如 `L2_split=(7.45, 5.00)`、`L3_dual=(5.80, 4.35)`、`L4_c1_grid=(8.20, 5.45)`）与 `apply_slide_minimal_style()`。
2. **`garrettj403/SciencePlots`**（★9,397，<https://github.com/garrettj403/SciencePlots>）
   - **特点与避坑**：经典 `.mplstyle` 集合（`science`, `nature`, `ieee`）。**注意**：嵌入 PowerPoint 时严禁开启 `usetex=True`（LaTeX Type-3 / `cm*` 字体进 PPT 必变乱码方块），必须使用本 Skill `slide_minimal` 的 `mathtext.fontset="custom"` (`Arial`) + `sanitize_svg_for_ppt()`。
3. **`Ultraplot/UltraPlot`**（★347，<https://github.com/Ultraplot/UltraPlot>，`proplot` 的 Matplotlib 3.9+ 继任者）
   - **配合场景**：极适合 `L4-C1` 四宫格消融/多浓度矩阵图，一行代码自动共享坐标轴、外置 Colorbar 并标注 `(a)(b)(c)(d)`。
4. **`ponnhide/patchworklib`**（★435，<https://github.com/ponnhide/patchworklib>）& **`btel/svg_utils`**（★339，<https://github.com/btel/svg_utils>）& **`FlyRanch/figurefirst`**（★90，<https://github.com/FlyRanch/figurefirst>）
   - **配合场景**：需在 `L2` 槽位内组合非对称异构子图（如左侧 3D 分子团簇 SVG + 右侧能垒曲线 SVG）时，用 `svg_utils` 在纯矢量层拼合后再调用 `sanitize_svg_for_ppt()`。
5. **色彩与统计显著性增强库**：
   - **`callumrollo/cmcrameri`**（★238，<https://github.com/callumrollo/cmcrameri>）：感知均匀科研色图（`batlow`, `vik`, `roma`），适合 2D 自由能面与光谱热图。
   - **`trevismd/statannotations`**（★865，<https://github.com/trevismd/statannotations>）：在组会柱状图/箱线图上自动添加无碰撞 `* / ** / p` 统计显著性括号。
   - **`Marsilea-viz/marsilea`**（★331，<https://github.com/Marsilea-viz/marsilea>）：声明式组合聚类热图。
   - **`rgerum/pylustrator`**（★905，<https://github.com/rgerum/pylustrator>）：交互微调排版后自动将坐标改动写回可复现 Python 脚本。

---

## 四、为什么坚持 `<asvg:svgBlip>` 双轨注入而非 `svg2pptx` / `svg2ooxml`？

开源社区存在 `BramAlkema/svg2ooxml`（<https://github.com/BramAlkema/svg2ooxml>）与 `benouinirachid/svg2pptx`（<https://github.com/benouinirachid/svg2pptx>）等将 SVG 直接展开为 DrawingML `<p:sp>` 形状的库，但在**科研组会 PPT** 中必须采用 **`<asvg:svgBlip>` + 450 DPI PNG 双轨注入**：

1. **防形状数爆炸与卡顿**：一张含 300 个散点或光谱曲线的科研图若在生成期直接展开为 `<p:sp>`，会产生数百至上千个 XML 形状节点，不仅导致 PowerPoint 翻页卡顿，还会直接触发 `layout_audit.py` 的 `shapes > 14` 反卡片堆叠门禁。
2. **原生按需无损解组**：`<asvg:svgBlip>` 在幻灯片 XML 中仅占 **1 个 `<p:pic>` 节点**（450 DPI PNG 保障旧版查看器与 PDF 转换 100% 清晰），而在 Office 2016+ / Microsoft 365 中**右键 →「转换为形状 (Convert to Shape)」**即可在需要修改局部文字或箭头时一键无损解组为原生可编辑对象。
3. **零乱码数学公式保障**：配合 `electrolyte-raman-mlff/scripts/ppt_origin_export.py`（及本 Skill 内置 fallback）的 `sanitize_svg_for_ppt()`，所有 Matplotlib `$...$` 公式的 `<tspan>` 已按 `Arial.ttf` 字形推进宽度从左到右重排并展平为独立 `<text>`（`tspan_count == 0, clip_path_count == 0`），彻底消灭解组后公式错位、缺字方块与黑色遮罩框三大顽疾。
