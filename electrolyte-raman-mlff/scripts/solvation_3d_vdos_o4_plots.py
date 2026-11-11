#!/usr/bin/env python3
r"""
Extended Real-Data & 3D Structural Plotting Toolkit for `electrolyte-raman-mlff`:

Implements the 5 new reference paradigms requested for the MgCl2(+H3PO4) project:
  1. [3D Solvation Clusters + Force Vectors] — Jiang et al., J. Energy Chem. 109, 466 (2025) Table 1:
     Pure-vector depth-sorted glossy CPK ball-and-stick renderer for `[Mg(H2O)6]2+` (SSIP),
     `[MgCl(H2O)5]+` (CIP), `[Mg2Cl3(H2O)7]+` (S-cMISS), and `[Mg4Cl4(H2O)12]4+` (L-cMISS),
     with 3D-projected force vectors (`DFT` vs `Leg A` vs `O4`).
  2. [Cross-Concentration 3D Periodic Simulation Boxes] — Jiang et al., J. Energy Chem. 2025 Fig. 2a:
     Dashed regime containers (`Dilute SIW 1 m` -> `Concentrated 5 m` -> `Ultra-High WIS 12 m`)
     with 3D isometric wireframe unit cells and local zoomed callouts; supports loading `.gro`,
     PWmat `atom.config`, and `MOVEMENT` files directly.
  3. [Water Structure g_O-O(r) + Waterfall VDOS Shift] — Wang et al., Nat. Commun. 17, 1226 (2026) Fig. 3:
     Real `0, 1, 3, 5 m SG15-PBE AIMD` `g_O-O(r)`, multiscale `CN` & H-bond network transition,
     and gradient-blue waterfall VDOS stacks (`O-H stretch 2750-3900 cm-1` & `Low-freq 120-960 cm-1`)
     with semi-transparent wide shift arrows and embedded 3D mini ball-and-stick motifs.
  4. [Short-Range Repulsive Potential Wall beta*V_rep(r)] — Tazi et al., J. Chem. Phys. 136, 114507 (2012) Fig. 2b:
     Exact analytical `Mg2+-Ow` and `Mg2+-Cl-` repulsive walls (`1.5-3.5 A`, `0-40 k_BT`) comparing
     `iPMV 0.75` (brick wall), `Leg A (IOD 0.80)`, `ECCions81` (collapse), and `O4 Balanced / Soft`.
  5. [Sim. vs Exp. Density Parity & Forward-MD Closed Loop] — Zheng et al. (ByteFF-Pol), Nat. Commun. (2026) Fig. 4a,f:
     Macroscopic density parity (`0-5 m MgCl2`, `298.15 K`) with Pearson `r` & MAE plus two-tier
     structural/force closed-loop benchmark bars.

All outputs pass `sanitize_svg_for_ppt()` and `audit_svg_ppt_compatibility()` (zero `<tspan>`,
zero `<clipPath>`, 100% Arial glyphs) and automatically export OriginPro `.xlsx` + `.csv` workbooks.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
from matplotlib.ticker import AutoMinorLocator

SCRIPT_DIR = Path(__file__).resolve().parent
ASSET_DIR = SCRIPT_DIR.parent / "assets"
for _p in (str(SCRIPT_DIR), str(ASSET_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from color_palettes import (
    BALOS_HBOND_SHELLS,
    BYTEFF_DENSITY_MODELS,
    JIANG_CPK_3D,
    TAZI_REPULSIVE_WALL,
    WANG_WATERFALL_BLUES,
)
from electrolyte_plots import (
    add_panel_label,
    apply_electrolyte_nature_style,
    save_publication_figure,
)
from ppt_origin_export import (
    OriginColumn,
    build_editable_svg_pptx,
    clip_curve_to_box,
    clip_scatter_to_box,
    write_origin_csv,
    write_origin_xlsx,
)


# ==============================================================================
# 1. Pure-Vector 3D CPK Ball-and-Stick, Force Vector & Periodic Cube Engine
# ==============================================================================

def project_3d_points(
    coords: np.ndarray,
    elev: float = 22.0,
    azim: float = -38.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Orthographic 3D -> 2D camera projection returning `(x_2d, y_2d, z_depth)`."""
    pts = np.asarray(coords, dtype=float)
    th = math.radians(azim)
    ph = math.radians(elev)
    ex = np.array([-math.sin(th), math.cos(th), 0.0])
    ey = np.array([-math.sin(ph) * math.cos(th), -math.sin(ph) * math.sin(th), math.cos(ph)])
    ez = np.array([math.cos(ph) * math.cos(th), math.cos(ph) * math.sin(th), math.sin(ph)])
    return pts @ ex, pts @ ey, pts @ ez


def _stick_polygon(
    p0: np.ndarray,
    p1: np.ndarray,
    half_width: float,
) -> np.ndarray | None:
    v = p1 - p0
    length = float(np.hypot(v[0], v[1]))
    if length < 1e-6:
        return None
    n = np.array([-v[1] / length, v[0] / length]) * half_width
    return np.array([p0 + n, p1 + n, p1 - n, p0 - n])


def draw_3d_cluster(
    ax: plt.Axes,
    symbols: Sequence[str],
    coords: np.ndarray,
    *,
    bonds: Sequence[tuple[int, int]] | None = None,
    dashed_bonds: Sequence[tuple[int, int]] | None = None,
    force_vectors: Sequence[tuple[int, Sequence[float], str, str, str | None] | tuple[int, Sequence[float], str, str, str | None, tuple[float, float]]] | None = None,
    elev: float = 22.0,
    azim: float = -38.0,
    atom_scale: float = 1.0,
    bond_width: float = 0.085,
    force_scale: float = 0.85,
    padding: float = 0.72,
    alpha_atoms: Sequence[float] | None = None,
) -> None:
    """
    Render a depth-sorted, pure-vector glossy 3D ball-and-stick cluster (with optional 3D force
    arrows) onto `ax`. Sets `ax.set_aspect('equal')` and `ax.axis('off')` for true spherical atoms.

    `force_vectors`: list of `(atom_idx, vec_3d, hex_color, linestyle, text_tag)`.
    """
    coords = np.asarray(coords, dtype=float)
    # Center cluster around origin
    centered = coords - np.mean(coords, axis=0, keepdims=True)
    x2, y2, z_depth = project_3d_points(centered, elev=elev, azim=azim)
    radii = np.array([JIANG_CPK_3D.get(sym, JIANG_CPK_3D["O"])["radius"] * atom_scale for sym in symbols])

    # Build depth-sorted draw queue: (z_key, kind, payload)
    queue: list[tuple[float, str, Any]] = []

    if bonds:
        for i, j in bonds:
            p_i = np.array([x2[i], y2[i]])
            p_j = np.array([x2[j], y2[j]])
            d_ij = p_j - p_i
            dist_2d = float(np.hypot(d_ij[0], d_ij[1]))
            if dist_2d > 1e-4:
                u_ij = d_ij / dist_2d
                p_start = p_i + u_ij * min(0.45 * radii[i], 0.35 * dist_2d)
                p_end = p_j - u_ij * min(0.45 * radii[j], 0.35 * dist_2d)
                z_bond = 0.5 * (z_depth[i] + z_depth[j]) - 0.06
                a_bond = 1.0 if alpha_atoms is None else min(alpha_atoms[i], alpha_atoms[j])
                is_coord = ("Mg" in (symbols[i], symbols[j])) and ("Cl" in (symbols[i], symbols[j]) or "O" in (symbols[i], symbols[j]))
                queue.append((z_bond, "bond", (p_start, p_end, bond_width * (1.08 if is_coord else 0.85), is_coord, a_bond)))

    if dashed_bonds:
        for i, j in dashed_bonds:
            p_i = np.array([x2[i], y2[i]])
            p_j = np.array([x2[j], y2[j]])
            z_hb = 0.5 * (z_depth[i] + z_depth[j]) - 0.10
            queue.append((z_hb, "dashed", (p_i, p_j)))

    for idx, sym in enumerate(symbols):
        a_val = 1.0 if alpha_atoms is None else float(alpha_atoms[idx])
        queue.append((float(z_depth[idx]), "atom", (idx, sym, x2[idx], y2[idx], radii[idx], a_val)))

    queue.sort(key=lambda item: item[0])

    z_order_base = 2
    for step_idx, (_, kind, payload) in enumerate(queue):
        zo = z_order_base + step_idx * 0.01
        if kind == "dashed":
            p_i, p_j = payload
            ax.plot([p_i[0], p_j[0]], [p_i[1], p_j[1]], ls="--", lw=0.95, color="#334155", zorder=zo)
        elif kind == "bond":
            p_s, p_e, hw, is_coord, a_b = payload
            poly_pts = _stick_polygon(p_s, p_e, hw)
            if poly_pts is not None:
                base_col = "#64748B" if is_coord else "#94A3B8"
                hi_col = "#CBD5E1" if is_coord else "#E2E8F0"
                ax.add_patch(Polygon(poly_pts, closed=True, facecolor=base_col, edgecolor="#334155", lw=0.45, alpha=a_b, zorder=zo))
                core_pts = _stick_polygon(p_s, p_e, hw * 0.36)
                if core_pts is not None:
                    ax.add_patch(Polygon(core_pts, closed=True, facecolor=hi_col, edgecolor="none", alpha=a_b * 0.85, zorder=zo + 0.002))
        elif kind == "atom":
            _, sym, cx, cy, rad, a_val = payload
            spec = JIANG_CPK_3D.get(sym, JIANG_CPK_3D["O"])
            lw_rim = 0.75 if sym in ("Mg", "Cl") else 0.55
            ax.add_patch(Circle((cx, cy), radius=rad, facecolor=spec["core"], edgecolor=spec["rim"], lw=lw_rim, alpha=a_val, zorder=zo))
            ax.add_patch(Circle((cx - 0.14 * rad, cy + 0.14 * rad), radius=0.70 * rad, facecolor=spec["mid"], edgecolor="none", alpha=a_val * 0.90, zorder=zo + 0.002))
            ax.add_patch(Circle((cx - 0.30 * rad, cy + 0.30 * rad), radius=0.23 * rad, facecolor=spec["spec"], edgecolor="none", alpha=a_val * 0.94, zorder=zo + 0.004))

    # Overlay 3D-projected force vectors on top of atoms
    all_x = list(x2 - radii) + list(x2 + radii)
    all_y = list(y2 - radii) + list(y2 + radii)

    if force_vectors:
        zero_proj_x, zero_proj_y, _ = project_3d_points(np.zeros((1, 3)), elev=elev, azim=azim)
        for f_idx, f_spec in enumerate(force_vectors):
            if len(f_spec) == 6:
                a_idx, vec3, col_f, ls_f, tag_txt, lbl_off = f_spec  # type: ignore[misc]
            else:
                a_idx, vec3, col_f, ls_f, tag_txt = f_spec  # type: ignore[misc]
                lbl_off = None
            vx, vy, _ = project_3d_points(np.asarray([vec3], dtype=float), elev=elev, azim=azim)
            dx = float(vx[0] - zero_proj_x[0]) * force_scale
            dy = float(vy[0] - zero_proj_y[0]) * force_scale
            mag2 = math.hypot(dx, dy)
            if mag2 < 1e-4:
                continue
            ux, uy = dx / mag2, dy / mag2
            sx = float(x2[a_idx]) + ux * (radii[a_idx] * 0.72)
            sy = float(y2[a_idx]) + uy * (radii[a_idx] * 0.72)
            ex_f = sx + dx
            ey_f = sy + dy
            arr = FancyArrowPatch(
                (sx, sy), (ex_f, ey_f),
                arrowstyle="-|>,head_length=3.6,head_width=2.1",
                mutation_scale=1.0,
                linewidth=1.45,
                linestyle=ls_f,
                color=col_f,
                zorder=z_order_base + len(queue) + 2 + f_idx,
            )
            ax.add_patch(arr)
            all_x.append(ex_f)
            all_y.append(ey_f)
            if tag_txt:
                tx = ex_f + (lbl_off[0] if lbl_off is not None else 0.12 * ux)
                ty = ey_f + (lbl_off[1] if lbl_off is not None else 0.12 * uy)
                ax.text(
                    tx, ty, tag_txt,
                    fontsize=5.6, fontweight="bold", color=col_f,
                    ha="left" if ux >= -0.05 else "right",
                    va="center",
                    bbox=dict(boxstyle="round,pad=0.08", facecolor="white", edgecolor="none", alpha=0.82),
                    zorder=z_order_base + len(queue) + 5 + f_idx,
                )
                all_x.append(tx + (1.15 if ux >= -0.05 else -1.15))
                all_y.append(ty)

    xmin, xmax = min(all_x) - padding, max(all_x) + padding
    ymin, ymax = min(all_y) - padding, max(all_y) + padding
    cx_mid = 0.5 * (xmin + xmax)
    cy_mid = 0.5 * (ymin + ymax)
    half_span = 0.5 * max(xmax - xmin, ymax - ymin)
    ax.set_xlim(cx_mid - half_span, cx_mid + half_span)
    ax.set_ylim(cy_mid - half_span, cy_mid + half_span)
    ax.set_aspect("equal")
    ax.axis("off")


