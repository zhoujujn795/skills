# Electrolyte Multiscale MD, MLFF Benchmark & Vibrational Spectroscopy Plotting Guide

This reference documents the specialized physical chemistry, electrolyte solvation, machine-learning force field (MLFF), and Raman/VDOS spectroscopy plotting conventions tailored for the **Aqueous $\mathrm{MgCl_2(+\,H_3PO_4)}$ Multiscale MD & Vibrational Spectroscopy** project (`DBMLFF` force benchmark + `Mol2Raman` / DFT Raman attribution).

It is directly distilled from the 4 benchmark papers in the project's Google Drive (`参考绘图`):

1. **Pan & Galli**, *Nature Communications* **11**, 421 (2020) — `DOI: 10.1038/s41467-019-14248-1`
   - *Structural paradigm*: **Zero-gap vertical stacked panels (`hspace=0.0`)** sharing the x-axis (`Raman shift (cm⁻¹)` or `Frequency (cm⁻¹)`), with y-axis ticks hidden (`yticks=[]`) for normalized/arbitrary-unit spectra (`R(ω)` / `VDOS`).
   - *Curve encoding*: Black (`#1A1A1A`) for Experiment / Total reference, Crimson Red (`#E41A1C`) for Isotropic / Total FPMD or DFT Raman, Cobalt Blue (`#2B5C8F`) for VDOS or Inter-shell contribution, and Warm Taupe (`#B89B82`) for Intra-cluster (`[Mg(H₂O)₆]²⁺` / `CIP`) contribution.
   - *Peak annotations*: Italic math mode labels (`$\nu_1\ (355)$`, `$\nu_{\mathrm{Mg-Cl}}$`, `$\nu_{\mathrm{lib}}$`) placed above peak tips in a dedicated lower band (`y < 0.88`), while panel letters (`a`, `b`) and state labels (`1 m MgCl₂ (SSIP)`) occupy the upper band (`y = 0.88..0.94`) to guarantee zero text/peak collision.

2. **Wang et al.**, *Nature Communications* **17**, 1226 (2026) — `DOI: 10.1038/s41467-025-67982-0`
   - *MLFF / Force-Field Parity (`Fig. 2a–c`)*: Square `1:1` parity scatter (`F_DFT` vs `F_Model`) with diagonal `k--` line, translucent scatter points (`#5E9CE6`, `alpha=0.35`, `rasterized=True`), **top-left `RMSE` text block**, and a **bottom-right `Error Distribution` inset histogram (`inset_axes([0.53, 0.13, 0.41, 0.34])`)** formatted with `PercentFormatter`.
   - *RDF & Coordination Number (`Fig. 3a–d`)*: Stacked `g(r)` and `CN(r)` panels with vertical dashed first-shell cutoff (`r = 2.85 Å` for `Mg²⁺–O_w`).
   - *Concentration-Gradient Spectral Waterfall (`Fig. 3e–f`)*: Vertically offset spectra (`offset_step = 0.50..0.60`) colored along a sequential dark-navy-to-sky-blue gradient (`WANG_WATERFALL_BLUES`), accompanied by a screen-space translucent cyan shift arrow (`arrowstyle="simple"`, `alpha=0.30`) tracking the progressive peak blue/red shift across concentrations.

3. **Balos et al.**, *Nature Chemistry* **14**, 1031–1039 (2022) — `DOI: 10.1038/s41557-022-00977-2`
   - *Time-Correlation / Radial Force Error with Inset (`Fig. 4`)*: Line curves with `fill_between(..., alpha=0.22)` uncertainty bands and a top-right linear regression inset (`inset_axes([0.55, 0.52, 0.40, 0.42])`).
   - *Solvation-Shell / Coordination-Environment Grouped Bars (`Fig. 6`)*: Soft pastel fills (`BALOS_HBOND_SHELLS`: `#F4C29F`, `#92C99A`, `#C2B2D8`, `#F2E896`, `#9ECAE1`) paired with **crisp black bar outlines (`edgecolor="black", linewidth=0.85`)** and black error-bar caps (`capsize=2.5`). Always place the boxed legend in the low-bar corner (`loc="upper left"` when `6W (SSIP)` is on the left) with `15–20%` y-headroom.

