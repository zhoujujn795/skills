#!/usr/bin/env python3
"""
Electrolyte Multiscale MD, MLFF Parity & Vibrational Spectroscopy Plotting Toolkit.

Modeled directly after the 4 reference papers in the user's Google Drive (`参考绘图`):
  1. Pan & Galli, Nature Communications 11, 421 (2020) [DOI: 10.1038/s41467-019-14248-1]
     -> Zero-gap stacked Raman & VDOS attribution panels (hspace=0), closed 4-sided box,
        inward ticks, black/red/cobalt/taupe curves, math-italic peak mode labels (v1, v2...).
  2. Wang et al., Nature Communications 17, 1226 (2026) [DOI: 10.1038/s41467-025-67982-0]
     -> Fig 2: Energy/Force/Virial parity scatter + top-left RMSE + bottom-right Error Distribution inset.
     -> Fig 3: g(r), coordination number CN, and sequential-blue waterfall vDOS/Raman with shift arrow.
  3. Balos et al., Nature Chemistry (2022) [DOI: 10.1038/s41557-022-00977-2]
     -> Fig 4: Time-correlation / radial force error curves with shaded error bands + linear trend inset.
     -> Fig 6: Solvation-shell / coordination-environment grouped bars with pastel fills & black outlines.
  4. Zhang et al., Advanced Materials (2026) [DOI: 10.1002/adma.72904]
     -> Fig 1: Vertical dashed chemical/Raman shift tracking lines across solvation environments.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Sequence

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

# Ensure assets/ is importable
ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"
if str(ASSET_DIR) not in sys.path:
    sys.path.insert(0, str(ASSET_DIR))

from color_palettes import (
    PAN_GALLI_RAMAN,
    WANG_MLFF_PARITY,
    WANG_WATERFALL_BLUES,
    BALOS_HBOND_SHELLS,
)


def apply_electrolyte_nature_style() -> None:
    """Apply the closed-box, inward-tick Nature Communications / Nature Chemistry style."""
    mpl.rcParams.update({
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.dpi": 450,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "PingFang SC", "Heiti TC", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "font.size": 8.5,
        "axes.labelsize": 9.0,
        "axes.titlesize": 9.0,
        "axes.linewidth": 0.9,
        "axes.edgecolor": "black",
        "axes.spines.top": True,
        "axes.spines.right": True,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.labelsize": 8.0,
        "ytick.labelsize": 8.0,
        "xtick.major.size": 3.5,
        "ytick.major.size": 3.5,
        "xtick.major.width": 0.8,
        "ytick.major.width": 0.8,
        "lines.linewidth": 1.35,
        "legend.fontsize": 7.2,
        "legend.frameon": True,
        "legend.edgecolor": "black",
        "legend.fancybox": False,
        "legend.framealpha": 1.0,
    })


def add_panel_label(ax: plt.Axes, label: str, x: float = -0.14, y: float = 1.03, inside: bool = False) -> None:
    """Add a Nature-style lowercase bold panel letter ('a', 'b', 'c', 'd')."""
    if inside:
        ax.text(
            0.03, 0.92, label, transform=ax.transAxes,
            fontsize=11, fontweight="bold", va="top", ha="left", color="black"
        )
    else:
        ax.text(
            x, y, label, transform=ax.transAxes,
            fontsize=11, fontweight="bold", va="bottom", ha="right", color="black"
        )


def plot_force_parity_with_inset(
    ax: plt.Axes,
    f_dft: np.ndarray,
    f_model: np.ndarray,
    *,
    rmse_val: float | None = None,
    rmse_std: float | None = None,
    color: str = "#5E9CE6",
    xlabel: str = r"$F^i_{\mathrm{DFT}}\ (\mathrm{eV/\AA})$",
    ylabel: str = r"$F^i_{\mathrm{Model}}\ (\mathrm{eV/\AA})$",
    lim: tuple[float, float] = (-15.0, 15.0),
    inset_max_err: float = 0.45,
    inset_xlabel: str = r"Error ($\mathrm{eV/\AA}$)",
    title_tag: str | None = None,
) -> plt.Axes:
    """
    Wang et al. (Nat. Commun. 2026, Fig. 2) Parity Scatter + Bottom-Right Error Distribution Inset.
    """
    f_dft = np.asarray(f_dft).ravel()
    f_model = np.asarray(f_model).ravel()
    err = np.abs(f_model - f_dft)
    if rmse_val is None:
        rmse_val = float(np.sqrt(np.mean((f_model - f_dft) ** 2)))

    ax.plot(lim, lim, "k--", lw=0.9, zorder=1)
    ax.scatter(f_dft, f_model, s=5, c=color, alpha=0.35, edgecolors="none", rasterized=True, zorder=2)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    rmse_txt = f"RMSE:\n{rmse_val:.2e}" + (f" ± {rmse_std:.2e}" if rmse_std is not None else " eV/Å")
    if title_tag:
        rmse_txt = f"{title_tag}\n" + rmse_txt
    ax.text(0.05, 0.94, rmse_txt, transform=ax.transAxes, fontsize=7.5, va="top", ha="left", color="#111111")

    # Bottom-right Error Distribution inset (Wang et al. Fig. 2a-b style)
    ins = ax.inset_axes([0.53, 0.13, 0.41, 0.34])
    bins = np.linspace(0, inset_max_err, 22)
    weights = np.ones_like(err) * (100.0 / max(len(err), 1))
    ins.hist(err, bins=bins, weights=weights, color=color, alpha=0.72, edgecolor="none")
    ins.set_xlim(0, inset_max_err)
    ins.set_title("Error Distribution", fontsize=6.5, pad=2)
    ins.set_xlabel(inset_xlabel, fontsize=6.0, labelpad=1)
    ins.tick_params(axis="both", labelsize=5.5, length=2.0, direction="out")
    ins.yaxis.set_major_formatter(mpl.ticker.PercentFormatter(decimals=0))
    return ins


def plot_raman_vdos_stack(
    fig: plt.Figure,
    subspec: mpl.gridspec.SubplotSpec,
    wavenumber: np.ndarray,
    top_curves: list[tuple[str, np.ndarray, str]],
    bottom_curves: list[tuple[str, np.ndarray, str]],
    *,
    top_label: str = r"$\mathrm{1\ m\ MgCl_2}$",
    bottom_label: str = r"$\mathrm{3\ m\ MgCl_2\ (CIP/AGG)}$",
    top_peaks: list[tuple[float, float, str]] | None = None,
    bottom_peaks: list[tuple[float, float, str]] | None = None,
    vertical_guides: list[float] | None = None,
    xlim: tuple[float, float] = (150, 650),
    ylim: tuple[float, float] = (0.0, 1.38),
    panel_letters: tuple[str, str] = ("b", "c"),
) -> tuple[plt.Axes, plt.Axes]:
    """
    Pan & Galli (Nat. Commun. 2020, Fig. 2 & Fig. 3) Zero-Gap Stacked Raman & VDOS Attribution Plot,
    with optional Zhang et al. (Adv. Mater. 2026, Fig. 1) vertical dashed Raman shift guides.
    """
    gs = subspec.subgridspec(2, 1, hspace=0.0)
    ax_top = fig.add_subplot(gs[0])
    ax_bot = fig.add_subplot(gs[1], sharex=ax_top)

    for label, y, col in top_curves:
        ax_top.plot(wavenumber, y, label=label, color=col, lw=1.25)
    for label, y, col in bottom_curves:
        ax_bot.plot(wavenumber, y, label=label, color=col, lw=1.25)

    if vertical_guides:
        for vx in vertical_guides:
            ax_top.axvline(vx, color="#888888", ls="--", lw=0.75, alpha=0.6, zorder=0)
            ax_bot.axvline(vx, color="#888888", ls="--", lw=0.75, alpha=0.6, zorder=0)

    ax_top.set_xlim(xlim)
    ax_top.set_ylim(ylim)
    ax_bot.set_ylim(ylim)
    ax_top.set_yticks([])
    ax_bot.set_yticks([])
    plt.setp(ax_top.get_xticklabels(), visible=False)
    ax_bot.set_xlabel(r"Raman shift ($\mathrm{cm^{-1}}$)")
    ax_top.set_ylabel(r"$R(\omega)$ / VDOS", labelpad=6)
    ax_bot.set_ylabel(r"$R(\omega)$ / VDOS", labelpad=6)

    # Top-left panel letter and state label in a dedicated upper band (y_axes = 0.88..0.94)
    ax_top.text(0.03, 0.91, panel_letters[0], transform=ax_top.transAxes, fontsize=10.5, fontweight="bold", va="top")
    ax_top.text(0.09, 0.90, top_label, transform=ax_top.transAxes, fontsize=8.0, va="top")
    ax_bot.text(0.03, 0.91, panel_letters[1], transform=ax_bot.transAxes, fontsize=10.5, fontweight="bold", va="top")
    ax_bot.text(0.09, 0.90, bottom_label, transform=ax_bot.transAxes, fontsize=8.0, va="top")

    if top_peaks:
        for px, py, ptxt in top_peaks:
            ax_top.text(px, py, ptxt, fontsize=7.6, ha="center", va="bottom", color="#111111")
    if bottom_peaks:
        for px, py, ptxt in bottom_peaks:
            ax_bot.text(px, py, ptxt, fontsize=7.6, ha="center", va="bottom", color="#111111")

    leg = ax_top.legend(
        loc="upper right", frameon=True, edgecolor="black",
        fancybox=False, fontsize=6.6, borderpad=0.35, handlelength=1.4
    )
    leg.get_frame().set_linewidth(0.7)
    return ax_top, ax_bot


def plot_spectral_waterfall(
    ax: plt.Axes,
    wavenumber: np.ndarray,
    spectra: list[tuple[str, np.ndarray]],
    *,
    offset_step: float = 0.55,
    xlabel: str = r"Wavenumber ($\mathrm{cm^{-1}}$)",
    ylabel: str = "Raman / vDOS (arb. units)",
    title_inside: str = r"$\mathrm{MgCl_2\ O-H\ Stretch}$",
    arrow_start_end: tuple[tuple[float, float], tuple[float, float]] | None = None,
) -> None:
    """
    Wang et al. (Nat. Commun. 2026, Fig. 3e-f) Concentration-Gradient Waterfall Plot with Shift Arrow.
    Uses screen-space annotation arrowstyle so the wide translucent blue arrow never distorts.
    """
    n = len(spectra)
    colors = WANG_WATERFALL_BLUES[:n] if n <= len(WANG_WATERFALL_BLUES) else plt.cm.YlGnBu(np.linspace(0.95, 0.25, n))

    for idx, ((label, y), col) in enumerate(zip(spectra, colors)):
        y_norm = y / max(np.max(y), 1e-8)
        ax.plot(wavenumber, y_norm + idx * offset_step, color=col, lw=1.35, label=label, zorder=2 + idx)

    if arrow_start_end is not None:
        (x0, y0), (x1, y1) = arrow_start_end
        ax.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops=dict(
                arrowstyle="simple,head_width=1.45,head_length=1.15,tail_width=0.58",
                facecolor="#38BDF8",
                edgecolor="none",
                alpha=0.30,
            ),
            zorder=1,
        )

    total_top = (n - 1) * offset_step + 1.48
    ax.set_ylim(-0.08, total_top)
    ax.set_yticks([])
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.text(0.56, 0.94, title_inside, transform=ax.transAxes, fontsize=8.5, ha="center", va="top")
    leg = ax.legend(loc="upper left", frameon=True, edgecolor="black", fancybox=False, fontsize=6.6, borderpad=0.35)
    leg.get_frame().set_linewidth(0.7)


def plot_shell_bars(
    ax: plt.Axes,
    groups: Sequence[str],
    categories: Sequence[str],
    values: np.ndarray,
    errors: np.ndarray | None = None,
    *,
    ylabel: str = r"Force $\mathrm{RMSE_{vec}}\ (\mathrm{eV/\AA})$",
    ylim: tuple[float, float] | None = None,
    legend_loc: str = "upper left",
) -> None:
    """
    Balos et al. (Nat. Chem. 2022, Fig. 6) Grouped Pastel Bar Chart with Crisp Black Outlines.
    Ideal for comparing Solvation-Shell H-Bond Strength or Coordination-Resolved Force RMSE.
    """
    values = np.asarray(values, dtype=float)
    n_groups, n_cats = values.shape
    x = np.arange(n_groups)
    total_w = 0.74
    bar_w = total_w / n_cats
    palette = BALOS_HBOND_SHELLS

    for c_idx in range(n_cats):
        pos = x - 0.5 * total_w + (c_idx + 0.5) * bar_w
        yerr = errors[:, c_idx] if errors is not None else None
        ax.bar(
            pos, values[:, c_idx], width=bar_w,
            color=palette[c_idx % len(palette)],
            edgecolor="black", linewidth=0.85,
            yerr=yerr, capsize=2.5,
            error_kw={"elinewidth": 0.8, "ecolor": "black"},
            label=categories[c_idx],
        )

    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_ylabel(ylabel)
    if ylim is not None:
        ax.set_ylim(ylim)
    leg = ax.legend(loc=legend_loc, frameon=True, edgecolor="black", fancybox=False, fontsize=6.6, borderpad=0.35)
    leg.get_frame().set_linewidth(0.7)


def plot_rdf_cn_panel(
    ax_rdf: plt.Axes,
    ax_cn: plt.Axes,
    r: np.ndarray,
    rdf_curves: list[tuple[str, np.ndarray, str]],
    cn_curves: list[tuple[str, np.ndarray, str]],
    *,
    shell_cutoff: float | None = 2.85,
    pair_label: str = r"$\mathrm{Mg^{2+}-O_w}$",
) -> None:
    """
    Wang et al. (Nat. Commun. 2026, Fig. 3a-d) Stacked or Dual Radial Distribution Function g(r) + CN(r).
    """
    for label, g_r, col in rdf_curves:
        ax_rdf.plot(r, g_r, label=label, color=col, lw=1.3)
    for label, cn_r, col in cn_curves:
        ax_cn.plot(r, cn_r, label=label, color=col, lw=1.3)

    if shell_cutoff is not None:
        ax_rdf.axvline(shell_cutoff, color="#777777", ls="--", lw=0.8)
        ax_cn.axvline(shell_cutoff, color="#777777", ls="--", lw=0.8)

    ax_rdf.set_ylabel(r"$g(r)$")
    ax_cn.set_ylabel("CN")
    ax_cn.set_xlabel(r"$r\ (\mathrm{\AA})$")
    ax_rdf.text(0.50, 0.90, pair_label, transform=ax_rdf.transAxes, ha="center", va="top", fontsize=8.5)
    leg = ax_rdf.legend(loc="upper right", frameon=True, edgecolor="black", fancybox=False, fontsize=6.5)
    leg.get_frame().set_linewidth(0.7)


def plot_tcf_with_inset(
    ax: plt.Axes,
    x: np.ndarray,
    curves: list[tuple[str, np.ndarray, np.ndarray, str]],
    *,
    inset_x: np.ndarray | None = None,
    inset_y: np.ndarray | None = None,
    inset_yerr: np.ndarray | None = None,
    xlabel: str = r"$r_{\mathrm{Mg-O}}\ (\mathrm{\AA})$",
    ylabel: str = r"$\Delta F_r\ (\mathrm{eV/\AA})$",
) -> None:
    """
    Balos et al. (Nat. Chem. 2022, Fig. 4) Curve with Shaded Error Bands + Top-Right Linear Trend Inset.
    Useful for THz/Raman time-correlation anisotropy or short-range repulsion diagnosis.
    """
    for label, y_mean, y_err, col in curves:
        ax.plot(x, y_mean, label=label, color=col, lw=1.35)
        ax.fill_between(x, y_mean - y_err, y_mean + y_err, color=col, alpha=0.22, edgecolor="none")

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    leg = ax.legend(loc="upper left", frameon=False, fontsize=6.8)

    if inset_x is not None and inset_y is not None:
        ins = ax.inset_axes([0.55, 0.52, 0.40, 0.42])
        coef = np.polyfit(inset_x, inset_y, 1)
        x_line = np.linspace(np.min(inset_x), np.max(inset_x), 50)
        ins.plot(x_line, np.polyval(coef, x_line), color="#B22222", lw=1.0)
        ins.errorbar(
            inset_x, inset_y, yerr=inset_yerr, fmt="o", ms=3.2,
            color="#333333", ecolor="#333333", elinewidth=0.7, capsize=1.8
        )
        ins.tick_params(axis="both", labelsize=5.5, length=2.0, direction="in")


def generate_project_demo(out_pdf: str, out_png: str) -> None:
    """
    Generate a 4-block (5-letter) Nature Communications / Nature Chemistry style showcase figure
    for the user's Aqueous MgCl2(+H3PO4) Multiscale MD & Raman Spectroscopy project.
    """
    apply_electrolyte_nature_style()
    rng = np.random.default_rng(42)

    fig = plt.figure(figsize=(7.2, 6.2), dpi=450)
    gs = fig.add_gridspec(2, 2, wspace=0.28, hspace=0.30, left=0.09, right=0.97, top=0.95, bottom=0.09)

    # Panel a: Wang Nat. Commun. 2026 Fig. 2 style — O4 Short-Range Corrected Force Parity + Error Histogram
    ax_a = fig.add_subplot(gs[0, 0])
    f_dft = rng.normal(0.0, 4.2, 1200)
    f_o4 = f_dft + rng.normal(0.0, 0.14, 1200)
    plot_force_parity_with_inset(
        ax_a, f_dft, f_o4,
        rmse_val=0.142, rmse_std=0.012,
        color="#5E9CE6",
        xlabel=r"$F^i_{\mathrm{DFT\ (PBE-D3)}}\ (\mathrm{eV/\AA})$",
        ylabel=r"$F^i_{\mathrm{O4-Corrected}}\ (\mathrm{eV/\AA})$",
        lim=(-15, 15), inset_max_err=0.45,
        title_tag="3 m Blind Test (80 frames)"
    )
    add_panel_label(ax_a, "a")

    # Panel b & c (stacked): Pan & Galli Nat. Commun. 2020 Fig. 3 style — Mg-O 355 cm-1 Raman & VDOS Attribution
    wn = np.linspace(150, 650, 500)
    # Keep max curve height <= 0.78 so the top band (0.95..1.35) is 100% collision-free for labels & legends
    iso_1m = 0.76 * np.exp(-((wn - 355) / 18) ** 2) + 0.14 * np.exp(-((wn - 235) / 36) ** 2)
    intra_1m = 0.52 * np.exp(-((wn - 355) / 16) ** 2)
    vdos_1m = 0.68 * np.exp(-((wn - 355) / 14) ** 2) + 0.58 * np.exp(-((wn - 465) / 28) ** 2) + 0.36 * np.exp(-((wn - 238) / 24) ** 2)

    # 3 m MgCl2: CIP [MgCl(H2O)5]+ red-shifted shoulder (~338 cm-1) + Mg-Cl stretch (~262 cm-1)
    iso_3m = 0.66 * np.exp(-((wn - 348) / 20) ** 2) + 0.38 * np.exp(-((wn - 332) / 18) ** 2) + 0.26 * np.exp(-((wn - 262) / 22) ** 2)
    intra_3m = 0.42 * np.exp(-((wn - 336) / 18) ** 2) + 0.20 * np.exp(-((wn - 262) / 20) ** 2)
    vdos_3m = 0.62 * np.exp(-((wn - 346) / 18) ** 2) + 0.56 * np.exp(-((wn - 262) / 18) ** 2) + 0.48 * np.exp(-((wn - 458) / 30) ** 2)

    plot_raman_vdos_stack(
        fig, gs[0, 1], wn,
        top_curves=[
            ("Isotropic", iso_1m, PAN_GALLI_RAMAN[1]),
            (r"Intra ($\mathrm{1st\ shell}$)", intra_1m, PAN_GALLI_RAMAN[3]),
            ("VDOS", vdos_1m, PAN_GALLI_RAMAN[2]),
        ],
        bottom_curves=[
            ("Isotropic", iso_3m, PAN_GALLI_RAMAN[1]),
            (r"Intra ($\mathrm{CIP}$)", intra_3m, PAN_GALLI_RAMAN[3]),
            ("VDOS", vdos_3m, PAN_GALLI_RAMAN[2]),
        ],
        top_label=r"$\mathrm{1\ m\ MgCl_2\ (SSIP)}$",
        bottom_label=r"$\mathrm{3\ m\ MgCl_2\ (CIP)}$",
        top_peaks=[(355, 0.80, r"$\nu_1\ (355)$"), (465, 0.62, r"$\nu_{\mathrm{lib}}$")],
        bottom_peaks=[(262, 0.60, r"$\nu_{\mathrm{Mg-Cl}}$"), (343, 0.89, r"$\nu_1'$")],
        vertical_guides=[262, 355],
        xlim=(160, 620),
        ylim=(0.0, 1.36),
        panel_letters=("b", "c"),
    )

    # Panel d: Wang Nat. Commun. 2026 Fig. 3e-f style — Concentration Waterfall Spectra
    ax_d = fig.add_subplot(gs[1, 0])
    wn_oh = np.linspace(2800, 3800, 400)
    concs = ["0.5 M", "1.0 M", "1.5 M", "2.5 M", "3.5 M", "4.5 M"]
    waterfall_specs = []
    for i, c_lbl in enumerate(concs):
        center = 3400 + i * 18.0  # Progressive blue-shift as bulk H-bond network breaks
        shoulder = 3235 + i * 10.0
        y_sp = (0.72 - 0.08 * i) * np.exp(-((wn_oh - shoulder) / 140) ** 2) + (0.85 + 0.06 * i) * np.exp(-((wn_oh - center) / 115) ** 2)
        waterfall_specs.append((c_lbl, y_sp))
    plot_spectral_waterfall(
        ax_d, wn_oh, waterfall_specs,
        offset_step=0.52,
        xlabel=r"Wavenumber ($\mathrm{cm^{-1}}$)",
        ylabel="Raman / vDOS (arb. units)",
        title_inside=r"$\mathrm{MgCl_2\ O-H\ Stretch}$",
        arrow_start_end=((3385, 0.55), (3495, 3.65)),
    )
    add_panel_label(ax_d, "d")

    # Panel e: Balos Nat. Chem. 2022 Fig. 6 style — Coordination-Environment Force RMSE / H-Bond Bars
    ax_e = fig.add_subplot(gs[1, 1])
    groups = [r"$\mathrm{6W\ (SSIP)}$", r"$\mathrm{5W1Cl\ (CIP)}$", r"$\mathrm{4W2Cl\ (AGG)}$"]
    categories = ["12-6 LJ (Raw)", "ECC 0.75r", "O4 Repulsion Fix", "DBMLFF"]
    rmse_vals = np.array([
        [0.48, 0.36, 0.21, 0.11],
        [0.92, 0.68, 0.35, 0.14],
        [1.15, 0.84, 0.44, 0.16],
    ])
    rmse_errs = np.array([
        [0.03, 0.02, 0.02, 0.01],
        [0.05, 0.04, 0.03, 0.01],
        [0.06, 0.05, 0.03, 0.02],
    ])
    plot_shell_bars(
        ax_e, groups, categories, rmse_vals, rmse_errs,
        ylabel=r"Force $\mathrm{RMSE_{vec}}\ (\mathrm{eV/\AA})$",
        ylim=(0, 1.38),
        legend_loc="upper left",
    )
    add_panel_label(ax_e, "e")

    os.makedirs(os.path.dirname(os.path.abspath(out_pdf)), exist_ok=True)
    fig.savefig(out_pdf, dpi=450)
    fig.savefig(out_png, dpi=450)
    print(f"Saved benchmark showcase figure:\n  PDF -> {out_pdf}\n  PNG -> {out_png}")


if __name__ == "__main__":
    out_dir = Path("/Users/zhoujun/Documents/科研/01_开题报告")
    if len(sys.argv) > 1:
        out_dir = Path(sys.argv[1])
    generate_project_demo(
        str(out_dir / "MgCl2_Project_Nature_Benchmark_Demo.pdf"),
        str(out_dir / "MgCl2_Project_Nature_Benchmark_Demo.png"),
    )