def embed_3d_motif_inset(
    parent_ax: plt.Axes,
    bbox_axes: Sequence[float],
    symbols: Sequence[str],
    coords: np.ndarray,
    *,
    bonds: Sequence[tuple[int, int]] | None = None,
    dashed_bonds: Sequence[tuple[int, int]] | None = None,
    elev: float = 20.0,
    azim: float = -35.0,
    atom_scale: float = 0.92,
    padding: float = 0.45,
) -> plt.Axes:
    """Embed a transparent, circular-atom 3D ball-and-stick motif directly inside any 2D plot."""
    ins = parent_ax.inset_axes(list(bbox_axes), zorder=4)
    ins.patch.set_alpha(0.0)
    draw_3d_cluster(
        ins, symbols, coords,
        bonds=bonds, dashed_bonds=dashed_bonds,
        elev=elev, azim=azim,
        atom_scale=atom_scale,
        bond_width=0.08,
        padding=padding,
    )
    return ins


# ==============================================================================
# Canonical Solvation Clusters & Periodic Simulation Cell Builders / Loaders
# ==============================================================================

def _append_water(
    symbols: list[str],
    coords: list[np.ndarray],
    bonds: list[tuple[int, int]],
    mg_idx: int,
    mg_pos: np.ndarray,
    direction: Sequence[float],
    r_mgo: float = 2.09,
    tilt_deg: float = 0.0,
) -> int:
    """Attach an H2O molecule to `mg_pos` along `direction` with outward-pointing hydrogens."""
    u = np.asarray(direction, dtype=float)
    u = u / np.linalg.norm(u)
    o_pos = mg_pos + r_mgo * u
    # Construct orthogonal vector perp to u
    ref = np.array([0.0, 0.0, 1.0]) if abs(u[2]) < 0.85 else np.array([1.0, 0.0, 0.0])
    v1 = np.cross(u, ref)
    v1 = v1 / np.linalg.norm(v1)
    v2 = np.cross(u, v1)
    ang = math.radians(tilt_deg)
    plane_vec = math.cos(ang) * v1 + math.sin(ang) * v2

    half_hoh = math.radians(52.25)
    r_oh = 0.97
    h1_pos = o_pos + r_oh * (math.cos(half_hoh) * u + math.sin(half_hoh) * plane_vec)
    h2_pos = o_pos + r_oh * (math.cos(half_hoh) * u - math.sin(half_hoh) * plane_vec)

    o_idx = len(symbols)
    symbols.extend(["O", "H", "H"])
    coords.extend([o_pos, h1_pos, h2_pos])
    bonds.append((mg_idx, o_idx))
    bonds.append((o_idx, o_idx + 1))
    bonds.append((o_idx, o_idx + 2))
    return o_idx


def build_cluster_ssip() -> tuple[list[str], np.ndarray, list[tuple[int, int]]]:
    """Octahedral `[Mg(H2O)6]2+` (`Mg_SSIP` / F-sMISS)."""
    syms = ["Mg"]
    coords = [np.zeros(3)]
    bonds: list[tuple[int, int]] = []
    dirs = [
        ([1, 0, 0], 25.0), ([-1, 0, 0], -25.0),
        ([0, 1, 0], 65.0), ([0, -1, 0], -65.0),
        ([0, 0, 1], 15.0), ([0, 0, -1], 105.0),
    ]
    for d, tilt in dirs:
        _append_water(syms, coords, bonds, 0, coords[0], d, r_mgo=2.09, tilt_deg=tilt)
    return syms, np.array(coords), bonds


def build_cluster_cip() -> tuple[list[str], np.ndarray, list[tuple[int, int]]]:
    """Contact ion pair `[MgCl(H2O)5]+` (`Mg_CIP / Cl_CIP`)."""
    syms = ["Mg", "Cl"]
    coords = [np.zeros(3), np.array([2.41, 0.18, 0.12])]
    bonds: list[tuple[int, int]] = [(0, 1)]
    dirs = [
        ([-1, -0.08, 0], 30.0),
        ([0, 1, 0.1], 65.0), ([0, -1, -0.1], -55.0),
        ([-0.08, 0, 1], 15.0), ([-0.08, 0, -1], 105.0),
    ]
    for d, tilt in dirs:
        _append_water(syms, coords, bonds, 0, coords[0], d, r_mgo=2.09, tilt_deg=tilt)
    return syms, np.array(coords), bonds


def build_cluster_binuclear_agg() -> tuple[list[str], np.ndarray, list[tuple[int, int]]]:
    """Short-chain chloride-bridged dimer `[Mg2(mu-Cl)2Cl(H2O)7]+` (`S-cMISS`)."""
    mg1 = np.array([-1.76, 0.0, 0.0])
    mg2 = np.array([1.76, 0.0, 0.0])
    cl_b1 = np.array([0.0, 1.66, 0.28])
    cl_b2 = np.array([0.0, -1.66, -0.28])
    cl_t = np.array([3.98, 0.55, 0.65])
    syms = ["Mg", "Mg", "Cl", "Cl", "Cl"]
    coords = [mg1, mg2, cl_b1, cl_b2, cl_t]
    bonds: list[tuple[int, int]] = [(0, 2), (0, 3), (1, 2), (1, 3), (1, 4)]

    # 4 terminal waters on Mg1, 3 terminal waters on Mg2
    for d, t in [([-1, 0.55, 0.3], 20), ([-1, -0.55, -0.3], -35), ([-0.25, 0.2, 1.0], 50), ([-0.25, -0.2, -1.0], 110)]:
        _append_water(syms, coords, bonds, 0, mg1, d, r_mgo=2.10, tilt_deg=t)
    for d, t in [([0.95, -0.65, -0.35], 40), ([0.25, 0.25, 1.0], -20), ([0.25, -0.2, -1.0], 95)]:
        _append_water(syms, coords, bonds, 1, mg2, d, r_mgo=2.10, tilt_deg=t)
    return syms, np.array(coords), bonds


def build_cluster_tetranuclear_agg() -> tuple[list[str], np.ndarray, list[tuple[int, int]]]:
    """Long-chain / ring polynuclear bridge `[Mg4(mu-Cl)4(H2O)12]4+` (`L-cMISS`)."""
    r_mg = 2.05
    mgs = [
        np.array([-r_mg, -r_mg, 0.16]),
        np.array([r_mg, -r_mg, -0.16]),
        np.array([r_mg, r_mg, 0.16]),
        np.array([-r_mg, r_mg, -0.16]),
    ]
    cls = [
        np.array([0.0, -2.52, -0.22]),
        np.array([2.52, 0.0, 0.22]),
        np.array([0.0, 2.52, -0.22]),
        np.array([-2.52, 0.0, 0.22]),
    ]
    syms = ["Mg"] * 4 + ["Cl"] * 4
    coords = list(mgs) + list(cls)
    bonds: list[tuple[int, int]] = [
        (0, 4), (4, 1),
        (1, 5), (5, 2),
        (2, 6), (6, 3),
        (3, 7), (7, 0),
    ]
    for m_idx, mp in enumerate(mgs):
        outward = mp / np.linalg.norm(mp[:2])
        dirs = [
            (outward + np.array([0.0, 0.0, 0.15]), 25.0),
            (0.35 * outward + np.array([0.0, 0.0, 1.0]), 70.0),
            (0.35 * outward + np.array([0.0, 0.0, -1.0]), -50.0),
        ]
        for d, t in dirs:
            _append_water(syms, coords, bonds, m_idx, mp, d, r_mgo=2.11, tilt_deg=t)
    return syms, np.array(coords), bonds


def build_motif_water_dimer_hbond() -> tuple[list[str], np.ndarray, list[tuple[int, int]], list[tuple[int, int]]]:
    """Tetrahedral water-water H-bonded motif (`O-H...O`, r_OO = 2.75 A)."""
    syms = ["O", "H", "H", "O", "H", "H"]
    coords = np.array([
        [0.0, 0.0, 0.0],
        [0.96, 0.08, 0.0],
        [-0.32, 0.90, 0.12],
        [2.74, 0.15, 0.0],
        [3.18, 0.96, 0.28],
        [3.22, -0.58, -0.35],
    ])
    bonds = [(0, 1), (0, 2), (3, 4), (3, 5)]
    dashed = [(1, 3)]
    return syms, coords, bonds, dashed


def build_motif_water_chloride_hbond() -> tuple[list[str], np.ndarray, list[tuple[int, int]], list[tuple[int, int]]]:
    """Concentrated water-chloride H-bonded motif (`O-H...Cl-`, r_OCl = 3.12 A)."""
    syms = ["O", "H", "H", "Cl"]
    coords = np.array([
        [0.0, 0.0, 0.0],
        [0.97, 0.05, 0.0],
        [-0.30, 0.91, 0.15],
        [3.10, 0.12, 0.0],
    ])
    bonds = [(0, 1), (0, 2)]
    dashed = [(1, 3)]
    return syms, coords, bonds, dashed


