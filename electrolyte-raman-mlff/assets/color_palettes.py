"""Curated sRGB palettes for scientific figures.

Sources were checked 2026-10-01. Palette selection alone never establishes
accessibility: audit the rendered foreground/background contrast and add
redundant encodings.

Paul Tol values and recommended fixed order:
https://sronpersonalpages.nl/~pault/data/colourschemes.pdf
(SRON/EPS/TN/09-002, issue 3.2, 18 August 2021)
"""

from __future__ import annotations

from typing import Final

# Monochromatic + Single-Accent Academic Slate Palette (Preferred for clean academic papers & slides)
# Baselines use neutral cool-gray/slate steps; ONLY the proposed/key series uses deep navy (#1E3A5F).
ACADEMIC_MONO_SLATE: Final = [
    "#1E3A5F",  # Primary / Proposed method (Deep Academic Navy)
    "#475569",  # Baseline 1 (Dark Slate Gray)
    "#94A3B8",  # Baseline 2 (Medium Cool Gray)
    "#CBD5E1",  # Baseline 3 / Reference (Light Cool Gray)
    "#0F172A",  # Ground Truth / DFT Reference (Near-Black)
]

# Okabe-Ito colors as reproduced in Wong, Nature Methods 8, 441 (2011).
OKABE_ITO: Final = {
    "orange": "#E69F00",
    "sky_blue": "#56B4E9",
    "bluish_green": "#009E73",
    "yellow": "#F0E442",
    "blue": "#0072B2",
    "vermillion": "#D55E00",
    "reddish_purple": "#CC79A7",
    "black": "#000000",
}
OKABE_ITO_LIST: Final = [
    "#E69F00",
    "#56B4E9",
    "#009E73",
    "#F0E442",
    "#0072B2",
    "#D55E00",
    "#CC79A7",
    "#000000",
]

# These five meet 3:1 against white in sRGB. Still use markers/line styles.
OKABE_ITO_ON_WHITE: Final = [
    "#0072B2",
    "#D55E00",
    "#009E73",
    "#CC79A7",
    "#000000",
]

# Compatibility alias: Wong presents the same eight colors in another order.
WONG: Final = [
    "#000000",
    "#E69F00",
    "#56B4E9",
    "#009E73",
    "#F0E442",
    "#0072B2",
    "#D55E00",
    "#CC79A7",
]

# Paul Tol qualitative schemes in the fixed sequence recommended in issue 3.2.
TOL_BRIGHT: Final = [
    "#4477AA",
    "#EE6677",
    "#228833",
    "#CCBB44",
    "#66CCEE",
    "#AA3377",
    "#BBBBBB",
]
TOL_HIGH_CONTRAST: Final = ["#004488", "#DDAA33", "#BB5566"]
TOL_VIBRANT: Final = [
    "#EE7733",
    "#0077BB",
    "#33BBEE",
    "#EE3377",
    "#CC3311",
    "#009988",
    "#BBBBBB",
]
TOL_MUTED: Final = [
    "#CC6677",
    "#332288",
    "#DDCC77",
    "#117733",
    "#88CCEE",
    "#882255",
    "#44AA99",
    "#999933",
    "#AA4499",
]
TOL_MEDIUM_CONTRAST: Final = [
    "#6699CC",
    "#004488",
    "#EECC66",
    "#994455",
    "#997700",
    "#EE99AA",
]
TOL_PALE: Final = [
    "#BBCCEE",
    "#CCEEFF",
    "#CCDDAA",
    "#EEEEBB",
    "#FFCCCC",
    "#DDDDDD",
]
TOL_DARK: Final = [
    "#222255",
    "#225555",
    "#225522",
    "#666633",
    "#663333",
    "#555555",
]
TOL_LIGHT: Final = [
    "#77AADD",
    "#EE8866",
    "#EEDD88",
    "#FFAABB",
    "#99DDFF",
    "#44BB99",
    "#BBCC33",
    "#AAAA00",
    "#DDDDDD",
]

# Reference Benchmarks for Aqueous Mg2+ / MgCl2 Electrolyte & Raman Spectroscopy Project:
# 1. Pan & Galli, Nature Communications 11, 421 (2020) — FPMD Raman & VDOS attribution
PAN_GALLI_RAMAN: Final = [
    "#000000",  # Unpolarized Raman / Total (Black)
    "#E62222",  # Isotropic Raman (Crimson Red)
    "#3355BB",  # VDOS / Vibrational Density of States (Cobalt Blue)
    "#BC8F8F",  # Intramolecular / Sub-species component (Rosy Taupe)
]

