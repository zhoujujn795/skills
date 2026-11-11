# Six-Module Reference Guide: MgCl₂ Aqueous Electrolyte, 3D Solvation, Raman/VDOS & MLFF

This reference documents the complete 6-module top-journal plotting conventions tailored for **《水系镁离子电池电解液溶剂化结构演化的多尺度模拟与振动光谱研究》**, distilled from the reference figures in Google Drive (`参考绘图`) and verified thermodynamic/spectroscopic standards:

---

## Module 1 (`Fig_Cat1`): `MgCl2水系电解质` — Force Trace, Dual RDF/CN & Shell Bars

1. **Tazi et al.**, *J. Chem. Phys.* **136**, 114507 (2012) — `DOI: 10.1063/1.3692965`
   - *Fig. 3*: **3-Component ($F_x, F_y, F_z$) Trajectory Force Trace (`plot_tazi_3comp_force_trace`)** across configuration index (`1..80`), directly comparing DFT reference forces (red `×` markers) against classical force field predictions (solid/dashed lines).
2. **Jiang et al.**, *J. Energy Chem.* **109**, 466–478 (2025) — `DOI: 10.1016/j.jechem.2025.05.053`
   - *Fig. 2d–e*: **Dual-Axis RDF $g(r)$ + Running Coordination Number $\mathrm{CN}(r)$ (`plot_jiang_rdf_cn_dual`)** — solid lines on left axis for $g(r)$, dashed lines on right axis for $\mathrm{CN}(r)$.
   - *Fig. 2b–c & Fig. 3a*: **Concentration-Dependent Solvation Speciation (`SSIP`, `CIP`, `AGG`) + H-Bond Network Evolution**.
3. **Balos et al.**, *Nature Chemistry* **14**, 1031–1039 (2022) — `DOI: 10.1038/s41557-022-00977-2`
   - *Fig. 6*: **Coordination-Environment Resolved Pastel + Black-Edge Grouped Bar Chart (`plot_shell_bars`)** for `Mg_free`, `Mg_paired`, `Cl_CIP`, `Cl_Trans`, `Cl_SSIP`, and `Cl_Free`.

---

## Module 2 (`Fig_Cat2`): `拉曼光谱预测` — Mol2Raman Zoom Box, Pan–Galli Stack & TNEP Bars

1. **Sorrentino et al. (`Mol2Raman`)**, *Digital Discovery* **5**, 161–176 (2026) — `DOI: 10.1039/d5dd00210a`
   - *Fig. 4*: **DFT vs Predicted Raman Spectrum Overlay with `× 2` Magnified Low-Wavenumber Box (`plot_mol2raman_overlay_with_zoom_box`)** highlighting `160–540 cm⁻¹` ($\nu_{\mathrm{Mg-Cl}}$ at `262 cm⁻¹` and $\nu_1\ \mathrm{MgO_6}$ at `355 cm⁻¹`).
   - *Fig. 3*: **Spectral Peak Matching $F_1\ (15\ \mathrm{cm^{-1}})$ Histogram (`plot_mol2raman_f1_histogram`)** comparing `1st-Shell Only (6W)` vs `Explicit 1st+2nd Shell (18W)`.
2. **Xu et al. (`TNEP`)**, *J. Chem. Theory Comput.* (2024) — `DOI: 10.1021/acs.jctc.3c01343`
   - *Fig. 2*: **Two-Tier Log-Scale Test RRMSE (%) Bar Chart (`plot_xu_tnep_log_rrmse_bars`)** for Dipole ($\boldsymbol{\mu}$) and Polarizability Tensor ($\boldsymbol{\alpha}|\boldsymbol{\chi}$).
3. **Pan & Galli**, *Nature Communications* **11**, 421 (2020) — `DOI: 10.1038/s41467-019-14248-1`
   - *Fig. 2–3*: **Zero-Gap (`hspace=0`) Stacked Raman & VDOS Attribution (`plot_raman_vdos_stack`)**.

---

## Module 3 (`Fig_Cat3`): `机器学习力场` — Force Parity Histogram Inset & MACE/NequIP Learning Curve

1. **Wang et al.**, *Nature Communications* **17**, 1226 (2026) — `DOI: 10.1038/s41467-025-67982-0`
   - *Fig. 2*: **Force/Energy Parity Scatter + Bottom-Right `Error Distribution` Percentage Histogram Inset (`plot_force_parity_with_inset`)**.
2. **Batatia et al. (`MACE`, NeurIPS 2022)** & **Batzner et al. (`NequIP`, *Nat. Commun.* 13, 2453, 2022)**
   - *Fig. 2 / Fig. 5*: **Log-Log Force MAE Learning Curve (`plot_mace_nequip_learning_curve`)** with power-law slopes $s$ and horizontal DFT convergence floor (`PBE vs PBE-D3 RMSE = 0.0068 eV/Å`).

---

## Module 4 (`Fig_Real1`): `3D 溶剂化团簇 + 跨浓度周期性盒子快照`