def load_periodic_box_from_file(path: str | Path) -> tuple[float, list[str], np.ndarray]:
    """
    Parse a periodic cubic simulation box `(L_Angstrom, symbols, cart_coords_Angstrom)` from
    either PWmat `atom.config` / `MOVEMENT` or GROMACS `.gro`.
    """
    p = Path(path)
    lines = p.read_text(errors="replace").splitlines()
    z_map = {1: "H", 8: "O", 12: "Mg", 15: "P", 17: "Cl"}

    if p.suffix.lower() == ".gro":
        nat = int(lines[1].strip())
        box_tokens = [float(x) for x in lines[2 + nat].split()]
        L_A = box_tokens[0] * 10.0
        syms, cart = [], []
        for ln in lines[2 : 2 + nat]:
            atom_name = ln[10:15].strip()
            if atom_name.startswith(("LP", "EP", "MW")):
                continue
            parts = ln[20:].split()
            xyz_A = [float(parts[0]) * 10.0, float(parts[1]) * 10.0, float(parts[2]) * 10.0]
            if atom_name.startswith(("MG", "Mg")):
                syms.append("Mg")
            elif atom_name.startswith(("CL", "Cl")):
                syms.append("Cl")
            elif atom_name.startswith("O"):
                syms.append("O")
            elif atom_name.startswith("P"):
                syms.append("P")
            else:
                syms.append("H")
            cart.append(xyz_A)
        arr = np.asarray(cart, dtype=float) % L_A
        return L_A, syms, arr

    # PWmat atom.config / first frame of MOVEMENT
    nat = int(lines[0].split()[0])
    lat_i = next(i for i, l in enumerate(lines) if l.strip().upper().startswith("LATTICE")) + 1
    pos_i = next(i for i, l in enumerate(lines) if l.strip().upper().startswith("POSITION")) + 1
    L_A = float(lines[lat_i].split()[0])
    syms, frac = [], []
    for ln in lines[pos_i : pos_i + nat]:
        q = ln.split()
        syms.append(z_map.get(int(q[0]), "O"))
        frac.append([float(q[1]), float(q[2]), float(q[3])])
    cart_arr = (np.asarray(frac, dtype=float) % 1.0) * L_A
    return L_A, syms, cart_arr


def build_representative_pbe_box(
    conc_m: int,
    seed: int = 42,
) -> tuple[float, list[str], np.ndarray, list[tuple[int, int]]]:
    """
    Construct a steric-clash-free periodic `56 H2O + n MgCl2` unit cell matching the exact
    SG15-PBE AIMD & SCF patch cell parameters (`1 m`: L=11.96 A, `5 m`: L=12.39 A, `12 m`: L=13.12 A).
    """
    rng = np.random.default_rng(seed + conc_m)
    spec = {
        1: (11.961, 1, 0),    # 1 MgCl2 + 56 H2O, 100% SSIP
        5: (12.391, 5, 0),    # 5 MgCl2 + 56 H2O, concentrated SSIP / solvent-shared Cl-
        12: (13.120, 12, 8),  # 12 MgCl2 + 56 H2O, WIS CIP + AGG bridging network
    }[conc_m]
    L, n_mg, n_bridged = spec

    syms: list[str] = []
    coords: list[np.ndarray] = []
    bonds: list[tuple[int, int]] = []

    def _too_close(pt: np.ndarray, min_d: float) -> bool:
        if not coords:
            return False
        arr = np.asarray(coords)
        diff = arr - pt[None, :]
        diff -= L * np.rint(diff / L)
        return bool(np.min(np.linalg.norm(diff, axis=-1)) < min_d)

    # Place Mg2+ ions
    mg_indices: list[int] = []
    if conc_m == 1:
        mg_pts = [np.array([0.50 * L, 0.50 * L, 0.50 * L])]
    elif conc_m == 5:
        mg_pts = [
            np.array([0.24, 0.26, 0.28]) * L,
            np.array([0.74, 0.25, 0.72]) * L,
            np.array([0.28, 0.75, 0.70]) * L,
            np.array([0.75, 0.74, 0.28]) * L,
            np.array([0.52, 0.50, 0.52]) * L,
        ]
    else:
        # 12 m WIS: include a central Mg-Cl-Mg-Cl percolating chain + dispersedCIPs
        mg_pts = [
            np.array([0.24, 0.48, 0.50]) * L,
            np.array([0.50, 0.52, 0.52]) * L,
            np.array([0.76, 0.48, 0.48]) * L,
            np.array([0.50, 0.24, 0.50]) * L,
            np.array([0.50, 0.78, 0.52]) * L,
            np.array([0.22, 0.22, 0.24]) * L,
            np.array([0.78, 0.22, 0.26]) * L,
            np.array([0.22, 0.78, 0.25]) * L,
            np.array([0.78, 0.78, 0.26]) * L,
            np.array([0.24, 0.24, 0.78]) * L,
            np.array([0.76, 0.26, 0.78]) * L,
            np.array([0.26, 0.76, 0.78]) * L,
        ]

    for mp in mg_pts:
        mg_indices.append(len(syms))
        syms.append("Mg")
        coords.append(mp)

    # Place Cl- ions (solvent-separated for 1m & 5m; inner-shell bridging/CIP for 12m)
    n_cl = 2 * n_mg
    if conc_m == 12:
        bridge_pairs = [(0, 1), (1, 2), (1, 3), (1, 4), (5, 6), (7, 8)]
        for i_m, j_m in bridge_pairs:
            mid = 0.5 * (coords[i_m] + coords[j_m]) + np.array([0.0, 0.35, 0.55])
            cl_idx = len(syms)
            syms.append("Cl")
            coords.append(mid % L)
            bonds.append((i_m, cl_idx))
            bonds.append((j_m, cl_idx))
        while sum(1 for s in syms if s == "Cl") < n_cl:
            host_mg = mg_indices[len(syms) % len(mg_indices)]
            u = rng.normal(size=3)
            u /= np.linalg.norm(u)
            cand = (coords[host_mg] + 2.42 * u) % L
            if not _too_close(cand, 2.05):
                cl_idx = len(syms)
                syms.append("Cl")
                coords.append(cand)
                bonds.append((host_mg, cl_idx))
    else:
        attempts = 0
        while sum(1 for s in syms if s == "Cl") < n_cl and attempts < 800:
            attempts += 1
            cand = rng.uniform(0.08 * L, 0.92 * L, size=3)
            # Keep Cl- outside 3.7 A of Mg2+ in 1m & 5m (100% SSIP in PBE AIMD!)
            d_mg = min(np.linalg.norm((coords[m] - cand) - L * np.rint((coords[m] - cand) / L)) for m in mg_indices)
            if d_mg >= 3.65 and not _too_close(cand, 2.45):
                syms.append("Cl")
                coords.append(cand)

    # Coordinate first-shell waters around Mg2+, then fill remaining bulk waters up to 56 H2O
    n_waters = 0
    oct_dirs = [[1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1], [0, 0, -1]]
    for m_i in mg_indices:
        target_w = 6 if conc_m <= 5 else 3
        added = 0
        for d_vec in oct_dirs:
            if added >= target_w or n_waters >= 56:
                break
            o_cand = (coords[m_i] + 2.09 * np.asarray(d_vec, dtype=float)) % L
            if not _too_close(o_cand, 1.75):
                u = np.asarray(d_vec, dtype=float)
                o_idx = len(syms)
                h1 = (o_cand + np.array([0.58, 0.58, 0.48]) * 0.96) % L
                h2 = (o_cand + np.array([-0.58, 0.58, -0.48]) * 0.96) % L
                syms.extend(["O", "H", "H"])
                coords.extend([o_cand, h1, h2])
                if np.linalg.norm(coords[m_i] - o_cand) < 3.2:
                    bonds.append((m_i, o_idx))
                    bonds.append((o_idx, o_idx + 1))
                    bonds.append((o_idx, o_idx + 2))
                added += 1
                n_waters += 1

    attempts = 0
    while n_waters < 56 and attempts < 2000:
        attempts += 1
        o_cand = rng.uniform(0.06 * L, 0.94 * L, size=3)
        if not _too_close(o_cand, 2.05):
            ang = rng.uniform(0, 2 * math.pi)
            h1 = o_cand + 0.96 * np.array([math.cos(ang), math.sin(ang), 0.35])
            h2 = o_cand + 0.96 * np.array([math.cos(ang + 1.82), math.sin(ang + 1.82), -0.35])
            o_idx = len(syms)
            syms.extend(["O", "H", "H"])
            coords.extend([o_cand, h1, h2])
            bonds.append((o_idx, o_idx + 1))
            bonds.append((o_idx, o_idx + 2))
            n_waters += 1

    return L, syms, np.asarray(coords, dtype=float), bonds


def draw_3d_periodic_box(
    ax: plt.Axes,
    L: float,
    symbols: Sequence[str],
    coords: np.ndarray,
    *,
    bonds: Sequence[tuple[int, int]] | None = None,
    elev: float = 20.0,
    azim: float = -36.0,
    water_alpha: float = 0.52,
) -> None:
    """
    Render a 3D isometric wireframe cubic cell `[0, L]^3` with depth-sorted back edges,
    glossy CPK ions/waters, and crisp front edges (Jiang JEC 2025 Fig. 2a style).
    """
    centered = np.asarray(coords, dtype=float) - 0.5 * L
    corners = np.array([
        [sx, sy, sz]
        for sx in (-0.5 * L, 0.5 * L)
        for sy in (-0.5 * L, 0.5 * L)
        for sz in (-0.5 * L, 0.5 * L)
    ])
    edges = [
        (0, 1), (0, 2), (0, 4),
        (1, 3), (1, 5), (2, 3),
        (2, 6), (3, 7), (4, 5),
        (4, 6), (5, 7), (6, 7),
    ]
    cx2, cy2, cz_d = project_3d_points(corners, elev=elev, azim=azim)
    min_corner = int(np.argmin(cz_d))

    # Back 3 edges connected to the farthest corner
    for i, j in edges:
        if i == min_corner or j == min_corner:
            ax.plot([cx2[i], cx2[j]], [cy2[i], cy2[j]], color="#94A3B8", ls="--", lw=0.8, zorder=1)

    alphas = [1.0 if s in ("Mg", "Cl", "P") else water_alpha for s in symbols]
    x2, y2, z_d = project_3d_points(centered, elev=elev, azim=azim)
    radii = np.array([JIANG_CPK_3D.get(s, JIANG_CPK_3D["O"])["radius"] * 0.85 for s in symbols])

    q: list[tuple[float, str, Any]] = []
    if bonds:
        for i, j in bonds:
            pi, pj = np.array([x2[i], y2[i]]), np.array([x2[j], y2[j]])
            if np.linalg.norm(centered[i] - centered[j]) < 3.4:
                a_b = 0.95 if ("Mg" in (symbols[i], symbols[j])) else water_alpha * 0.75
                q.append((0.5 * (z_d[i] + z_d[j]) - 0.05, "bond", (pi, pj, a_b)))
    for idx, sym in enumerate(symbols):
        q.append((float(z_d[idx]), "atom", (sym, x2[idx], y2[idx], radii[idx], alphas[idx])))
    q.sort(key=lambda t: t[0])

    for k_idx, (_, kind, pay) in enumerate(q):
        zo = 2.0 + k_idx * 0.005
        if kind == "bond":
            pi, pj, a_b = pay
            ax.plot([pi[0], pj[0]], [pi[1], pj[1]], color="#64748B", lw=0.75, alpha=a_b, zorder=zo)
        else:
            sym, px, py, rad, a_v = pay
            sp = JIANG_CPK_3D.get(sym, JIANG_CPK_3D["O"])
            ax.add_patch(Circle((px, py), radius=rad, facecolor=sp["core"], edgecolor=sp["rim"], lw=0.45, alpha=a_v, zorder=zo))
            ax.add_patch(Circle((px - 0.26 * rad, py + 0.26 * rad), radius=0.25 * rad, facecolor=sp["spec"], edgecolor="none", alpha=a_v * 0.9, zorder=zo + 0.001))

    # Front 9 edges of periodic box
    for i, j in edges:
        if i != min_corner and j != min_corner:
            ax.plot([cx2[i], cx2[j]], [cy2[i], cy2[j]], color="#334155", ls="-", lw=0.95, zorder=20)

    ax.set_xlim(-1.05 * L, 1.05 * L)
    ax.set_ylim(-1.14 * L, 1.04 * L)
    ax.set_aspect("equal")
    ax.axis("off")


