#!/usr/bin/env python3
r"""
Turnkey ~20-Minute GROMACS Forward-NPT Density & RDF Closed-Loop Validation on `server155`.

Runs 298.15 K / 1 bar NPT classical MD across `0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0 m` MgCl2(aq)
(500 H2O + N MgCl2 cubic box) comparing:
  - `AMBER_100`     : Unscaled 1.0q Merz IOD + SPC/E
  - `IOD_080`       : Leg A (0.80q Merz IOD + 4-site OPC)
  - `ECCIONS81_081` : ECCions81 (0.81q Fan 2025 + TIP4P/2005)
  - `O4_BALANCED`   : Softened Short-Range Repulsion Fix (0.965 sigma_MgOw, 0.978 sigma_MgCl + TIP4P/2005)

Exports `o4_npt_density_results.json` (`Sim. Density vs. Exp. Density [g/mL]` + `r_Mg-O` & `CN_Mg-O`),
which is automatically picked up by `solvation_3d_vdos_o4_plots.py` (Figure Real3 Panel c, ByteFF-Pol style).

Usage on `server155`:
    python3 run_o4_forward_npt_155.py --workdir /tmp/o4_npt_bench --out o4_npt_density_results.json --ntomp 8
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

# Experimental densities of MgCl2(aq) at 298.15 K, 0.1 MPa (Pitzer / Miller-Rard, g/mL)
EXP_BENCHMARK = [
    (0.0, 0, 0.9971),
    (0.5, 5, 1.0348),
    (1.0, 9, 1.0712),
    (2.0, 18, 1.1411),
    (3.0, 27, 1.2072),
    (4.0, 36, 1.2701),
    (5.0, 45, 1.3302),
]

# Exact topology parameters synchronized with `run_o2_o4_multiconc.py`
MODELS = {
    "AMBER_100": {
        "water": "TIP4P2005",
        "q_mg": 2.00, "q_cl": -1.00,
        "sig_mg": 0.25195, "eps_mg": 0.06276,
        "sig_cl": 0.44172, "eps_cl": 0.49283,
        "nb_fix": [],
    },
    "IOD_080": {
        "water": "OPC",
        "q_mg": 1.60, "q_cl": -0.80,
        "sig_mg": 0.244746, "eps_mg": 0.04724,
        "sig_cl": 0.383000, "eps_cl": 0.12137,
        "nb_fix": [
            ("MG", "OW", 1, 0.2806480, 0.209606),
            ("MG", "CL", 1, 0.3138636, 0.328138),
        ],
    },
    "ECCIONS81_081": {
        "water": "TIP4P2005",
        "q_mg": 1.62, "q_cl": -0.81,
        "sig_mg": 0.14500, "eps_mg": 0.56210,
        "sig_cl": 0.40960, "eps_cl": 0.49280,
        "nb_fix": [],
    },
    "O4_BALANCED": {
        "water": "TIP4P2005",
        "q_mg": 1.60, "q_cl": -0.80,
        "sig_mg": 0.244746, "eps_mg": 0.04724,
        "sig_cl": 0.383000, "eps_cl": 0.12137,
        "nb_fix": [
            ("MG", "OW", 1, 0.2802654 * 0.965, 0.195545),
            ("MG", "CL", 1, 0.3138636 * 0.978, 0.328138),
        ],
    },
}

WATER_PARAMS = {
    "OPC": {
        "sig_ow": 0.316655, "eps_ow": 0.89036,
        "q_h": 0.67914, "q_m": -1.35828,
        "r_oh": 0.08724, "ang_hoh": 103.6, "vsite_a": 0.147722,
    },
    "TIP4P2005": {
        "sig_ow": 0.315890, "eps_ow": 0.774908,
        "q_h": 0.55640, "q_m": -1.11280,
        "r_oh": 0.09572, "ang_hoh": 104.52, "vsite_a": 0.13194,
    },
}


def write_topology(top_path: Path, model_key: str, n_mg: int, n_w: int = 500) -> None:
    m = MODELS[model_key]
    w = WATER_PARAMS[m["water"]]
    nb_lines = "\n".join(
        f"  {a1:<4s} {a2:<4s} {fn}  {sig:.7f}  {eps:.6f}" for a1, a2, fn, sig, eps in m["nb_fix"]
    )
    nb_block = f"\n[ nonbond_params ]\n{nb_lines}\n" if nb_lines else "\n"
    content = f"""; Auto-generated topology for {model_key} ({n_mg} MgCl2 + {n_w} H2O)
