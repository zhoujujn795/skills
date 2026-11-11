---
name: electrolyte-raman-mlff
description: Standalone publication-grade plotting skill specifically for the Aqueous MgCl2(+H3PO4) Multiscale MD, Machine Learning Force Field (DBMLFF / O4 short-range repulsion fix), and Raman Spectroscopy (Mol2Raman / TNEP / DFT cluster attribution) project. Trigger whenever generating figures for MgCl2 electrolyte solvation (3D CPK coordination clusters with force vectors, cross-concentration 3D periodic simulation boxes, RDF, CN, speciation, Tazi 3-component force traces), water structure & Raman/VDOS spectroscopy prediction (waterfall VDOS peak shifts with wide arrows, embedded 3D motifs, Mol2Raman x2 zoom boxes, Pan-Galli zero-gap stacks, F1 distributions, TNEP log RRMSE bars), or classical/MLFF benchmarks (Tazi analytical short-range repulsive potential walls beta*V_rep(r), ByteFF-Pol Sim. vs Exp. density parity, force parity with error histogram inset, MACE/NequIP log-log learning curves).
license: MIT
---

# Aqueous $\mathrm{MgCl_2(+\,H_3PO_4)}$ Electrolyte, 3D Solvation, Raman/VDOS & MLFF Plotting Skill

This is a **standalone, project-specific plotting skill** decoupled from generic visualization defaults. It implements the exact visual paradigms of the top-journal reference figures curated in Google Drive (`参考绘图`) plus literature-standard thermodynamic/spectroscopic conventions:
1. **一、`MgCl2水系电解质`（39+ 张）**: *Jiang J. Energy Chem. 2025 (Table 1 & Fig. 2a,d–e)*, *Tazi J. Chem. Phys. 2012 (Fig. 2b & Fig. 3)*, *Balos Nat. Chem. 2022 (Fig. 6)*, *Zhang Adv. Mater. 2026*.
2. **二、`拉曼光谱预测与水结构 VDOS`（23+ 张）**: *Wang Nat. Commun. 2026 (Fig. 3a–f)*, *Sorrentino (Mol2Raman) Dig. Disc. 2026 (Fig. 3–4)*, *Xu (TNEP) JCTC 2024 (Fig. 2,4)*, *Pan & Galli Nat. Commun. 2020 (Fig. 2–3)*.
3. **三、`机器学习力场与短程修正闭环`（17+ 张）**: *Zheng (ByteFF-Pol) Nat. Commun. 2026 (Fig. 2b–c, Fig. 4a,f)*, *Wang Nat. Commun. 2026 (Fig. 2)*, *Batatia (MACE) NeurIPS 2022*, *Batzner (NequIP) Nat. Commun. 2022*.

## Visual & Export Guarantees (`electrolyte_nature`)

- **Closed 4-Sided Axes Box & Inward Ticks**: `axes.spines.top = True`, `axes.spines.right = True`, `axes.linewidth = 0.9`, `xtick.direction = "in"`, `ytick.direction = "in"`, crisp rectangular black-bordered legends (`fancybox = False`).
- **Mathtext Superscript Best Practice**: Write multi-symbol ionic charges as `\mathrm{Mg^{2{+}}}` so TeX treats `+` as `mathord` without inserting binary-operator whitespace before `+`.
- **PowerPoint Zero-Garbled-Text (`零乱码`) Editable SVG & Native `<asvg:svgBlip>` PPTX**:
  - Forces `mathtext.fontset = "custom"` (`Arial` / `Arial:italic` / `Arial:bold`, `fallback = "stixsans"`).
  - `scripts/ppt_origin_export.py::sanitize_svg_for_ppt()` sorts `<tspan>` glyphs left-to-right by `x`, normalizes math codepoints (`\u2212 -> '-'`, `\u27e8/\u27e9 -> '<'/'>'`, `\u22c5 -> '·'`, `\u22ef -> '···'`, `\u2032 -> "'"`) to 100% `Arial.ttf`-supported glyphs, flattens all `<tspan>` tags into standalone `<text x="..." y="...">` elements, and strips `<clipPath>` black-box masks after pre-clipping data with `clip_curve_to_box()` / `clip_scatter_to_box()`.
  - Verified on every save by `audit_svg_ppt_compatibility()`, and packaged into an Office 2016+ native-SVG `.pptx` deck via `build_editable_svg_pptx()`.
- **OriginPro / Orange / Excel Native Source Data Export**:
  - Automatically writes `Origin_Source_Data/*_Origin_Data.xlsx` multi-sheet workbooks + UTF-8-BOM `.csv` files with OriginPro's 3-row metadata header (`Long Name`, `Units`, `Comments / Legend`).

## Core Plotting Modules

### Part A — Three-Category Benchmark Suite (`scripts/electrolyte_plots.py`)