# 2. Wang et al., Nature Communications 17, 1226 (2026) — MLFF Parity (Energy / Force / Virial)
WANG_MLFF_PARITY: Final = [
    "#E67E45",  # Energy E_MLP vs E_DFT (Coral Orange)
    "#5E9CE6",  # Force F_MLP vs F_DFT (Sky Blue)
    "#4DAF4A",  # Virial V_MLP vs V_DFT (Emerald Green)
    "#191970",  # O4 / Corrected Force / Specific Solvate (Midnight Navy)
]

# 3. Wang et al., Nature Communications 17, 1226 (2026) Fig. 3e-f — Concentration Waterfall Blues
WANG_WATERFALL_BLUES: Final = [
    "#000000",  # Dilute limit (e.g., 0.1 M / 1:100)
    "#082A63",  # Low concentration (0.5 M / 1:40)
    "#0D47A1",  # Moderate concentration (1.0 M / 1:20)
    "#1976D2",  # Intermediate concentration (2.0 M / 1:10)
    "#42A5F5",  # High concentration (3.0 M / 1:5)
    "#78B7E8",  # Concentrated (4.0 M / 1:3)
    "#00D5FF",  # Water-in-salt / Eutectic limit (14 M / 1:2)
]

# 4. Balos et al., Nature Chemistry (2022) Fig. 6 — Solvation Shell H-Bond / Force Error Bars
BALOS_HBOND_SHELLS: Final = [
    "#FBC99D",  # 1st Shell / Cation-coordinated (Warm Peach, use with black 0.8pt outline)
    "#9FD9A4",  # Anion-coordinated / CIP (Soft Mint Green, use with black 0.8pt outline)
    "#C4B5D9",  # Shared Cation-Anion Bridge / AGG (Lavender, use with black 0.8pt outline)
    "#FFF9A6",  # Bulk-type water / SSIP outer shell (Soft Yellow, use with black 0.8pt outline)
]

# 5. Jiang et al., J. Energy Chem. 109, 466–478 (2025) Table 1 & Fig. 2a — 3D CPK Glossy Atom Shading
JIANG_CPK_3D: Final = {
    "Mg": {"core": "#E67E22", "mid": "#F39C12", "spec": "#FEF5E7", "rim": "#7E3F08", "radius": 0.44},
    "Cl": {"core": "#27AE60", "mid": "#58D68D", "spec": "#EAFAF1", "rim": "#145A32", "radius": 0.48},
    "O":  {"core": "#DC2626", "mid": "#F87171", "spec": "#FEE2E2", "rim": "#7F1D1D", "radius": 0.34},
    "H":  {"core": "#F1F5F9", "mid": "#FFFFFF", "spec": "#FFFFFF", "rim": "#475569", "radius": 0.21},
    "P":  {"core": "#8E44AD", "mid": "#BB8FCE", "spec": "#F5EEF8", "rim": "#4A235A", "radius": 0.42},
}

# 6. Tazi et al., J. Chem. Phys. 136, 114507 (2012) Fig. 2b — Short-Range Repulsive Potential Wall
TAZI_REPULSIVE_WALL: Final = {
    "ipmv":     "#DC2626",  # Ultra-steep iPMV 0.75 wall (Crimson Red)
    "legA":     "#D97706",  # Baseline Merz IOD 0.80 + OPC wall (Amber Orange)
    "o4_bal":   "#1E3A8A",  # Proposed O4 Balanced softened wall (Deep Academic Navy)
    "o4_soft":  "#0284C7",  # O4 Soft OPC variant (Cerulean Blue)
    "eccions":  "#7C3AED",  # ECCions81 inner-shell collapse (Royal Violet)
}

# 7. Zheng et al. (ByteFF-Pol), Nat. Commun. (2026) Fig. 4a,f — Density & Transport Parity
BYTEFF_DENSITY_MODELS: Final = {
    "amber_100q": "#3B82F6",  # Unscaled 1.0q Classical Force Field (Steel Blue)
    "legA_080q":  "#F97316",  # Merz IOD 0.80q Baseline (Warm Orange)
    "eccions81":  "#DC2626",  # ECCions81 Over-contracted (Brick Red)
    "o4_fix":     "#16A34A",  # Proposed O4 Balanced / DBMLFF (Emerald Green)
}

PALETTES: Final = {
    "academic_mono_slate": ACADEMIC_MONO_SLATE,
    "pan_galli_raman": PAN_GALLI_RAMAN,
    "wang_mlff_parity": WANG_MLFF_PARITY,
    "wang_waterfall_blues": WANG_WATERFALL_BLUES,
    "balos_hbond_shells": BALOS_HBOND_SHELLS,
    "okabe_ito": OKABE_ITO_LIST,
    "okabe_ito_on_white": OKABE_ITO_ON_WHITE,
    "wong": WONG,
    "tol_bright": TOL_BRIGHT,
    "tol_high_contrast": TOL_HIGH_CONTRAST,
    "tol_vibrant": TOL_VIBRANT,
    "tol_muted": TOL_MUTED,
    "tol_medium_contrast": TOL_MEDIUM_CONTRAST,
    "tol_pale": TOL_PALE,
    "tol_dark": TOL_DARK,
    "tol_light": TOL_LIGHT,
}