# ==============================================================================
# 2. Waterfall VDOS + Semi-Transparent Wide Shift Arrow (Wang Nat. Commun. 2026)
# ==============================================================================

def _smooth_1d(y: np.ndarray, radius: int = 2) -> np.ndarray:
    """Gentle Gaussian kernel smoothing preserving peak area and centroid."""
    if radius <= 0 or len(y) < 2 * radius + 1:
        return y.copy()
    kx = np.arange(-radius, radius + 1, dtype=float)
    kernel = np.exp(-0.5 * (kx / (0.65 * radius)) ** 2)
    kernel /= np.sum(kernel)
    ypad = np.pad(y, radius, mode="edge")
    return np.convolve(ypad, kernel, mode="valid")


def _draw_wide_shift_arrow(
    ax: plt.Axes,
    p_start: tuple[float, float],
    p_end: tuple[float, float],
    *,
    shaft_width_frac: float = 0.11,
    head_width_frac: float = 0.21,
    head_len_frac: float = 0.22,
    color: str = "#38BDF8",
    alpha: float = 0.28,
) -> None:
    """Draw a semi-transparent wide block arrow in Axes fraction coordinates `(0..1, 0..1)`."""
    p0 = np.asarray(p_start, dtype=float)
    p1 = np.asarray(p_end, dtype=float)
    v = p1 - p0
    L = float(np.hypot(v[0], v[1]))
    if L < 1e-4:
        return
    u = v / L
    n = np.array([-u[1], u[0]])
    hl = min(head_len_frac, 0.42 * L)
    neck = p1 - hl * u
    sw = 0.5 * shaft_width_frac
    hw = 0.5 * head_width_frac
    pts = np.array([
        p0 + sw * n,
        neck + sw * n,
        neck + hw * n,
        p1,
        neck - hw * n,
        neck - sw * n,
        p0 - sw * n,
    ])
    poly = Polygon(pts, closed=True, transform=ax.transAxes, facecolor=color, edgecolor="none", alpha=alpha, zorder=1.5)
    ax.add_patch(poly)


def plot_waterfall_vdos_with_shift_arrow(
    ax: plt.Axes,
    freq_cm1: np.ndarray,
    series: Sequence[tuple[str, np.ndarray, str]],
    *,
    xlim: tuple[float, float],
    offset_step: float = 0.88,
    top_headroom: float = 1.62,
    smooth_radius: int = 2,
    arrow_axes_start: tuple[float, float] = (0.48, 0.08),
    arrow_axes_end: tuple[float, float] = (0.58, 0.88),
    panel_title: str = r"$\mathrm{MgCl_2:H_2O}$",
    legend_loc: str = "upper left",
) -> None:
    """
    Wang et al. (Nat. Commun. 2026, Fig. 3e-f) Gradient-Blue Waterfall VDOS Stack
    with a Semi-Transparent Sky-Blue Shift Arrow.
    """
    mask = (freq_cm1 >= xlim[0]) & (freq_cm1 <= xlim[1])
    x_sub = freq_cm1[mask]
    n_curves = len(series)
    ylim = (-0.10, (n_curves - 1) * offset_step + top_headroom)

    _draw_wide_shift_arrow(ax, arrow_axes_start, arrow_axes_end, color="#38BDF8", alpha=0.28)

    for idx, (lbl, raw_y, col) in enumerate(series):
        y_seg = _smooth_1d(np.asarray(raw_y, dtype=float)[mask], radius=smooth_radius)
        ymax = float(np.max(y_seg)) if len(y_seg) else 1.0
        y_norm = (y_seg / ymax if ymax > 0 else y_seg) + idx * offset_step
        xc, yc = clip_curve_to_box(x_sub, y_norm, xlim, ylim)
        ax.plot(xc, yc, color=col, lw=1.45, label=lbl, zorder=3 + idx * 0.1)

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_yticks([])
    ax.set_xlabel(r"Wavenumber ($\mathrm{cm^{-1}}$)")
    ax.set_ylabel("VDOS (arb. units)")
    ax.set_title(panel_title, fontsize=8.2, fontweight="bold", pad=5.0, color="#0F172A")
    leg = ax.legend(loc=legend_loc, frameon=True, edgecolor="black", fancybox=False, fontsize=6.1, borderpad=0.25, handlelength=1.4)
    leg.get_frame().set_linewidth(0.7)


# ==============================================================================
# 3. Analytical Repulsive Potential Wall & ByteFF-Pol Density Parity Primitives
# ==============================================================================

def lj_beta_vrep(r_ang: np.ndarray, sigma_nm: float, eps_kj: float, kbt_kj: float = 2.47896) -> np.ndarray:
    """Compute dimensionless Pauli repulsive wall `beta * V_rep(r) = 4 * eps * (sigma / r)^12 / (k_B T)`."""
    sigma_A = sigma_nm * 10.0
    return (4.0 * eps_kj * (sigma_A / np.asarray(r_ang, dtype=float)) ** 12) / kbt_kj


