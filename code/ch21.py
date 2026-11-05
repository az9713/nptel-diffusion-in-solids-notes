"""Synthetic pipe-path and leakage checks; SI units unless stated."""

from pathlib import Path
import json
import numpy as np
import matplotlib

import matplotlib.pyplot as plt

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch21"
ROOT = Path(__file__).resolve().parents[1]


def main():
    a, rho, D, Dp = 5e-10, 1e14, 1e-20, 1e-12
    phi = np.pi * a * a * rho
    parallel = (1 - phi) * D + phi * Dp
    series = 1 / ((1 - phi) / D + phi / Dp)
    rho_grid = np.logspace(10, 16, 200)
    fraction = np.pi * a * a * rho_grid
    eff = (1 - fraction) * D + fraction * Dp
    R = 8.31446261815324
    Dl = 1.2e-4 * np.exp(-303000 / (R * 673))
    length = np.sqrt(Dl * (14 * 24 * 3600))
    # Two-compartment exchange: capacities phi and 1-phi.
    k = 0.2
    tau = np.linspace(0, 5, 101)
    cp = 1 + (1 - phi) * np.exp(-k * tau)
    cl = 1 - phi * np.exp(-k * tau)
    mass = phi * cp + (1 - phi) * cl
    assert np.max(np.abs(mass - 1)) < 1e-14
    out = {
        "status": "synthetic; lecture tutorial inputs recomputed separately",
        "pipe_fraction": float(phi),
        "spacing_m": float(rho**-0.5),
        "parallel_m2_s": float(parallel),
        "series_m2_s": float(series),
        "pipe_to_lattice_contribution": float(phi * Dp / ((1 - phi) * D)),
        "density_diameter_multiplier": 200.0,
        "tutorial": {
            "D_673K_m2_s": float(Dl),
            "sqrt_Dt_m": float(length),
            "alpha_delta_half_nm": float(5e-10 / (2 * length)),
            "q_ratio": float(np.sin(np.pi / 12) / np.sin(np.pi / 8)),
            "exp_minus_41_m3_s": float(np.exp(-41)),
        },
        "exchange_mass_max_error": float(np.max(np.abs(mass - 1))),
    }
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.loglog(rho_grid, eff, label="Parallel connected pipes")
    ax.axhline(D, color="gray", linestyle="--", label="Lattice alone")
    ax.set(
        xlabel="Dislocation line density (m⁻²)",
        ylabel="Effective diffusivity (m² s⁻¹)",
    )
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(ROOT / "assets/ch21-pathways.svg", metadata={"Date": None})
    plt.close(fig)
    (ROOT / "code/ch21-output.json").write_text(
        json.dumps(out, indent=2) + "\n"
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