1. **Jiang et al.**, *J. Energy Chem.* **109**, 466–478 (2025) — *Table 1*
   - Pure-vector depth-sorted glossy CPK 3D ball-and-stick clusters (`draw_3d_cluster`) for:
     - `F-sMISS` (`Mg_SSIP`): $[\mathrm{Mg(H_2O)_6}]^{2+}$ (`1–5 m` dominant)
     - `Monomeric CIP` (`Mg_CIP / Cl_CIP`): $[\mathrm{MgCl(H_2O)_5}]^+$ (`n = 81` inner-shell contact benchmark)
     - `S-cMISS`: $[\mathrm{Mg_2(\mu\text{-}Cl)_2Cl(H_2O)_7}]^+$ (short-chain chloride-bridged dimer)
     - `L-cMISS` (`Mg_AGG`): $[\mathrm{Mg_4(\mu\text{-}Cl)_4(H_2O)_{12}}]^{4+}$ (`54%` in `8–12 m` WIS SCF patch)
   - Overlaid with **staggered 3D-projected force vectors** (`DFT` solid red, `O4 Fix` solid navy, `Leg A 12-6 LJ` dashed amber) directly visualizing the short-range radial repulsion overshoot (`2.06×` / `+0.62 eV/Å`) and `O4` correction (`1.18×`–`1.22×`).
2. **Jiang et al.**, *J. Energy Chem.* **109**, 466–478 (2025) — *Fig. 2a*
   - Rounded dashed regime frames (`Dilute SIW 1 m` $\to$ `Concentrated 5 m` $\to$ `Ultra-High WIS 12 m`) housing 3D isometric wireframe periodic simulation cells (`draw_3d_periodic_box`) + dotted callout leader lines to zoomed local coordination motifs.

---

## Module 5 (`Fig_Real2`): `水结构 gO-O(r) + 瀑布式 VDOS 振动功率谱频移`

1. **Wang et al.**, *Nature Communications* **17**, 1226 (2026) — *Fig. 3a–f*
   - Driven 100% by real local `0, 1, 3, 5 m SG15-PBE AIMD` trajectories (`benchmark_comparison_report.json`):
     - **Panel a**: Water-water $g_{\mathrm{O-O}}(r)$ showing first-shell expansion (`2.73 → 2.83 Å`) + embedded 3D tetrahedral `H₂O···H₂O` dimer (`embed_3d_motif_inset`).
     - **Panel b**: Cross-concentration (`0–12 m`) transition from `SIW` (`CN_Mg-O = 6.00`) to `WIS` (`CN_Mg-Cl = 2.22`) alongside $\mathrm{HB(O_w\cdots O_w)}$ depletion (`1.78 → 0.78`) and $\mathrm{HB(O_w\cdots Cl^-)}$ formation (`0.00 → 0.89`).
     - **Panels c–d**: Gradient-blue (`#111111 → #0D2B80 → #1D70DC → #00B8D9`) waterfall VDOS stacks (`plot_waterfall_vdos_with_shift_arrow`) with semi-transparent sky-blue wide shift arrows (`+37 cm⁻¹` `O–H` stretch blue-shift in `2750–3920 cm⁻¹`, and `782 → 554 cm⁻¹` librational red-shift + $\nu_1(\mathrm{MgO_6}) \approx 360\ \mathrm{cm^{-1}}$ cage marker in `120–960 cm⁻¹`).

---

## Module 6 (`Fig_Real3`): `短程排斥势墙解析曲线 + O4 前向 MD 密度/结构验证`

1. **Tazi et al.**, *J. Chem. Phys.* **136**, 114507 (2012) — *Fig. 2b*
   - Exact dimensionless Pauli short-range repulsive wall $\beta V_{\mathrm{rep}}(r) = 4\epsilon(\sigma/r)^{12} / (k_B T)$ (`0–40` $k_B T$, `plot_tazi_repulsive_wall`) across real PBE contact bands (`1.98–2.22 Å` for $\mathrm{Mg^{2+}-O_w}$, `2.29–2.75 Å` for $\mathrm{Mg^{2+}-Cl^-}$), contrasting `iPMV 0.75` (`α = 7.54`), `Leg A: IOD 0.80` (`α = 2.06`), `O4 Balanced` (`α = 1.06`, `RMSE = 0.35 eV/Å` at `3 m`), `O4 Soft OPC`, and `ECCions81` (`α = 0.49` inner-shell collapse).
2. **Zheng et al. (`ByteFF-Pol`)**, *Nature Communications* (2026) — *Fig. 4a,f* (`DOI: 10.1038/s41467-026-73566-3`)
   - **Panel c**: `Sim. Density vs. Exp. Density (g/mL)` parity (`plot_byteff_density_parity`) across `0–5 m MgCl₂(aq)` at `298.15 K` (experimental Pitzer / Miller–Rard benchmark: `0.9971–1.3302 g/mL`) with Pearson $r$ & `MAE`. Automatically ingests `o4_npt_density_results.json` produced by `scripts/run_o4_forward_npt_155.py`.
   - **Panel d**: Zero-gap two-tier bar chart comparing OLS force slope $\alpha_{\mathrm{OLS}}$ (vs `Ideal α = 1.00`) and vector force $\mathrm{RMSE_{vec}}$ across `1m_orig20`, `1m_ext30`, `3m_prod30` (OOD blind test), and `pooled80`.

---

## Turnkey CLI Execution

```bash
# 1. Generate Modules 1-3 (Fig_Cat1 .. Fig_Cat3)
/Users/zhoujun/miniconda3/bin/python3 /Users/zhoujun/.cc-switch/skills/electrolyte-raman-mlff/scripts/electrolyte_plots.py /Users/zhoujun/Documents/科研/01_开题报告

# 2. Generate Modules 4-6 (Fig_Real1 .. Fig_Real3) + Unified 6-Slide Native-SVG Editable PPTX
/Users/zhoujun/miniconda3/bin/python3 /Users/zhoujun/.cc-switch/skills/electrolyte-raman-mlff/scripts/solvation_3d_vdos_o4_plots.py /Users/zhoujun/Documents/科研/01_开题报告
```