def plot_tazi_repulsive_wall(
    ax: plt.Axes,
    r_ang: np.ndarray,
    models: Sequence[tuple[str, np.ndarray, str, str, float]],
    *,
    xlim: tuple[float, float] = (1.5, 3.5),
    ylim: tuple[float, float] = (0.0, 40.0),
    contact_band: tuple[float, float, str] | None = None,
    xlabel: str = r"$r\ (\mathrm{\AA})$",
    ylabel: str = r"$\beta V_{\mathrm{rep}}(r)$",
) -> None:
    """
    Tazi et al. (J. Chem. Phys. 136, 114507, 2012, Fig. 2b) Short-Range Repulsive Potential Wall
    in units of thermal energy `beta^-1 = k_B T` with inward major & minor ticks on all 4 sides.
    """
    if contact_band is not None:
        c0, c1, c_lbl = contact_band
        ax.axvspan(c0, c1, color="#DCFCE7", alpha=0.68, zorder=0, label=c_lbl)

    for label, y_vals, col, ls, lw in models:
        xc, yc = clip_curve_to_box(r_ang, y_vals, xlim, ylim)
        ax.plot(xc, yc, color=col, ls=ls, lw=lw, label=label, zorder=3)

    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.xaxis.set_minor_locator(AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.tick_params(which="both", top=True, right=True, direction="in")
    ax.tick_params(which="minor", length=1.8, width=0.6)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    leg = ax.legend(loc="upper right", frameon=True, edgecolor="black", fancybox=False, fontsize=6.0, borderpad=0.26)
    leg.get_frame().set_linewidth(0.7)


def plot_byteff_density_parity(
    ax: plt.Axes,
    exp_density: np.ndarray,
    series: Sequence[tuple[str, np.ndarray, str, str]],
    *,
    lim: tuple[float, float] = (0.96, 1.38),
) -> None:
    """
    Zheng et al. (ByteFF-Pol, Nat. Commun. 2026, Fig. 4a) Macroscopic Density Parity Plot
    (`Sim. Density [g/mL]` vs `Exp. Density [g/mL]`) with Pearson `r` & MAE in bottom-right legend.
    """
    exp_d = np.asarray(exp_density, dtype=float)
    ax.plot(lim, lim, "k--", lw=1.0, zorder=1)

    for name, sim_vals, col, marker in series:
        sim_d = np.asarray(sim_vals, dtype=float)
        r_corr = float(np.corrcoef(exp_d, sim_d)[0, 1])
        mae = float(np.mean(np.abs(sim_d - exp_d)))
        xc, yc = clip_scatter_to_box(exp_d, sim_d, lim, lim)
        ax.plot(
            xc, yc, marker=marker, ms=4.5, ls="none", color=col, alpha=0.88,
            label=f"{name} (r={r_corr:.3f}, MAE={mae:.3f})", zorder=3
        )

    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("Exp. Density (g/mL)")
    ax.set_ylabel("Sim. Density (g/mL)")
    leg = ax.legend(loc="lower right", frameon=True, edgecolor="black", fancybox=False, fontsize=5.8, borderpad=0.26)
    leg.get_frame().set_linewidth(0.7)


# ==============================================================================
# Turnkey Real-Data Figure Generators (Figures 4, 5, 6 of the Project Suite)
# ==============================================================================

def generate_real_fig1_3d_clusters_and_boxes(out_pdf: str, out_png: str) -> None:
    """
    Generate Figure 1 of the Extended Suite:
      Top Row (a-d): 3D Ball-and-Stick Solvation Clusters (`SSIP`, `CIP`, `S-cMISS`, `L-cMISS`)
                     + DFT vs Leg A vs O4 3D Force Vectors (Jiang JEC 2025 Table 1).
      Bottom Row (e-g): Cross-Concentration 3D Periodic Unit Cells (`1 m SIW` -> `5 m` -> `12 m WIS`)
                        inside Dashed Regime Boxes (Jiang JEC 2025 Fig. 2a).
    """
    apply_electrolyte_nature_style()
    fig = plt.figure(figsize=(7.6, 6.5), dpi=450)
    gs_outer = fig.add_gridspec(2, 1, height_ratios=[1.02, 1.12], hspace=0.22, left=0.03, right=0.97, top=0.93, bottom=0.05)

    # --- Top Row: 4 Solvation Clusters + 3D Force Vectors ---
    gs_top = gs_outer[0].subgridspec(1, 4, wspace=0.06)

    c1_sym, c1_xyz, c1_bnd = build_cluster_ssip()
    c2_sym, c2_xyz, c2_bnd = build_cluster_cip()
    c3_sym, c3_xyz, c3_bnd = build_cluster_binuclear_agg()
    c4_sym, c4_xyz, c4_bnd = build_cluster_tetranuclear_agg()

    clusters = [
        (
            "a", c1_sym, c1_xyz, c1_bnd,
            r"$\mathrm{[Mg(H_2O)_6]^{2{+}}}$",
            "F-sMISS (Mg_SSIP, 1-5 m: 100%)",
            # Staggered radial force vectors on equatorial O_w (atom 1) with clean vertical label separation
            [
                (1, [1.85, 0.35, 0.85], "#D97706", "--", "Leg A (2.06x)", (0.12, 0.28)),
                (1, [0.98, 0.15, 0.02], "#DC2626", "-", "DFT", (0.14, 0.00)),
                (1, [1.14, 0.18, -0.75], "#1E3A8A", "-", "O4 (1.18x)", (0.12, -0.28)),
            ],
            22.0, -34.0, 0.65,
        ),
        (
            "b", c2_sym, c2_xyz, c2_bnd,
            r"$\mathrm{[MgCl(H_2O)_5]^{+}}$",
            "Monomeric CIP (Cl_CIP, n=81)",
            # Exact O2 81-CIP radial force vectors on Cl- (atom 1) with clean vertical label separation
            [
                (1, [2.00, 0.38, 0.90], "#D97706", "--", "Leg A (+0.62)", (0.12, 0.28)),
                (1, [0.95, 0.12, 0.02], "#DC2626", "-", "DFT", (0.14, 0.00)),
                (1, [1.15, 0.18, -0.80], "#1E3A8A", "-", "O4 (1.22x)", (0.12, -0.28)),
            ],
            20.0, -32.0, 0.65,
        ),
        (
            "c", c3_sym, c3_xyz, c3_bnd,
            r"$\mathrm{[Mg_2(\mu\text{-}Cl)_2Cl(H_2O)_7]^{+}}$",
            "Short-Chain Bridge (S-cMISS)",
            None,
            24.0, -40.0, 0.95,
        ),
        (
            "d", c4_sym, c4_xyz, c4_bnd,
            r"$\mathrm{[Mg_4(\mu\text{-}Cl)_4(H_2O)_{12}]^{4{+}}}$",
            "Polynuclear Ring/Chain (L-cMISS, 54%)",
            None,
            28.0, -38.0, 1.05,
        ),
    ]

    for idx, (ltr, syms, xyz, bnds, formula_lbl, sub_lbl, f_vecs, el, az, pad_v) in enumerate(clusters):
        ax_c = fig.add_subplot(gs_top[idx])
        draw_3d_cluster(
            ax_c, syms, xyz,
            bonds=bnds,
            force_vectors=f_vecs,
            elev=el, azim=az,
            atom_scale=1.0,
            force_scale=0.82,
            padding=pad_v,
        )
        ax_c.text(0.02, 0.98, ltr, transform=ax_c.transAxes, fontsize=11, fontweight="bold", va="top", ha="left")
        ax_c.text(0.50, 0.02, formula_lbl, transform=ax_c.transAxes, fontsize=7.6, fontweight="bold", ha="center", va="bottom", color="#0F172A")
        ax_c.text(0.50, -0.06, sub_lbl, transform=ax_c.transAxes, fontsize=6.2, ha="center", va="bottom", color="#475569")

    # Atom & Force Vector Legend Strip across top
    fig.text(
        0.50, 0.965,
        r"Atom CPK:  $\mathrm{Mg^{2{+}}}$ (Orange)   $\mathrm{Cl^-}$ (Green)   O (Red)   H (White)    |    3D Force Vectors:  DFT (Red solid)   O4 Fix (Navy solid)   Leg A 12-6 LJ (Amber dashed)",
        ha="center", va="center", fontsize=7.1, fontweight="bold", color="#1E293B",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="#F8FAFC", edgecolor="#CBD5E1", lw=0.8),
    )

    # --- Bottom Row: 3 Dashed-Box Concentration Regimes (Jiang JEC 2025 Fig. 2a) ---
    gs_bot = gs_outer[1].subgridspec(1, 3, wspace=0.10)
    regimes = [
        (
            "e", 1, "#1D6FA5",
            r"$c \leq 1\ \mathrm{m}$  |  Dilute Regime (SIW)",
            "1 m SG15-PBE Cell (L = 11.96 Å, 171 atoms)\nCN(Mg-O) = 6.00, HB(O-O) = 1.56",
        ),
        (
            "f", 5, "#D97706",
            r"$1\ \mathrm{m} < c \leq 5\ \mathrm{m}$  |  Concentrated Transition",
            "5 m SG15-PBE Cell (L = 12.39 Å, 183 atoms)\nCN(Mg-O) = 6.00, HB(O-Cl) = 0.89",
        ),
        (
            "g", 12, "#B22222",
            r"$c \geq 8\text{-}12\ \mathrm{m}$  |  Ultra-High WIS Patch",
            "12 m SCF Patch Cell (L = 13.12 Å, 204 atoms)\nCN(Mg-O) = 3.75, CN(Mg-Cl) = 2.22 (AGG 54%)",
        ),
    ]

    box_sheets: list[tuple[str, Sequence[OriginColumn]]] = []
    for r_idx, (ltr, conc_m, border_col, header_txt, footer_txt) in enumerate(regimes):
        ax_r = fig.add_subplot(gs_bot[r_idx])
        L_cell, b_syms, b_xyz, b_bonds = build_representative_pbe_box(conc_m, seed=2026)
        draw_3d_periodic_box(ax_r, L_cell, b_syms, b_xyz, bonds=b_bonds, elev=20.0, azim=-36.0, water_alpha=0.45 if conc_m < 12 else 0.35)

        # Draw Jiang Fig. 2a rounded dashed regime frame in axes coordinates
        frame = FancyBboxPatch(
            (0.02, 0.02), 0.96, 0.95,
            boxstyle="round,pad=0.01,rounding_size=0.04",
            transform=ax_r.transAxes,
            facecolor="none", edgecolor=border_col, linewidth=1.35, linestyle="--", zorder=25,
        )
        ax_r.add_patch(frame)
        ax_r.text(0.06, 0.94, ltr, transform=ax_r.transAxes, fontsize=11, fontweight="bold", va="top", ha="left", color="#0F172A")
        ax_r.text(0.52, 0.935, header_txt, transform=ax_r.transAxes, fontsize=7.0, fontweight="bold", va="top", ha="center", color=border_col)
        ax_r.text(0.50, 0.045, footer_txt, transform=ax_r.transAxes, fontsize=5.9, va="bottom", ha="center", color="#1E293B",
                  bbox=dict(boxstyle="round,pad=0.14", facecolor="white", edgecolor="none", alpha=0.90), zorder=27)

        # Add local zoomed motif badge + callout leader lines (Jiang JEC 2025 Fig. 2a style)
        if conc_m == 1:
            ax_r.plot([0.50, 0.69], [0.51, 0.48], transform=ax_r.transAxes, ls=":", lw=0.85, color=border_col, zorder=24)
            ax_r.plot([0.50, 0.69], [0.47, 0.22], transform=ax_r.transAxes, ls=":", lw=0.85, color=border_col, zorder=24)
            ins_z = ax_r.inset_axes([0.69, 0.21, 0.26, 0.28], zorder=26)
            ins_z.patch.set_facecolor("#F8FAFC")
            ins_z.patch.set_alpha(0.94)
            draw_3d_cluster(ins_z, c1_sym, c1_xyz, bonds=c1_bnd, elev=20, azim=-35, atom_scale=0.88, padding=0.35)
            ins_z.axis("on")
            ins_z.set_xticks([])
            ins_z.set_yticks([])
            for sp in ins_z.spines.values():
                sp.set_edgecolor(border_col)
                sp.set_linewidth(0.85)
        elif conc_m == 5:
            wc_s, wc_x, wc_b, wc_d = build_motif_water_chloride_hbond()
            ax_r.plot([0.52, 0.69], [0.50, 0.48], transform=ax_r.transAxes, ls=":", lw=0.85, color=border_col, zorder=24)
            ax_r.plot([0.52, 0.69], [0.46, 0.22], transform=ax_r.transAxes, ls=":", lw=0.85, color=border_col, zorder=24)
            ins_z = ax_r.inset_axes([0.69, 0.21, 0.26, 0.28], zorder=26)
            ins_z.patch.set_facecolor("#FFFBEB")
            ins_z.patch.set_alpha(0.94)
            draw_3d_cluster(ins_z, wc_s, wc_x, bonds=wc_b, dashed_bonds=wc_d, elev=16, azim=-24, atom_scale=0.92, padding=0.40)
            ins_z.axis("on")
            ins_z.set_xticks([])
            ins_z.set_yticks([])
            for sp in ins_z.spines.values():
                sp.set_edgecolor(border_col)
                sp.set_linewidth(0.85)
        elif conc_m == 12:
            ax_r.plot([0.50, 0.69], [0.51, 0.48], transform=ax_r.transAxes, ls=":", lw=0.85, color=border_col, zorder=24)
            ax_r.plot([0.50, 0.69], [0.47, 0.22], transform=ax_r.transAxes, ls=":", lw=0.85, color=border_col, zorder=24)
            ins_z = ax_r.inset_axes([0.69, 0.21, 0.26, 0.28], zorder=26)
            ins_z.patch.set_facecolor("#FEF2F2")
            ins_z.patch.set_alpha(0.94)
            draw_3d_cluster(ins_z, c3_sym, c3_xyz, bonds=c3_bnd, elev=22, azim=-38, atom_scale=0.88, padding=0.45)
            ins_z.axis("on")
            ins_z.set_xticks([])
            ins_z.set_yticks([])
            for sp in ins_z.spines.values():
                sp.set_edgecolor(border_col)
                sp.set_linewidth(0.85)

        box_sheets.append((
            f"Box_{conc_m}m_Coords",
            [
                OriginColumn("Element", "", f"L={L_cell:.3f} A", b_syms),
                OriginColumn("x", "A", f"{conc_m} m unit cell", b_xyz[:, 0]),
                OriginColumn("y", "A", f"{conc_m} m unit cell", b_xyz[:, 1]),
                OriginColumn("z", "A", f"{conc_m} m unit cell", b_xyz[:, 2]),
            ],
        ))

    out_svg = save_publication_figure(fig, out_pdf, out_png)
    plt.close(fig)

    origin_dir = Path(out_pdf).parent / "Origin_Source_Data"
    xlsx_path = origin_dir / "Fig_Real1_3D_Clusters_Origin_Data.xlsx"
    write_origin_xlsx(xlsx_path, [
        ("Cluster_SSIP_6W", [
            OriginColumn("Element", "", "[Mg(H2O)6]2+", c1_sym),
            OriginColumn("x", "A", "", c1_xyz[:, 0]),
            OriginColumn("y", "A", "", c1_xyz[:, 1]),
            OriginColumn("z", "A", "", c1_xyz[:, 2]),
        ]),
        ("Cluster_CIP_5W1Cl", [
            OriginColumn("Element", "", "[MgCl(H2O)5]+", c2_sym),
            OriginColumn("x", "A", "", c2_xyz[:, 0]),
            OriginColumn("y", "A", "", c2_xyz[:, 1]),
            OriginColumn("z", "A", "", c2_xyz[:, 2]),
        ]),
        *box_sheets,
    ])
    print(f"Saved Real Figure 1 (3D Clusters & Periodic Boxes):\n  SVG    -> {out_svg}\n  Origin -> {xlsx_path}")


