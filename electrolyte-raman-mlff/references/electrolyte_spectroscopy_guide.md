# Three-Category Reference Guide: MgCl₂ Aqueous Electrolyte, Raman Prediction & MLFF

This reference documents the complete 3-category top-journal plotting conventions tailored for **《水系镁离子电池电解液溶剂化结构演化的多尺度模拟与振动光谱研究》**, distilled directly from the 79 figures in the project's Google Drive (`参考绘图`):

---

## Category 1: `MgCl2水系电解质` (39 Figures)

1. **Tazi et al.**, *J. Chem. Phys.* **136**, 114507 (2012) — `DOI: 10.1063/1.3692965`
   - *Fig. 3 (p16)*: **3-Component ($F_x, F_y, F_z$) Trajectory Force Trace (`plot_tazi_3comp_force_trace`)** across configuration index (`1..80`), directly comparing DFT reference forces (red `×` markers) against classical force field predictions (solid/dashed lines). Direct literature precedent for our 20-frame / 80-frame single-snapshot force benchmark.
2. **Jiang et al.**, *J. Energy Chem.* **109**, 466–478 (2025) — `DOI: 10.1016/j.jechem.2025.05.053`
   - *Fig. 2d–e*: **Dual-Axis RDF $g(r)$ + Running Coordination Number $\mathrm{CN}(r)$ (`plot_jiang_rdf_cn_dual`)** — solid lines on left axis for $g(r)$, dashed lines on right axis for $\mathrm{CN}(r)$.
   - *Fig. 2b–c & Fig. 3a*: **Concentration-Dependent Solvation Speciation (`SSIP`, `CIP`, `AGG`) + H-Bond Network Evolution**.
3. **Balos et al.**, *Nature Chemistry* **14**, 1031–1039 (2022) — `DOI: 10.1038/s41557-022-00977-2`
   - *Fig. 6*: **Coordination-Environment Resolved Pastel + Black-Edge Grouped Bar Chart (`plot_shell_bars`)** — used for comparing `Mg_free`, `Mg_paired`, `Cl_CIP`, `Cl_Trans`, `Cl_SSIP`, and `Cl_Free` force $\mathrm{RMSE_{vec}}$.

---

## Category 2: `拉曼光谱预测` (23 Figures)

1. **Sorrentino et al. (`Mol2Raman`)**, *Digital Discovery* **5**, 161–176 (2026) — `DOI: 10.1039/d5dd00210a`
   - *Fig. 4*: **DFT vs Predicted Raman Spectrum Overlay with `× 2` Magnified Low-Wavenumber Box (`plot_mol2raman_overlay_with_zoom_box`)** — blue curve for DFT-calculated spectrum, red curve for ML-predicted spectrum, and a crisp black rectangle highlighting the amplified (`× 2`) low-frequency region (`160–540 cm⁻¹`, covering $\nu_{\mathrm{Mg-Cl}}$ at `262 cm⁻¹` and $\nu_1\ \mathrm{MgO_6}$ at `355 cm⁻¹`).
   - *Fig. 3*: **Spectral Peak Matching $F_1\ (15\ \mathrm{cm^{-1}})$ Histogram (`plot_mol2raman_f1_histogram`)** — overlapping translucent histograms comparing `1st-Shell Only (6W)` vs `Explicit 1st+2nd Shell (18W)` with vertical dashed median lines.
2. **Xu et al. (`TNEP`)**, *J. Chem. Theory Comput.* (2024) — `DOI: 10.1021/acs.jctc.3c01343`
   - *Fig. 2*: **Two-Tier Log-Scale Test RRMSE (%) Bar Chart (`plot_xu_tnep_log_rrmse_bars`)** for Dipole ($\boldsymbol{\mu}$) and Polarizability Tensor ($\boldsymbol{\alpha}|\boldsymbol{\chi}$).
   - *Fig. 4*: **Multi-Tier Zero-Gap Stacked IR / Anisotropic Raman / Isotropic Raman Spectra**.
3. **Pan & Galli**, *Nature Communications* **11**, 421 (2020) — `DOI: 10.1038/s41467-019-14248-1`
   - *Fig. 2–3*: **Zero-Gap (`hspace=0`) Stacked Raman & VDOS Attribution (`plot_raman_vdos_stack`)** with Zhang et al. (*Adv. Mater.* 2026) vertical dashed Raman shift guides.

---

## Category 3: `机器学习力场` (17 Figures)

1. **Wang et al.**, *Nature Communications* **17**, 1226 (2026) — `DOI: 10.1038/s41467-025-67982-0`
   - *Fig. 2*: **Force/Energy Parity Scatter + Bottom-Right `Error Distribution` Percentage Histogram Inset (`plot_force_parity_with_inset`)**.
2. **Batatia et al. (`MACE`, NeurIPS 2022)** & **Batzner et al. (`NequIP`, *Nat. Commun.* 13, 2453, 2022)**
   - *Fig. 2 / Fig. 5*: **Log-Log Force MAE Learning Curve (`plot_mace_nequip_learning_curve`)** (`Force MAE [eV/Å]` vs `Number of training configurations N` from $10^1$ to $10^3$) with power-law slopes $s$ and horizontal DFT convergence floor (`PBE vs PBE-D3 RMSE = 0.0068 eV/Å`).
3. **Zheng et al. (`ByteFF-Pol`)**, *Nature Communications* (2026) — `DOI: 10.1038/s41467-026-73566-3`
   - *Fig. 2b–c*: **Short-Range Radial Force / Interaction Energy Decomposition** (`Pure 12-6 LJ r^-12`, `Pure Coulomb`, `Leg A Total`, `LDA Overbinding`, `O4 Balanced Fix`).
   - *Fig. 4*: **Charge-Scaling (`0.75r / 0.80r ECC`) vs Polarizable / MLFF Transport & Coordination Comparison**.

---

## Turnkey CLI Execution

Generate all three category figures (`PDF` + `450 DPI PNG`) in one command:
```bash
/Users/zhoujun/miniconda3/bin/python3 /Users/zhoujun/.cc-switch/skills/scientific-visualization/scripts/electrolyte_plots.py /Users/zhoujun/Documents/科研/01_开题报告
```
