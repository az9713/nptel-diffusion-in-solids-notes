"""Finite-slab modes, source parameters, and numerical refinement checks."""

import argparse
import json
from pathlib import Path
import numpy as np
from scipy.special import erfc


def absorbing_profile(x, tau, terms=100):
    odd = np.arange(1, 2 * terms, 2, dtype=float)
    return np.sum(
        4
        / (np.pi * odd[:, None])
        * np.sin(np.pi * odd[:, None] * x[None, :])
        * np.exp(-(np.pi**2) * odd[:, None] ** 2 * tau),
        axis=0,
    )


def finite_difference(cells, final_tau, ratio=0.4):
    if cells < 3 or not 0 < ratio <= 0.5 or final_tau <= 0:
        raise ValueError("Invalid grid, time, or explicit mesh ratio")
    x = np.linspace(0, 1, cells + 1)
    dx = 1 / cells
    steps = int(np.ceil(final_tau / (ratio * dx * dx)))
    dtau = final_tau / steps
    r = dtau / (dx * dx)
    u = np.sin(np.pi * x)
    u[[0, -1]] = 0
    for _ in range(steps):
        old = u.copy()
        u[1:-1] = old[1:-1] + r * (old[2:] - 2 * old[1:-1] + old[:-2])
        assert np.min(u) >= -1e-14
    exact = np.sin(np.pi * x) * np.exp(-(np.pi**2) * final_tau)
    amplification = 1 - 4 * r * np.sin(np.pi / (2 * cells)) ** 2
    discrete_exact = np.sin(np.pi * x) * amplification**steps
    assert np.max(np.abs(u - discrete_exact)) < 1e-12
    return dict(
        cells=cells,
        steps=steps,
        actual_ratio=r,
        max_error=float(np.max(np.abs(u - exact))),
    )


def run():
    odd = np.arange(1, 401, 2, dtype=float)
    tau = 0.1
    mean = np.sum(8 / (np.pi**2 * odd**2) * np.exp(-(odd**2) * np.pi**2 * tau))
    first_mean = 8 / np.pi**2 * np.exp(-(np.pi**2) * tau)
    outward = 8 * np.sum(np.exp(-(odd**2) * np.pi**2 * tau))
    eps = 1e-6

    def slab_mean(time):
        return np.sum(
            8 / (np.pi**2 * odd**2) * np.exp(-(odd**2) * np.pi**2 * time)
        )

    derivative = (slab_mean(tau + eps) - slab_mean(tau - eps)) / (2 * eps)
    assert abs(derivative + outward) < 1e-8
    x = np.linspace(0, 1, 10001)
    closed = 1 + 0.4 * np.cos(2 * np.pi * x) * np.exp(-4 * np.pi**2 * tau)
    assert abs(np.trapezoid(closed, x) - 1) < 1e-12
    refinements = [finite_difference(n, 0.05) for n in (40, 80, 160)]
    ratios = [
        refinements[i]["max_error"] / refinements[i + 1]["max_error"]
        for i in range(2)
    ]
    assert all(3.8 < value < 4.2 for value in ratios)
    # An unstable update makes a nonnegative spike negative for r>1/2.
    invalid = 1 - 2 * 0.6
    assert invalid < 0
    # Visually checked source Scilab inputs; not measured steel data.
    Q, D0, gas_constant = 200000.0, 1e-5, 8.314
    T_C, days = 1000.0, 1.0
    T_K, seconds = T_C + 273.15, days * 86400
    source_D = D0 * np.exp(-Q / (gas_constant * T_K))
    incorrect_D = D0 * np.exp(-200 / (gas_constant * T_K))
    normalized_at_1mm = erfc(1e-3 / (2 * np.sqrt(source_D * seconds)))
    return dict(
        absorbing_mean_at_tau_point1=float(mean),
        first_mode_mean_at_tau_point1=float(first_mean),
        first_mode_relative_error=float((mean - first_mean) / mean),
        outward_flux_in_Dc0_per_L_units=float(outward),
        closed_mean=1.0,
        refinements=refinements,
        error_ratios=ratios,
        unstable_spike_center=invalid,
        illustrative_source_parameters=dict(
            Q_J_per_mol=Q,
            D0_m2_per_s=D0,
            R_J_per_mol_K=gas_constant,
            T_C=T_C,
            T_K=T_K,
            days=days,
        ),
        illustrative_source_D_m2_per_s=float(source_D),
        activation_unit_error_multiplier=float(incorrect_D / source_D),
        illustrative_normalized_1mm_profile=float(normalized_at_1mm),
    )


def figures():
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams["svg.hashsalt"] = "ch04"
    import matplotlib.pyplot as plt

    root = Path(__file__).resolve().parents[1]
    plt.style.use("dark_background")
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8), constrained_layout=True)
    x = np.linspace(0, 1, 501)
    for tau in (0.01, 0.05, 0.2):
        axes[0].plot(x, absorbing_profile(x, tau), label=f"τ={tau:g}")
        axes[1].plot(
            x, 1 + 0.4 * np.cos(2 * np.pi * x) * np.exp(-4 * np.pi**2 * tau)
        )
    for axis in axes:
        axis.set_xlabel("Position x/L")
        axis.set_ylabel("Normalized concentration")
        axis.grid(alpha=0.2)
    axes[0].set_title("Absorbing faces: amount decreases")
    axes[1].set_title("Closed specimen: mean remains one")
    axes[0].legend()
    (root / "figures").mkdir(exist_ok=True)
    fig.savefig(
        root / "figures/ch04-boundary-models.svg", metadata={"Date": None}
    )
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--figures", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(), indent=2))
    if args.figures:
        figures()