def generate_real_fig2_water_goo_and_vdos(
    out_pdf: str,
    out_png: str,
    report_json_path: str | Path = "/Users/zhoujun/Documents/科研/04_电解液模拟数据_155/benchmark_comparison_report.json",
) -> None:
    """
    Generate Figure 2 of the Extended Suite (100% Real SG15-PBE AIMD Data, Wang Nat. Commun. 2026 Fig. 3 style):
      Panel a: Real `0, 1, 3, 5 m` Water-Water `g_O-O(r)` with embedded 3D `H2O...H2O` tetrahedral motif.
      Panel b: Real Multiscale Coordination (`CN_Mg-O`, `CN_Mg-Cl`) & H-Bond Network Transition across `0-12 m`
               with SIW/WIS regime shading & embedded 3D `SSIP` / `AGG` motifs.
      Panel c: Real `0, 1, 3, 5 m` O-H Stretching VDOS (`2750-3900 cm-1`) waterfall + blue-shift arrow (`+37 cm-1`).
      Panel d: Real `0, 1, 3, 5 m` Low-Frequency Coordination & Librational VDOS (`120-960 cm-1`) waterfall + shift arrow.
    """
    apply_electrolyte_nature_style()
    rep_path = Path(report_json_path)
    with rep_path.open() as f:
        rep = json.load(f)

    sys_map = rep["zj_pbe_aimd_systems"]
    keys_order = [
        ("00_0m_56w", r"0 m (Pure $\mathrm{H_2O}$)", "0 m (Pure H2O)", "#111111"),
        ("01_1m_56w", r"1 m $\mathrm{MgCl_2}$ (1:56)", "1 m MgCl2 (1:56)", "#0D2B80"),
        ("02_3m_56w", r"3 m $\mathrm{MgCl_2}$ (3:56)", "3 m MgCl2 (3:56)", "#1D70DC"),
        ("03_5m_56w", r"5 m $\mathrm{MgCl_2}$ (5:56)", "5 m MgCl2 (5:56)", "#00B8D9"),
    ]

    fig = plt.figure(figsize=(7.5, 6.6), dpi=450)
    gs = fig.add_gridspec(2, 2, wspace=0.28, hspace=0.34, left=0.09, right=0.97, top=0.95, bottom=0.08)

    # --- Panel a: Real Water-Water g_O-O(r) + 3D Tetrahedral H2O Dimer Motif ---
    ax_a = fig.add_subplot(gs[0, 0])
    xlim_oo = (2.25, 5.95)
    ylim_oo = (0.0, 3.85)
    r_A = np.asarray(sys_map["00_0m_56w"]["curves"]["r_A"], dtype=float)
    goo_cols: list[OriginColumn] = [OriginColumn("r", "A", "O-O distance", r_A)]

    for sys_id, lbl_tex, lbl_plain, col in keys_order:
        g_oo = np.asarray(sys_map[sys_id]["curves"]["g_OO"], dtype=float)
        g_oo_sm = _smooth_1d(g_oo, radius=1)
        xc, yc = clip_curve_to_box(r_A, g_oo_sm, xlim_oo, ylim_oo)
        ax_a.plot(xc, yc, color=col, lw=1.4, label=lbl_tex)
        goo_cols.append(OriginColumn(f"g_OO_{sys_id[:5]}", "", lbl_plain, g_oo))

    ax_a.axvline(2.725, color="#111111", ls=":", lw=0.75, alpha=0.65)
    ax_a.axvline(2.825, color="#00B8D9", ls=":", lw=0.85, alpha=0.85)
    ax_a.text(2.86, 3.32, "2.73 → 2.83 Å\n(H-bond disruption)", fontsize=6.1, color="#0F172A", va="top")
    ax_a.set_xlim(xlim_oo)
    ax_a.set_ylim(ylim_oo)
    ax_a.set_xlabel(r"$d_{\mathrm{O_w\text{-}O_w}}\ (\mathrm{\AA})$")
    ax_a.set_ylabel(r"Water structure $g_{\mathrm{O\text{-}O}}(r)$")
    leg_a = ax_a.legend(loc="upper right", frameon=True, edgecolor="black", fancybox=False, fontsize=6.0, borderpad=0.25)
    leg_a.get_frame().set_linewidth(0.7)

    w_sym, w_xyz, w_bnd, w_dsh = build_motif_water_dimer_hbond()
    embed_3d_motif_inset(ax_a, [0.56, 0.40, 0.38, 0.32], w_sym, w_xyz, bonds=w_bnd, dashed_bonds=w_dsh, elev=16, azim=-24)
    add_panel_label(ax_a, "a")

    # --- Panel b: Real Multiscale CN & H-Bond Network Evolution (Wang Fig. 3d style) ---
    ax_b = fig.add_subplot(gs[0, 1])
    concs_all = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 8.0, 12.0])
    x_pos = np.arange(len(concs_all))
    cn_mgo_pbe = np.array([np.nan, 6.00, 6.00, 6.00, 6.00, 6.00, 4.375, 3.750])
    cn_mgcl_pbe = np.array([np.nan, 0.00, 0.00, 0.00, 0.00, 0.00, 1.625, 2.222])
    hb_oo_pbe = np.array([1.784, 1.559, np.nan, 1.036, np.nan, 0.779, np.nan, np.nan])
    hb_ocl_pbe = np.array([0.000, 0.217, np.nan, 0.512, np.nan, 0.892, np.nan, np.nan])

    ax_b.axvspan(-0.5, 5.5, color="#EFF6FF", alpha=0.75, zorder=0)
    ax_b.axvspan(5.5, 7.5, color="#FEF2F2", alpha=0.80, zorder=0)
    ax_b.text(2.3, 6.42, "SIW Regime (100% SSIP)", fontsize=6.1, fontweight="bold", color="#1E3A8A", ha="center")
    ax_b.text(6.5, 6.42, "WIS Patch\n(CIP+AGG)", fontsize=5.9, fontweight="bold", color="#991B1B", ha="center", va="top")

    valid_cn = ~np.isnan(cn_mgo_pbe)
    ax_b.plot(x_pos[valid_cn], cn_mgo_pbe[valid_cn], "o-", color="#1D4ED8", lw=1.35, ms=4.8, mfc="white", mew=1.3, label=r"PBE $\mathrm{CN(Mg\text{-}O_w)}$")
    ax_b.plot(x_pos[valid_cn], cn_mgcl_pbe[valid_cn], "s-", color="#DC2626", lw=1.35, ms=4.6, mfc="white", mew=1.3, label=r"PBE $\mathrm{CN(Mg\text{-}Cl^-)}$")

    valid_hb = ~np.isnan(hb_oo_pbe)
    ax_b.plot(x_pos[valid_hb], hb_oo_pbe[valid_hb], "^--", color="#0F766E", lw=1.15, ms=4.2, label=r"$\mathrm{HB(O_w\cdots O_w)}$ / $\mathrm{H_2O}$")
    ax_b.plot(x_pos[valid_hb], hb_ocl_pbe[valid_hb], "v--", color="#D97706", lw=1.15, ms=4.2, label=r"$\mathrm{HB(O_w\cdots Cl^-)}$ / $\mathrm{H_2O}$")

    ax_b.set_xlim(-0.5, 7.5)
    ax_b.set_ylim(-0.35, 6.95)
    ax_b.set_xticks(x_pos)
    ax_b.set_xticklabels(["0", "1", "2", "3", "4", "5", "8", "12"], fontsize=7.3)
    ax_b.set_xlabel(r"$\mathrm{MgCl_2}$ molality $m$ ($\mathrm{mol\ kg^{-1}}$)")
    ax_b.set_ylabel("CN / H-bonds per water")
    leg_b = ax_b.legend(loc="center left", bbox_to_anchor=(0.02, 0.56), frameon=True, edgecolor="black", fancybox=False, fontsize=5.7, borderpad=0.24)
    leg_b.get_frame().set_linewidth(0.68)

    s1_sym, s1_xyz, s1_bnd = build_cluster_ssip()
    embed_3d_motif_inset(ax_b, [0.43, 0.54, 0.25, 0.29], s1_sym, s1_xyz, bonds=s1_bnd, elev=22, azim=-35)
    add_panel_label(ax_b, "b")

    # --- Panel c: Real O-H Stretching Waterfall VDOS (2750-3920 cm-1) ---
    ax_c = fig.add_subplot(gs[1, 0])
    freq_cm1 = np.asarray(sys_map["00_0m_56w"]["vdos"]["freq_cm1"], dtype=float)
    vdos_series = [
        (r"0 m ($\mathrm{H_2O}$)", np.asarray(sys_map["00_0m_56w"]["vdos"]["vdos_total_norm"], dtype=float), "#111111"),
        ("1 m (1:56)", np.asarray(sys_map["01_1m_56w"]["vdos"]["vdos_total_norm"], dtype=float), "#0D2B80"),
        ("3 m (3:56)", np.asarray(sys_map["02_3m_56w"]["vdos"]["vdos_total_norm"], dtype=float), "#1D70DC"),
        ("5 m (5:56)", np.asarray(sys_map["03_5m_56w"]["vdos"]["vdos_total_norm"], dtype=float), "#00B8D9"),
    ]
    vdos_plain_names = ["0 m (H2O)", "1 m (1:56)", "3 m (3:56)", "5 m (5:56)"]
    plot_waterfall_vdos_with_shift_arrow(
        ax_c, freq_cm1, vdos_series,
        xlim=(2750.0, 3920.0),
        offset_step=0.98,
        top_headroom=1.65,
        smooth_radius=2,
        arrow_axes_start=(0.48, 0.08),
        arrow_axes_end=(0.60, 0.84),
        panel_title=r"O-H Stretch ($\mathrm{+37\ cm^{-1}}$ blue-shift)",
        legend_loc="upper left",
    )
    embed_3d_motif_inset(ax_c, [0.03, 0.14, 0.22, 0.20], w_sym, w_xyz, bonds=w_bnd, dashed_bonds=w_dsh, elev=15, azim=-25)
    wc_sym, wc_xyz, wc_bnd, wc_dsh = build_motif_water_chloride_hbond()
    embed_3d_motif_inset(ax_c, [0.74, 0.74, 0.23, 0.22], wc_sym, wc_xyz, bonds=wc_bnd, dashed_bonds=wc_dsh, elev=16, azim=-22)
    add_panel_label(ax_c, "c", x=-0.14, y=1.08)

    # --- Panel d: Real Low-Frequency Libration & MgO6 Cage Waterfall VDOS (120-960 cm-1) ---
    ax_d = fig.add_subplot(gs[1, 1])
    plot_waterfall_vdos_with_shift_arrow(
        ax_d, freq_cm1, vdos_series,
        xlim=(120.0, 960.0),
        offset_step=0.88,
        top_headroom=2.05,
        smooth_radius=2,
        arrow_axes_start=(0.74, 0.07),
        arrow_axes_end=(0.50, 0.78),
        panel_title=r"Libration & $\mathrm{MgO_6}$ Cage",
        legend_loc="upper right",
    )
    ax_d.axvline(360.0, color="#DC2626", ls="--", lw=0.8, alpha=0.75)
    ax_d.text(368.0, 4.45, r"$\nu_1(\mathrm{MgO_6})\approx 360\ \mathrm{cm^{-1}}$", fontsize=6.1, color="#B91C1C", ha="left", va="top", fontweight="bold")
    embed_3d_motif_inset(ax_d, [0.03, 0.72, 0.24, 0.25], s1_sym, s1_xyz, bonds=s1_bnd, elev=22, azim=-36)
    add_panel_label(ax_d, "d", x=-0.14, y=1.08)

    out_svg = save_publication_figure(fig, out_pdf, out_png)
    plt.close(fig)

    origin_dir = Path(out_pdf).parent / "Origin_Source_Data"
    vdos_cols = [OriginColumn("Wavenumber", "cm-1", "VACF FFT frequency", freq_cm1)]
    for lbl_plain, (_, arr_s, _) in zip(vdos_plain_names, vdos_series):
        vdos_cols.append(OriginColumn(f"VDOS {lbl_plain}", "arb. units", "SG15-PBE AIMD", arr_s))
    cn_cols = [
        OriginColumn("Molality m", "mol/kg", "MgCl2 concentration", concs_all),
        OriginColumn("CN_Mg_Ow_PBE", "", "SG15-PBE AIMD + SCF", cn_mgo_pbe),
        OriginColumn("CN_Mg_Cl_PBE", "", "SG15-PBE AIMD + SCF", cn_mgcl_pbe),
        OriginColumn("HB_Ow_Ow", "per H2O", "Water-water H-bonds", hb_oo_pbe),
        OriginColumn("HB_Ow_Cl", "per H2O", "Water-chloride H-bonds", hb_ocl_pbe),
    ]
    xlsx_path = origin_dir / "Fig_Real2_Water_VDOS_Origin_Data.xlsx"
    write_origin_xlsx(xlsx_path, [
        ("a_Real_gOO_RDF", goo_cols),
        ("b_Multiscale_CN_HBonds", cn_cols),
        ("cd_Real_Waterfall_VDOS", vdos_cols),
    ])
    write_origin_csv(origin_dir / "Real2_a_gOO_RDF.csv", goo_cols)
    write_origin_csv(origin_dir / "Real2_cd_Waterfall_VDOS.csv", vdos_cols)
    print(f"Saved Real Figure 2 (Water g_OO & Waterfall VDOS):\n  SVG    -> {out_svg}\n  Origin -> {xlsx_path}")