PALETTE_METADATA: Final = {
    "okabe_ito": {
        "kind": "qualitative",
        "source": "https://www.nature.com/articles/nmeth.1618",
        "caveat": "Yellow and other light colors need outlines on white.",
    },
    "okabe_ito_on_white": {
        "kind": "qualitative-subset",
        "source": "derived from Okabe-Ito by WCAG sRGB contrast calculation",
        "caveat": "At most five categories; use redundant encodings.",
    },
    "tol_bright": {
        "kind": "qualitative",
        "source": "https://sronpersonalpages.nl/~pault/data/colourschemes.pdf",
        "maximum_categories": 7,
    },
    "tol_high_contrast": {
        "kind": "qualitative",
        "source": "https://sronpersonalpages.nl/~pault/data/colourschemes.pdf",
        "maximum_categories": 3,
        "caveat": "Designed to retain separation in grayscale.",
    },
    "tol_vibrant": {
        "kind": "qualitative",
        "source": "https://sronpersonalpages.nl/~pault/data/colourschemes.pdf",
        "maximum_categories": 7,
    },
    "tol_muted": {
        "kind": "qualitative",
        "source": "https://sronpersonalpages.nl/~pault/data/colourschemes.pdf",
        "maximum_categories": 9,
    },
    "tol_medium_contrast": {
        "kind": "qualitative-pairs",
        "source": "https://sronpersonalpages.nl/~pault/data/colourschemes.pdf",
        "maximum_categories": 6,
    },
    "tol_pale": {
        "kind": "text-background",
        "source": "https://sronpersonalpages.nl/~pault/data/colourschemes.pdf",
        "caveat": "Not intended for plot lines or categorical maps.",
    },
    "tol_dark": {
        "kind": "text-foreground",
        "source": "https://sronpersonalpages.nl/~pault/data/colourschemes.pdf",
        "caveat": "Not intended as a multi-category plot palette.",
    },
    "tol_light": {
        "kind": "labeled-cell-fill",
        "source": "https://sronpersonalpages.nl/~pault/data/colourschemes.pdf",
        "maximum_categories": 9,
    },
}

SEQUENTIAL_COLORMAPS: Final = [
    "viridis",
    "plasma",
    "inferno",
    "magma",
    "cividis",
]

# Candidates, not blanket accessibility certifications. Center and normalization
# must match the scientific meaning, and rendered contrast still needs review.
DIVERGING_COLORMAP_CANDIDATES: Final = ["RdBu_r", "PuOr", "BrBG"]
DIVERGING_COLORMAPS_SAFE = DIVERGING_COLORMAP_CANDIDATES  # Compatibility alias.
DIVERGING_COLORMAPS_AVOID: Final = ["RdYlGn"]

FLUOROPHORES_TRADITIONAL: Final = {
    "DAPI": "#0000FF",
    "GFP": "#00FF00",
    "RFP": "#FF0000",
    "Cy5": "#FF00FF",
    "YFP": "#FFFF00",
}
FLUOROPHORES_ACCESSIBLE: Final = {
    "Channel1": "#0072B2",
    "Channel2": "#E69F00",
    "Channel3": "#D55E00",
    "Channel4": "#CC79A7",
    "Channel5": "#F0E442",
}
DNA_BASES: Final = {
    "A": "#00CC00",
    "C": "#0000CC",
    "G": "#FFB300",
    "T": "#CC0000",
}
DNA_BASES_ACCESSIBLE: Final = {
    "A": "#009E73",
    "C": "#0072B2",
    "G": "#E69F00",
    "T": "#D55E00",
}


def get_palette(palette_name: str = "okabe_ito_on_white") -> list[str]:
    """Return a copy of a named palette."""
    try:
        return list(PALETTES[palette_name])
    except KeyError as exc:
        available = ", ".join(sorted(PALETTES))
        raise ValueError(
            f"palette {palette_name!r} not found; available: {available}"
        ) from exc


def apply_palette(palette_name: str = "okabe_ito_on_white") -> list[str]:
    """Apply a named palette to Matplotlib, importing it only when requested."""
    try:
        import matplotlib as mpl
    except ImportError as exc:
        raise RuntimeError(
            "Matplotlib is required to apply a palette; "
            "install the pinned snapshot documented in SKILL.md"
        ) from exc
    colors = get_palette(palette_name)
    mpl.rcParams["axes.prop_cycle"] = mpl.cycler(color=colors)
    return colors


if __name__ == "__main__":
    for palette_name in sorted(PALETTES):
        print(f"{palette_name}: {', '.join(PALETTES[palette_name])}")