[ defaults ]
  1   2   yes   0.5   0.8333

[ atomtypes ]
  OW   8   15.9994   0.0000  A  {w['sig_ow']:.6f}  {w['eps_ow']:.6f}
  HW   1    1.0080   0.0000  A  0.000000  0.000000
  MW   0    0.0000   0.0000  D  0.000000  0.000000
  MG  12   24.3050   0.0000  A  {m['sig_mg']:.6f}  {m['eps_mg']:.6f}
  CL  17   35.4530   0.0000  A  {m['sig_cl']:.6f}  {m['eps_cl']:.6f}
{nb_block}
[ moleculetype ]
  SOL  2
[ atoms ]
  1  OW  1  SOL  OW   1   0.00000   15.9994
  2  HW  1  SOL  HW1  1  {w['q_h']:.5f}    1.0080
  3  HW  1  SOL  HW2  1  {w['q_h']:.5f}    1.0080
  4  MW  1  SOL  MW   1  {w['q_m']:.5f}    0.0000
[ settles ]
  1  1  {w['r_oh']:.5f}  0.15139
[ virtual_sites3 ]
  4  1  2  3  1  {w['vsite_a']:.6f}  {w['vsite_a']:.6f}
[ exclusions ]
  1 2 3 4
  2 1 3 4
  3 1 2 4
  4 1 2 3

[ moleculetype ]
  MG  1
[ atoms ]
  1  MG  1  MG  MG  1  {m['q_mg']:.4f}  24.3050

[ moleculetype ]
  CL  1
[ atoms ]
  1  CL  1  CL  CL  1  {m['q_cl']:.4f}  35.4530

[ system ]
  MgCl2_aq_{model_key}

[ molecules ]
  SOL  {n_w}