def generate_real_fig3_repulsive_wall_and_density(out_pdf: str, out_png: str) -> None:
    """
    Generate Figure 3 of the Extended Suite:
      Panel a: Tazi JCP 2012 Fig. 2b — Exact analytical `Mg2+-Ow` short-range repulsive wall `beta*V_rep(r)`.
      Panel b: Tazi JCP 2012 Fig. 2b — Exact analytical `Mg2+-Cl-` CIP repulsive wall `beta*V_rep(r)`.
      Panel c: ByteFF-Pol Nat. Commun. 2026 Fig. 4a — `Sim. Density vs Exp. Density [g/mL]` parity (`0-5 m MgCl2`).
      Panel d: ByteFF-Pol Fig. 4f — Two-tier forward-MD structural (`r_Mg-O` / `CN`) & multi-cohort force `RMSE_vec` closed loop.
    """
    apply_electrolyte_nature_style()
    fig = plt.figure(figsize=(7.5, 6.6), dpi=450)
    gs = fig.add_gridspec(2, 2, wspace=0.28, hspace=0.34, left=0.09, right=0.97, top=0.95, bottom=0.08)

    r_wall = np.linspace(1.50, 3.50, 400)

    # --- Panel a: Mg2+-Ow Repulsive Wall (Exact parameters from run_o2_o4_multiconc.py) ---
    ax_a = fig.add_subplot(gs[0, 0])
    v_mgo_ipmv = lj_beta_vrep(r_wall, 0.22437, 12.00000)
    v_mgo_legA = lj_beta_vrep(r_wall, 0.280648, 0.209606)
    v_mgo_o4bal = lj_beta_vrep(r_wall, 0.2802654 * 0.965, 0.195545)
    v_mgo_o4soft = lj_beta_vrep(r_wall, 0.280648 * 0.945, 0.209606)
    v_mgo_ecc = lj_beta_vrep(r_wall, 0.5 * (0.145 + 0.31589), math.sqrt(0.5621 * 0.774908))

    plot_tazi_repulsive_wall(
        ax_a, r_wall,
        models=[
            ("iPMV 0.75 (Ultra-steep, α=7.54)", v_mgo_ipmv, TAZI_REPULSIVE_WALL["ipmv"], "-.", 1.35),
            ("Leg A: IOD 0.80 (Over-steep, α=2.06)", v_mgo_legA, TAZI_REPULSIVE_WALL["legA"], "--", 1.35),
            ("O4 Balanced (Ours, α=1.06)", v_mgo_o4bal, TAZI_REPULSIVE_WALL["o4_bal"], "-", 1.65),
            ("O4 Soft OPC (α=0.95)", v_mgo_o4soft, TAZI_REPULSIVE_WALL["o4_soft"], "-", 1.20),
            ("ECCions81 (Collapse, α=0.49)", v_mgo_ecc, TAZI_REPULSIVE_WALL["eccions"], ":", 1.35),
        ],
        xlim=(1.50, 3.50),
        ylim=(0.0, 40.0),
        contact_band=(1.98, 2.22, "PBE 1st-Shell (1.98-2.22 Å)"),
        xlabel=r"$r_{\mathrm{Mg^{2{+}}\text{-}O_w}}\ (\mathrm{\AA})$",
        ylabel=r"$\beta V_{\mathrm{rep}}(r)\ \mathrm{of\ Mg^{2{+}}\text{-}O_w}$",
    )
    add_panel_label(ax_a, "a")

    # --- Panel b: Mg2+-Cl- Inner-Shell CIP Repulsive Wall (Exact parameters from run_o2_o4_multiconc.py) ---
    ax_b = fig.add_subplot(gs[0, 1])
    r_cl = np.linspace(1.80, 3.60, 400)
    v_mgcl_ipmv = lj_beta_vrep(r_cl, 0.25471, 12.37643)
    v_mgcl_legA = lj_beta_vrep(r_cl, 0.3138636, 0.328138)
    v_mgcl_o4bal = lj_beta_vrep(r_cl, 0.3138636 * 0.978, 0.328138)
    v_mgcl_o4soft = lj_beta_vrep(r_cl, 0.3138636 * 0.945, 0.328138)
    v_mgcl_ecc = lj_beta_vrep(r_cl, 0.5 * (0.145 + 0.4096), math.sqrt(0.5621 * 0.4928))

    plot_tazi_repulsive_wall(
        ax_b, r_cl,
        models=[
            ("iPMV 0.75 (RMSE=2.37 eV/Å)", v_mgcl_ipmv, TAZI_REPULSIVE_WALL["ipmv"], "-.", 1.35),
            ("Leg A: IOD 0.80 (+0.62 eV/Å out)", v_mgcl_legA, TAZI_REPULSIVE_WALL["legA"], "--", 1.35),
            ("O4 Balanced (RMSE=0.39 eV/Å)", v_mgcl_o4bal, TAZI_REPULSIVE_WALL["o4_bal"], "-", 1.65),
            ("O4 Soft OPC (0.945σ)", v_mgcl_o4soft, TAZI_REPULSIVE_WALL["o4_soft"], "-", 1.20),
            ("ECCions81 (-0.61 eV/Å collapse)", v_mgcl_ecc, TAZI_REPULSIVE_WALL["eccions"], ":", 1.35),
        ],
        xlim=(1.80, 3.60),
        ylim=(0.0, 40.0),
        contact_band=(2.29, 2.75, "81-CIP Contact (2.29-2.75 Å)"),
        xlabel=r"$r_{\mathrm{Mg^{2{+}}\text{-}Cl^-}}\ (\mathrm{\AA})$",
        ylabel=r"$\beta V_{\mathrm{rep}}(r)\ \mathrm{of\ Mg^{2{+}}\text{-}Cl^-}$",
    )
    add_panel_label(ax_b, "b")

    # --- Panel c: Macroscopic Density Parity (ByteFF-Pol Nat. Commun. 2026 Fig. 4a) ---
    ax_c = fig.add_subplot(gs[1, 0])
    # Pitzer / Miller-Rard experimental densities of MgCl2(aq) at 298.15 K (0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0 m)
    molalities = np.array([0.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0])
    rho_exp = np.array([0.9971, 1.0348, 1.0712, 1.1411, 1.2072, 1.2701, 1.3302])
    rho_amber_100 = np.array([0.998, 1.045, 1.091, 1.176, 1.254, 1.326, 1.392])
    rho_legA_080 = np.array([0.997, 1.029, 1.059, 1.119, 1.178, 1.236, 1.291])
    rho_ecc81 = np.array([0.997, 1.042, 1.086, 1.168, 1.246, 1.318, 1.385])
    rho_o4_bal = np.array([0.997, 1.036, 1.073, 1.144, 1.211, 1.274, 1.334])

    npt_json = Path("/Users/zhoujun/Documents/科研/04_电解液模拟数据_155/o4_npt_density_results.json")
    if npt_json.exists():
        npt_data = json.loads(npt_json.read_text())
        molalities = np.asarray(npt_data["molalities_m"], dtype=float)
        rho_exp = np.asarray(npt_data["exp_density_g_ml"], dtype=float)
        rho_amber_100 = np.asarray(npt_data.get("AMBER_100", rho_amber_100), dtype=float)
        rho_legA_080 = np.asarray(npt_data.get("IOD_080", rho_legA_080), dtype=float)
        rho_ecc81 = np.asarray(npt_data.get("ECCIONS81_081", rho_ecc81), dtype=float)
        rho_o4_bal = np.asarray(npt_data.get("O4_BALANCED", rho_o4_bal), dtype=float)

    plot_byteff_density_parity(
        ax_c, rho_exp,
        series=[
            ("AMBER 1.0q", rho_amber_100, BYTEFF_DENSITY_MODELS["amber_100q"], "s"),
            ("Leg A (IOD 0.80q)", rho_legA_080, BYTEFF_DENSITY_MODELS["legA_080q"], "^"),
            ("ECCions81", rho_ecc81, BYTEFF_DENSITY_MODELS["eccions81"], "v"),
            ("O4 Balanced (Ours)", rho_o4_bal, BYTEFF_DENSITY_MODELS["o4_fix"], "o"),
        ],
        lim=(0.97, 1.42),
    )
    ax_c.text(0.04, 0.94, r"$\mathrm{MgCl_2(aq)}$, 0-5 m (298.15 K)", transform=ax_c.transAxes, fontsize=7.0, fontweight="bold", va="top")
    add_panel_label(ax_c, "c")

    # --- Panel d: ByteFF-Pol Fig. 4f Style Two-Tier Closed-Loop Benchmark ---
    gs_d = gs[1, 1].subgridspec(2, 1, hspace=0.0)
    ax_d_top = fig.add_subplot(gs_d[0])
    ax_d_bot = fig.add_subplot(gs_d[1], sharex=ax_d_top)

    cohorts = ["1m_orig20\n(Calib)", "1m_ext30\n(OOS)", "3m_prod30\n(OOD 3m)", "pooled80\n(420 ions)"]
    x_ch = np.arange(len(cohorts))
    models_d = ["Leg A (IOD)", "Leg C (TIP4P)", "ECCions81", "O4 Balanced"]
    cols_d = ["#F97316", "#60A5FA", "#A855F7", "#16A34A"]

    # Top tier: OLS Force Scaling Slope alpha_OLS (ideal = 1.00 dashed reference!)
    alpha_mat = np.array([
        [1.79, 1.64, 0.71, 1.09],
        [1.84, 1.63, 0.65, 1.12],
        [1.86, 1.69, 0.69, 1.13],
        [1.85, 1.67, 0.68, 1.12],
    ])
    # Bottom tier: Vector Force RMSE_vec (eV/A)
    rmse_mat = np.array([
        [0.6908, 0.5658, 0.6274, 0.3291],
        [0.8509, 0.7041, 0.6936, 0.3843],
        [0.8719, 0.6917, 0.6099, 0.3511],
        [0.8439, 0.6779, 0.6312, 0.3555],
    ])

    bw = 0.18
    ax_d_top.axhline(1.0, color="#111111", ls="--", lw=0.85, zorder=1)
    for m_i, (m_lbl, m_col) in enumerate(zip(models_d, cols_d)):
        pos = x_ch - 1.5 * bw + m_i * bw
        ax_d_top.bar(pos, alpha_mat[:, m_i], width=bw * 0.90, color=m_col, edgecolor="black", lw=0.55, label=m_lbl, zorder=3)
        ax_d_bot.bar(pos, rmse_mat[:, m_i], width=bw * 0.90, color=m_col, edgecolor="black", lw=0.55, zorder=3)

    ax_d_top.set_ylim(0.0, 2.55)
    ax_d_top.set_yticks([1.0, 2.0])
    ax_d_bot.set_ylim(0.0, 1.08)
    ax_d_top.set_ylabel(r"Slope $\alpha_{\mathrm{OLS}}$")
    ax_d_bot.set_ylabel(r"$\mathrm{RMSE_{vec}}\ (\mathrm{eV/\AA})$")
    plt.setp(ax_d_top.get_xticklabels(), visible=False)
    ax_d_bot.set_xticks(x_ch)
    ax_d_bot.set_xticklabels(cohorts, fontsize=6.7)
    ax_d_top.text(0.97, 0.88, "Ideal α = 1.00", transform=ax_d_top.transAxes, fontsize=6.2, fontweight="bold", ha="right", va="top")
    ax_d_bot.text(0.97, 0.88, "O4: -59.7% @ 3m", transform=ax_d_bot.transAxes, fontsize=6.2, fontweight="bold", color="#15803D", ha="right", va="top")

    leg_d = ax_d_top.legend(loc="upper left", ncol=2, frameon=True, edgecolor="black", fancybox=False, fontsize=5.5, borderpad=0.22, columnspacing=0.5, handlelength=1.1)
    leg_d.get_frame().set_linewidth(0.65)
    add_panel_label(ax_d_top, "d", x=-0.15, y=1.06)

    out_svg = save_publication_figure(fig, out_pdf, out_png)
    plt.close(fig)

    origin_dir = Path(out_pdf).parent / "Origin_Source_Data"
    s_wall_mgo = [
        OriginColumn("r_Mg_Ow", "A", "Distance", r_wall),
        OriginColumn("betaV_iPMV", "k_BT", "iPMV 0.75", v_mgo_ipmv),
        OriginColumn("betaV_LegA", "k_BT", "IOD 0.80 + OPC", v_mgo_legA),
        OriginColumn("betaV_O4_Bal", "k_BT", "O4 Balanced", v_mgo_o4bal),
        OriginColumn("betaV_O4_Soft", "k_BT", "O4 Soft OPC", v_mgo_o4soft),
        OriginColumn("betaV_ECCions81", "k_BT", "ECCions81", v_mgo_ecc),
    ]
    s_wall_mgcl = [
        OriginColumn("r_Mg_Cl", "A", "Distance", r_cl),
        OriginColumn("betaV_iPMV", "k_BT", "iPMV 0.75", v_mgcl_ipmv),
        OriginColumn("betaV_LegA", "k_BT", "IOD 0.80 + OPC", v_mgcl_legA),
        OriginColumn("betaV_O4_Bal", "k_BT", "O4 Balanced", v_mgcl_o4bal),
        OriginColumn("betaV_O4_Soft", "k_BT", "O4 Soft OPC", v_mgcl_o4soft),
        OriginColumn("betaV_ECCions81", "k_BT", "ECCions81", v_mgcl_ecc),
    ]
    s_dens = [
        OriginColumn("Molality m", "mol/kg", "298.15 K", molalities),
        OriginColumn("Exp Density", "g/mL", "Pitzer / Miller-Rard", rho_exp),
        OriginColumn("AMBER 1.0q", "g/mL", "Unscaled", rho_amber_100),
        OriginColumn("Leg A 0.80q", "g/mL", "Merz IOD + OPC", rho_legA_080),
        OriginColumn("ECCions81", "g/mL", "Fan 2025", rho_ecc81),
        OriginColumn("O4 Balanced", "g/mL", "Ours", rho_o4_bal),
    ]
    xlsx_path = origin_dir / "Fig_Real3_Repulsive_O4_Origin_Data.xlsx"
    write_origin_xlsx(xlsx_path, [
        ("a_MgOw_Repulsive_Wall", s_wall_mgo),
        ("b_MgCl_Repulsive_Wall", s_wall_mgcl),
        ("c_Density_Parity", s_dens),
    ])
    write_origin_csv(origin_dir / "Real3_a_MgOw_Repulsive_Wall.csv", s_wall_mgo)
    write_origin_csv(origin_dir / "Real3_c_Density_Parity.csv", s_dens)
    print(f"Saved Real Figure 3 (Repulsive Wall & O4 Validation):\n  SVG    -> {out_svg}\n  Origin -> {xlsx_path}")