4. **Zhang et al.**, *Advanced Materials* (2026) — `DOI: 10.1002/adma.72904`
   - *Multi-Environment Shift Tracking (`Fig. 1`)*: Vertical dashed guide lines (`axvline`, `ls="--"`, `color="#888888"`) threading across stacked panels to highlight how `CIP`/`AGG` formation or `H₃PO₄` addition shifts the `Mg–O` breathing mode (`355 cm⁻¹`) and `Mg–Cl` stretching mode (`262 cm⁻¹`).

---

## Core Axes & Typography Convention (`electrolyte_nature` Preset)

Unlike biology journals (which often remove top and right spines and use outward ticks), **physical chemistry and spectroscopy papers in *Nature Communications*, *Nature Chemistry*, *JACS*, and *Advanced Materials* almost universally use**:
- **Closed 4-sided frame**: `axes.spines.top = True`, `axes.spines.right = True`, `axes.linewidth = 0.9`
- **Inward-pointing ticks**: `xtick.direction = "in"`, `ytick.direction = "in"`
- **Sharp rectangular legend box**: `legend.frameon = True`, `legend.edgecolor = "black"`, `legend.fancybox = False`
- **Editable vector fonts**: `pdf.fonttype = 42`, `ps.fonttype = 42`, `savefig.dpi = 450`

Use the preset via `style_presets.py`:
```python
from style_presets import style_context

with style_context("electrolyte_nature", palette_name="pan_galli_raman"):
    ...
```
or directly import the high-level plotting helpers in `scripts/electrolyte_plots.py`:

```python
from electrolyte_plots import (
    apply_electrolyte_nature_style,
    add_panel_label,
    plot_force_parity_with_inset,
    plot_raman_vdos_stack,
    plot_spectral_waterfall,
    plot_shell_bars,
    plot_rdf_cn_panel,
    plot_tcf_with_inset,
)
```

---

## Mapping to Project Tasks (`MgCl₂(+H₃PO₄)` Multiscale MD & Raman)

| Project Task / Manuscript Figure | Recommended Helper in `scripts/electrolyte_plots.py` | Palette in `assets/color_palettes.py` |
|---|---|---|
| **Line ①**: `DBMLFF` / `O4` Short-Range Repulsion Fix vs `DFT (PBE-D3)` Force & Energy Parity (`1 m` ID + `3 m` OOD Blind Test) | `plot_force_parity_with_inset()` | `wang_mlff_parity` (`#5E9CE6`) |
| **Line ①**: Coordination-Resolved Force `RMSE_vec` (`6W SSIP`, `5W1Cl CIP`, `4W2Cl AGG`) across `12-6 LJ`, `ECC 0.75r`, `O4`, and `DBMLFF` | `plot_shell_bars()` | `balos_hbond_shells` |
| **Line ①**: Short-Range `Mg²⁺–O_w` / `Mg²⁺–Cl⁻` Radial Force Error `ΔF_r(r)` with Shaded SD Band | `plot_tcf_with_inset()` | `pan_galli_raman` |
| **Line ① & ②**: `GROMACS` MD Radial Distribution Function `g(r)` & Running Coordination Number `CN(r)` (`0.75r` ECC vs `1.00r`) | `plot_rdf_cn_panel()` | `wang_waterfall_blues` |
| **Line ②**: `Mg–O` (`355 cm⁻¹`) & `Mg–Cl` (`262 cm⁻¹`) Isotropic Raman + Intra-Shell (`1st` vs `1st+2nd` shell) + VDOS Attribution | `plot_raman_vdos_stack()` | `pan_galli_raman` |
| **Line ②**: Cross-Concentration (`0.5 m → 4.5 m`) or `H₃PO₄` Perturbation Raman / vDOS Waterfall with Shift Arrow | `plot_spectral_waterfall()` | `wang_waterfall_blues` |