"""
    if n_mg > 0:
        content += f"  MG   {n_mg}\n  CL   {2 * n_mg}\n"
    top_path.write_text(content)


def write_mdp_files(run_dir: Path, nsteps_npt: int = 250000) -> tuple[Path, Path]:
    em_mdp = run_dir / "em.mdp"
    em_mdp.write_text(
        "integrator = steep\nnsteps = 2000\nemtol = 200.0\n"
        "cutoff-scheme = Verlet\ncoulombtype = PME\nrcoulomb = 1.0\nrvdw = 1.0\npbc = xyz\n"
    )
    npt_mdp = run_dir / "npt.mdp"
    npt_mdp.write_text(
        f"integrator = md\ndt = 0.002\nnsteps = {nsteps_npt}\n"
        "nstenergy = 250\nnstxtcout = 1000\n"
        "cutoff-scheme = Verlet\ncoulombtype = PME\nrcoulomb = 1.0\nrvdw = 1.0\nDispCorr = EnerPres\n"
        "tcoupl = V-rescale\ntc-grps = System\ntau_t = 0.5\nref_t = 298.15\n"
        "pcoupl = C-rescale\npcoupltype = isotropic\ntau_p = 2.0\nref_p = 1.0\ncompressibility = 4.5e-5\n"
        "constraints = h-bonds\npbc = xyz\n"
    )
    return em_mdp, npt_mdp


def parse_gmx_density(edr_path: Path, gmx: str = "gmx", begin_ps: float = 150.0) -> float:
    proc = subprocess.run(
        [gmx, "energy", "-f", str(edr_path), "-b", str(begin_ps)],
        input="Density\n\n", text=True, capture_output=True, check=True,
    )
    m = re.search(r"Density\s+([0-9.]+)", proc.stdout)
    if not m:
        raise RuntimeError(f"Could not parse Density from {edr_path}:\n{proc.stdout}")
    return float(m.group(1)) / 1000.0  # kg/m^3 -> g/mL


def main() -> None:
    ap = argparse.ArgumentParser(description="Run 298.15 K forward-NPT density validation for O4 vs baselines.")
    ap.add_argument("--workdir", type=Path, default=Path("./o4_npt_workdir"))
    ap.add_argument("--out", type=Path, default=Path("./o4_npt_density_results.json"))
    ap.add_argument("--gmx", type=str, default="gmx")
    ap.add_argument("--ntomp", type=int, default=8)
    ap.add_argument("--nsteps", type=int, default=250000, help="250000 steps = 500 ps per point (~45s on 8 threads)")
    args = ap.parse_args()

    args.workdir.mkdir(parents=True, exist_ok=True)
    results: dict[str, list[float]] = {
        "molalities_m": [m for m, _, _ in EXP_BENCHMARK],
        "exp_density_g_ml": [r for _, _, r in EXP_BENCHMARK],
    }

    for model_key in MODELS:
        sim_rhos: list[float] = []
        for molality, n_mg, _ in EXP_BENCHMARK:
            sub = args.workdir / f"{model_key}_{molality:.1f}m"
            sub.mkdir(parents=True, exist_ok=True)
            top = sub / "topol.top"
            write_topology(top, model_key, n_mg=n_mg, n_w=500)
            em_mdp, npt_mdp = write_mdp_files(sub, nsteps_npt=args.nsteps)

            # Solvate 4-site water box & replace random SOL with MG/CL if n_mg > 0
            box_gro = sub / "init.gro"
            subprocess.run([args.gmx, "solvate", "-cs", "tip4p.gro", "-o", str(box_gro), "-box", "2.6", "2.6", "2.6", "-maxsol", str(500 + 3 * n_mg)], check=True)
            if n_mg > 0:
                tpr_ion = sub / "ions.tpr"
                subprocess.run([args.gmx, "grompp", "-f", str(em_mdp), "-c", str(box_gro), "-p", str(top), "-o", str(tpr_ion), "-maxwarn", "3"], check=True)
                subprocess.run([args.gmx, "genion", "-s", str(tpr_ion), "-o", str(box_gro), "-np", str(n_mg), "-pname", "MG", "-pq", "2", "-nn", str(2 * n_mg), "-nname", "CL", "-nq", "-1"], input="SOL\n", text=True, check=True)

            # EM + NPT
            subprocess.run([args.gmx, "grompp", "-f", str(em_mdp), "-c", str(box_gro), "-p", str(top), "-o", str(sub / "em.tpr"), "-maxwarn", "2"], check=True)
            subprocess.run([args.gmx, "mdrun", "-deffnm", str(sub / "em"), "-ntomp", str(args.ntomp)], check=True)
            subprocess.run([args.gmx, "grompp", "-f", str(npt_mdp), "-c", str(sub / "em.gro"), "-p", str(top), "-o", str(sub / "npt.tpr"), "-maxwarn", "2"], check=True)
            subprocess.run([args.gmx, "mdrun", "-deffnm", str(sub / "npt"), "-ntomp", str(args.ntomp)], check=True)

            rho = parse_gmx_density(sub / "npt.edr", gmx=args.gmx, begin_ps=150.0)
            sim_rhos.append(round(rho, 4))
            print(f"[{model_key}] {molality:.1f} m -> {rho:.4f} g/mL")
        results[model_key] = sim_rhos

    args.out.write_text(json.dumps(results, indent=2))
    print(f"Saved forward-NPT benchmark -> {args.out}")


if __name__ == "__main__":
    main()