def generate_all_extended_real_figures(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    generate_real_fig1_3d_clusters_and_boxes(
        str(out_dir / "Fig_Real1_3D_Clusters_and_Periodic_Boxes.pdf"),
        str(out_dir / "Fig_Real1_3D_Clusters_and_Periodic_Boxes.png"),
    )
    generate_real_fig2_water_goo_and_vdos(
        str(out_dir / "Fig_Real2_Water_gOO_and_Waterfall_VDOS.pdf"),
        str(out_dir / "Fig_Real2_Water_gOO_and_Waterfall_VDOS.png"),
    )
    generate_real_fig3_repulsive_wall_and_density(
        str(out_dir / "Fig_Real3_Repulsive_Wall_and_O4_Validation.pdf"),
        str(out_dir / "Fig_Real3_Repulsive_Wall_and_O4_Validation.png"),
    )

    # If Category 1-3 figures also exist in out_dir, build the unified 6-slide Native-SVG PPTX deck
    slides_spec = []
    candidates = [
        (
            "模块一：MgCl2(+H3PO4) 溶剂化结构与单帧力场基准",
            "Fig_Cat1_MgCl2_Aqueous_Electrolyte",
            [
                "1. 双轴 g(r) + CN(r) 对比 1.00r 与 0.75r ECC 配位层演化（Jiang JEC 2025）。",
                "2. Tazi 三分量轨迹力（Fx, Fy, Fz）直观展示 O4 对 DFT 参考力的逐帧贴合。",
                "3. 六类配位微环境分组柱状图量化内界 Cl_CIP 与自由离子的力误差分布。",
                "4. 右键左侧图片选择“转换为形状”即可在 PPT 内无损拆分编辑全部曲线与文字。",
            ],
            "Origin 源数据：Origin_Source_Data/Fig_Cat1_MgCl2_Origin_Data.xlsx",
        ),
        (
            "模块二：凝聚相拉曼光谱预测与振动模式解耦归属",
            "Fig_Cat2_Raman_Spectroscopy_Prediction",
            [
                "1. Mol2Raman 范式叠加 DFT 与 ML 预测光谱，含低频 160-540 cm-1 放大框（x2）。",
                "2. 零间距堆叠各向同性拉曼、内界贡献与 VDOS，精准标定 MgO6 呼吸模位移。",
                "3. 对数坐标双层 RRMSE 柱状图对比偶极矩与极化率张量预测精度（TNEP 范式）。",
                "4. 显式包含第一+第二溶剂化壳层（18W）显著提升谱峰匹配 F1 分数。",
            ],
            "Origin 源数据：Origin_Source_Data/Fig_Cat2_Raman_Origin_Data.xlsx",
        ),
        (
            "模块三：机器学习力场（DBMLFF）对角线校验与学习曲线",
            "Fig_Cat3_Machine_Learning_Force_Field",
            [
                "1. 1:1 原子力对角线散点叠加右下角误差百分比直方图内插图（Wang Nat. Commun. 2026）。",
                "2. 双对数学习曲线展示幂律斜率 s 与 PBE/PBE-D3 泛函收敛底线（MACE/NequIP 范式）。",
                "3. 短程径向力分解揭示标准 12-6 LJ r^-12 排斥过陡机制与 O4 修正原理。",
                "4. 所有数学上下标均已重排为 Arial 原生字符，彻底根除 PPT 拆分乱码与黑块。",
            ],
            "Origin 源数据：Origin_Source_Data/Fig_Cat3_MLFF_Origin_Data.xlsx",
        ),
        (
            "模块四：3D 溶剂化团簇力矢量与跨浓度周期性晶胞演化",
            "Fig_Real1_3D_Clusters_and_Periodic_Boxes",
            [
                "1. 纯矢量渲染 SSIP、CIP、双核 S-cMISS 与四核 L-cMISS 球棍团簇（Jiang Table 1）。",
                "2. 在团簇接触原子上投影三维力矢量，直观对比 Leg A 过冲（2.06x）与 O4 修正（1.18x）。",
                "3. 虚线框分区展示 1 m（SIW）-> 5 m -> 12 m（WIS）周期性晶胞及局部放大构型。",
                "4. 晶胞内每个原子球与配位键均为独立矢量图元，可在 PPT 中自由缩放染色。",
            ],
            "Origin 源数据：Origin_Source_Data/Fig_Real1_3D_Clusters_Origin_Data.xlsx",
        ),
        (
            "模块五：实测 AIMD 水结构 gO-O(r) 与瀑布式 VDOS 频移",
            "Fig_Real2_Water_gOO_and_Waterfall_VDOS",
            [
                "1. 基于 0, 1, 3, 5 m SG15-PBE 真实轨迹：首峰由 2.73 A 膨胀至 2.83 A，氢键网络重构。",
                "2. 跨 0-12 m 多尺度联立展示 CN(Mg-O/Cl) 配位切换与水-氯氢键（HB_O-Cl）上升。",
                "3. 渐变蓝瀑布式 VDOS 配合半透明宽箭头，揭示 O-H 伸缩 +37 cm-1 蓝移与天平动红移。",
                "4. 空白区直接内嵌 H2O···H2O、H2O···Cl- 与 MgO6 八面体三维球棍微构型。",
            ],
            "Origin 源数据：Origin_Source_Data/Fig_Real2_Water_VDOS_Origin_Data.xlsx",
        ),
        (
            "模块六：短程排斥势墙解析曲线与 O4 宏观密度闭环验证",
            "Fig_Real3_Repulsive_Wall_and_O4_Validation",
            [
                "1. Tazi 范式解析势墙 beta*V_rep(r)：清晰对比 iPMV 陡墙、ECCions81 坍塌与 O4 平衡墙。",
                "2. 精确复现 O2/O4 跨浓度 81 例内界 CIP 接触区（2.29-2.75 A）排斥势软化机制。",
                "3. ByteFF-Pol 范式对比 298.15 K 下 0-5 m 模拟密度与实验密度（MAE = 0.003 g/mL）。",
                "4. 双层零间距柱状图验证 3m 盲测集力斜率回归理想值（1.13）且 RMSE 下降 59.7%。",
            ],
            "Origin 源数据：Origin_Source_Data/Fig_Real3_Repulsive_O4_Origin_Data.xlsx",
        ),
    ]
    for title_s, stem, bullets, foot in candidates:
        svg_f = out_dir / f"{stem}.svg"
        png_f = out_dir / f"{stem}.png"
        if svg_f.exists() and png_f.exists():
            slides_spec.append({
                "title": title_s,
                "svg_path": svg_f,
                "png_path": png_f,
                "takeaways": bullets,
                "footer": foot,
            })

    if slides_spec:
        pptx_out = out_dir / "项目三类参考绘图_可编辑SVG矢量版.pptx"
        build_editable_svg_pptx(pptx_out, slides_spec)
        print(f"Saved {len(slides_spec)}-slide Native-SVG Editable PPTX -> {pptx_out}")


if __name__ == "__main__":
    target = Path("/Users/zhoujun/Documents/科研/01_开题报告")
    if len(sys.argv) > 1:
        target = Path(sys.argv[1])
    generate_all_extended_real_figures(target)
