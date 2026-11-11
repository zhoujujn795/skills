---
name: electrolyte-raman-mlff
description: Standalone publication-grade plotting skill specifically for the Aqueous MgCl2(+H3PO4) Multiscale MD, Machine Learning Force Field (DBMLFF / O4 short-range repulsion fix), and Raman Spectroscopy (Mol2Raman / TNEP / DFT cluster attribution) project. Trigger whenever generating figures for MgCl2 electrolyte solvation (RDF, CN, speciation, Tazi 3-component force traces), Raman/VDOS spectroscopy prediction (Mol2Raman x2 zoom boxes, Pan-Galli zero-gap stacks, F1 distributions, TNEP log RRMSE bars), or MLFF benchmarks (parity with error histogram inset, MACE/NequIP log-log learning curves, PWmat PBE/LDA/PBE-D3 convergence).
license: MIT
---

# Aqueous $\mathrm{MgCl_2(+\,H_3PO_4)}$ Electrolyte, Raman Prediction & MLFF Plotting Skill

This is a **standalone, project-specific plotting skill** decoupled from generic visualization defaults. It implements the exact visual conventions of the 79 top-journal reference figures organized across the three categories in Google Drive (`参考绘图`):
1. **一、`MgCl2水系电解质`（39 张）**: *Jiang J. Energy Chem. 2025*, *Tazi J. Chem. Phys. 2012*, *Balos Nat. Chem. 2022*, *Zhang Adv. Mater. 2026*.
2. **二、`拉曼光谱预测`（23 张）**: *Sorrentino (Mol2Raman) Dig. Disc. 2026*, *Xu (TNEP) JCTC 2024*, *Pan & Galli Nat. Commun. 2020*, *Gastegger Chem. Sci. 2017*.
3. **三、`机器学习力场`（17 张）**: *Wang Nat. Commun. 2026*, *Batatia (MACE) NeurIPS 2022*, *Batzner (NequIP) Nat. Commun. 2022*, *Stevenson Nature 2026*, *Zheng (ByteFF-Pol) Nat. Commun. 2026*.

## Visual & Structural Rules (`electrolyte_nature`)

- **Closed 4-Sided Axes Box**: `axes.spines.top = True`, `axes.spines.right = True`, `axes.linewidth = 0.9`.
- **Inward-Pointing Ticks**: `xtick.direction = "in"`, `ytick.direction = "in"`.
- **Crisp Rectangular Legend**: `legend.frameon = True`, `legend.edgecolor = "black"`, `legend.fancybox = False`.
- **PowerPoint Zero-Garbled-Text (`零乱码`) Editable SVG**:
  - Forces `mathtext.fontset = "custom"` (`Arial` / `Arial:italic` / `Arial:bold`, `fallback = "stixsans"`), eliminating missing `'DejaVu Sans'` and legacy TeX encodings (`cmex10`/`cmsy10`).
  - `scripts/ppt_origin_export.py::sanitize_svg_for_ppt()` sorts `<tspan>` glyphs left-to-right by `x` (fixing Matplotlib's font-grouped XML order that scrambles formulas in PowerPoint), normalizes math codepoints (`\u2212 -> '-'`, `\u27e8/\u27e9 -> '<'/'>'`, `\u22c5 -> '·'`, `\u2032 -> "'"`) to 100% `Arial.ttf`-supported glyphs, flattens all `<tspan>` tags into standalone `<text x="..." y="...">` elements, and strips `<clipPath>` black-box masks after pre-clipping data with `clip_curve_to_box()` / `clip_scatter_to_box()`.
  - Automatically verified on every save by `audit_svg_ppt_compatibility()`.
- **OriginPro / Orange / Excel Native Source Data Export**:
  - Automatically writes `Origin_Source_Data/*_Origin_Data.xlsx` multi-sheet workbooks + UTF-8-BOM `.csv` files with OriginPro's 3-row metadata header (`Long Name`, `Units`, `Comments / Legend`).

## Core Plotting Functions (`scripts/electrolyte_plots.py`)

| Category | Function | Reference Paper Paradigm |
|---|---|---|
| **Cat 1: `MgCl2水系电解质`** | `plot_tazi_3comp_force_trace()` | *Tazi JCP 2012, Fig. 3*: 3-component ($F_x, F_y, F_z$) trajectory force trace across 80 frames (`DFT` red `×` vs `12-6 LJ` vs `O4 Fix`) |
| **Cat 1: `MgCl2水系电解质`** | `plot_jiang_rdf_cn_dual()` | *Jiang JEC 2025, Fig. 2d–e*: Dual-axis $g(r)$ (solid) + $\mathrm{CN}(r)$ (dashed) comparing `1.00r` vs `0.75r ECC` |
| **Cat 1: `MgCl2水系电解质`** | `plot_shell_bars()` | *Balos Nat. Chem. 2022, Fig. 6*: Pastel fill + crisp black outline grouped bars for 6 coordination environments (`Mg_free`, `Mg_paired`, `Cl_CIP`, `Cl_Trans`, `Cl_SSIP`, `Cl_Free`) |
| **Cat 2: `拉曼光谱预测`** | `plot_mol2raman_overlay_with_zoom_box()` | *Mol2Raman Dig. Disc. 2026, Fig. 4*: DFT vs ML-predicted Raman overlay with `× 2` low-frequency (`160–540 cm⁻¹`) black magnification box |
| **Cat 2: `拉曼光谱预测`** | `plot_raman_vdos_stack()` | *Pan & Galli Nat. Commun. 2020, Fig. 2–3*: Zero-gap (`hspace=0`) stacked Isotropic Raman + Intra-Shell + VDOS with vertical shift guides |
| **Cat 2: `拉曼光谱预测`** | `plot_xu_tnep_log_rrmse_bars()` | *Xu TNEP JCTC 2024, Fig. 2*: Two-tier log-scale (`Test RRMSE %`) bar chart for Dipole $\boldsymbol{\mu}$ & Polarizability $\boldsymbol{\alpha}$ |
| **Cat 2: `拉曼光谱预测`** | `plot_mol2raman_f1_histogram()` | *Mol2Raman Dig. Disc. 2026, Fig. 3*: Spectral peak matching $F_1\ (15\ \mathrm{cm^{-1}})$ histogram comparing `1st-Shell (6W)` vs `1st+2nd Shell (18W)` |
| **Cat 3: `机器学习力场`** | `plot_force_parity_with_inset()` | *Wang Nat. Commun. 2026, Fig. 2*: `1:1` Force parity scatter + top-left `RMSE` + bottom-right `Error Distribution (%)` histogram inset |
| **Cat 3: `机器学习力场`** | `plot_mace_nequip_learning_curve()` | *MACE Fig. 2 & NequIP Fig. 5*: Log-log `Force MAE` vs `Training Configurations N` with power-law slopes $s$ and `PBE vs PBE-D3` floor |

## Usage

Run the turnkey generator to produce all three category multi-panel figures (`PPT-safe SVG` + `PDF` + `450 DPI PNG` + `Origin_Source_Data/*.xlsx & *.csv`):
```bash
/Users/zhoujun/miniconda3/bin/python3 /Users/zhoujun/.cc-switch/skills/electrolyte-raman-mlff/scripts/electrolyte_plots.py /Users/zhoujun/Documents/科研/01_开题报告
```
See [`references/electrolyte_spectroscopy_guide.md`](references/electrolyte_spectroscopy_guide.md) and [`scripts/ppt_origin_export.py`](scripts/ppt_origin_export.py) for full details.