| Module | Function | Reference Paper Paradigm |
|---|---|---|
| **Cat 1: Electrolyte** | `plot_tazi_3comp_force_trace()` | *Tazi JCP 2012, Fig. 3*: 3-component ($F_x, F_y, F_z$) trajectory force trace across 80 frames (`DFT` red `×` vs `12-6 LJ` vs `O4 Fix`) |
| **Cat 1: Electrolyte** | `plot_jiang_rdf_cn_dual()` | *Jiang JEC 2025, Fig. 2d–e*: Dual-axis $g(r)$ (solid) + $\mathrm{CN}(r)$ (dashed) comparing `1.00r` vs `0.75r ECC` |
| **Cat 1: Electrolyte** | `plot_shell_bars()` | *Balos Nat. Chem. 2022, Fig. 6*: Pastel fill + crisp black outline grouped bars for 6 coordination environments |
| **Cat 2: Raman** | `plot_mol2raman_overlay_with_zoom_box()` | *Mol2Raman Dig. Disc. 2026, Fig. 4*: DFT vs ML-predicted Raman overlay with `× 2` low-frequency (`160–540 cm⁻¹`) magnification box |
| **Cat 2: Raman** | `plot_raman_vdos_stack()` | *Pan & Galli Nat. Commun. 2020, Fig. 2–3*: Zero-gap (`hspace=0`) stacked Isotropic Raman + Intra-Shell + VDOS |
| **Cat 2: Raman** | `plot_xu_tnep_log_rrmse_bars()` | *Xu TNEP JCTC 2024, Fig. 2*: Two-tier log-scale (`Test RRMSE %`) bar chart for Dipole $\boldsymbol{\mu}$ & Polarizability $\boldsymbol{\alpha}$ |
| **Cat 2: Raman** | `plot_mol2raman_f1_histogram()` | *Mol2Raman Dig. Disc. 2026, Fig. 3*: Spectral peak matching $F_1\ (15\ \mathrm{cm^{-1}})$ histogram (`6W` vs `18W`) |
| **Cat 3: MLFF** | `plot_force_parity_with_inset()` | *Wang Nat. Commun. 2026, Fig. 2*: `1:1` Force parity scatter + `RMSE` + bottom-right `Error Distribution (%)` histogram inset |
| **Cat 3: MLFF** | `plot_mace_nequip_learning_curve()` | *MACE Fig. 2 & NequIP Fig. 5*: Log-log `Force MAE` vs `Training Configurations N` with power-law slopes $s$ |

### Part B — Extended 3D Solvation, Real AIMD Waterfall VDOS & O4 Closed-Loop Suite (`scripts/solvation_3d_vdos_o4_plots.py`)

| Module | Function | Reference Paper Paradigm |
|---|---|---|
| **Real 1: 3D Clusters** | `draw_3d_cluster()` | *Jiang JEC 2025, Table 1*: Pure-vector depth-sorted glossy CPK ball-and-stick renderer for $[\mathrm{Mg(H_2O)_6}]^{2+}$, $[\mathrm{MgCl(H_2O)_5}]^+$, $[\mathrm{Mg_2(\mu\text{-}Cl)_2Cl(H_2O)_7}]^+$, and $[\mathrm{Mg_4(\mu\text{-}Cl)_4(H_2O)_{12}}]^{4+}$ with 3D force arrows (`DFT` vs `Leg A` vs `O4`) |
| **Real 1: 3D Boxes** | `draw_3d_periodic_box()` / `load_periodic_box_from_file()` | *Jiang JEC 2025, Fig. 2a*: Dashed regime containers (`1 m SIW` $\to$ `5 m` $\to$ `12 m WIS`) with 3D isometric unit cells + zoomed callout insets (supports `.gro`, PWmat `atom.config`, and `MOVEMENT`) |
| **Real 2: Water & VDOS** | `plot_waterfall_vdos_with_shift_arrow()` / `embed_3d_motif_inset()` | *Wang Nat. Commun. 2026, Fig. 3a–f*: Real `0, 1, 3, 5 m SG15-PBE AIMD` $g_{\mathrm{O-O}}(r)$, multiscale `0–12 m` CN/H-bond transition, embedded 3D mini ball-and-stick motifs, and gradient-blue waterfall VDOS stacks with wide sky-blue shift arrows |
| **Real 3: Repulsive Wall** | `plot_tazi_repulsive_wall()` / `lj_beta_vrep()` | *Tazi JCP 2012, Fig. 2b*: Exact analytical short-range Pauli repulsive potential wall $\beta V_{\mathrm{rep}}(r)$ (`0–40` $k_B T$) comparing `iPMV 0.75`, `Leg A (IOD 0.80)`, `ECCions81`, and `O4 Balanced / Soft` |
| **Real 3: Density Loop** | `plot_byteff_density_parity()` | *ByteFF-Pol Nat. Commun. 2026, Fig. 4a,f*: `Sim. Density vs. Exp. Density (g/mL)` parity (`0–5 m`, `298.15 K`) with Pearson $r$ & MAE + two-tier `Slope α_OLS` / `RMSE_vec` closed-loop bars (auto-loads `o4_npt_density_results.json` from `scripts/run_o4_forward_npt_155.py`) |

## Usage

Generate all 6 publication-grade figures (`PPT-safe SVG` + `PDF` + `450 DPI PNG` + `Origin_Source_Data/*.xlsx & *.csv` + 6-slide Native-SVG `.pptx`):
```bash
/Users/zhoujun/miniconda3/bin/python3 /Users/zhoujun/.cc-switch/skills/electrolyte-raman-mlff/scripts/electrolyte_plots.py /Users/zhoujun/Documents/科研/01_开题报告
/Users/zhoujun/miniconda3/bin/python3 /Users/zhoujun/.cc-switch/skills/electrolyte-raman-mlff/scripts/solvation_3d_vdos_o4_plots.py /Users/zhoujun/Documents/科研/01_开题报告
```
Run ~20-minute GROMACS forward-NPT density validation on `server155`:
```bash
python3 /Users/zhoujun/.cc-switch/skills/electrolyte-raman-mlff/scripts/run_o4_forward_npt_155.py --workdir /tmp/o4_npt_bench --out o4_npt_density_results.json --ntomp 8
```
See [`references/electrolyte_spectroscopy_guide.md`](references/electrolyte_spectroscopy_guide.md) and [`scripts/ppt_origin_export.py`](scripts/ppt_origin_export.py) for full details.
