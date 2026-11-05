"""Charged-defect models and frame-verified lecture oxygen fit."""

from pathlib import Path
import json
import numpy as np
from scipy.integrate import solve_ivp
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch25"
ROOT = Path(__file__).resolve().parents[1]
R = 8.31446261815324


def main():
    T = np.array([600, 650, 700, 750, 800, 850]) + 273.15
    D = np.array([3.24e-20, 2e-19, 1.03e-18, 4.48e-18, 1.71e-17, 5.77e-17])
    slope, intercept = np.polyfit(1 / T, np.log(D), 1)
    prediction = np.exp(intercept + slope / (1000 + 273.15))
    times = np.linspace(0, 300, 301)

    def reaction(t, y):
        rate = 2 * y[0] * y[1] - 0.5 * y[2]
        return [-rate, -rate, rate]

    sol = solve_ivp(reaction, [0, 20], [1, 0.2, 0], rtol=1e-10, atol=1e-12)
    dopant_error = float(np.max(abs(sol.y[0] + sol.y[2] - 1)))
    defect_error = float(np.max(abs(sol.y[1] + sol.y[2] - 0.2)))
    assert dopant_error < 1e-12 and defect_error < 1e-12
    enhancement = 1 + 9 * (1 - np.exp(-0.01 * times))
    ratio = np.logspace(-2, 2, 200)
    diffusivity = 1e-18 + ratio * 2e-18
    out = {
        "status": "synthetic defects; separately labeled source oxygen D data",
        "oxygen_tutorial": {
            "source_frame": "L55 at1248s",
            "T_C": [600, 650, 700, 750, 800, 850],
            "D_m2_s": D.tolist(),
            "slope_K": float(slope),
            "ln_prefactor_SI": float(intercept),
            "Q_J_mol": float(-R * slope),
            "D_at_1000C_m2_s": float(prediction),
            "limit": "lecture exercise extrapolation; no empirical validation",
        },
        "charged_model_at_ratio_10_m2_s": float(1e-18 + 10 * 2e-18),
        "source_sink_x_at100s": float(1 + 9 * (1 - np.exp(-1))),
        "pair_conservation": {
            "dopant_error": dopant_error,
            "defect_error": defect_error,
        },
        "Si31_activity_fraction_half_life_2p6h": {
            str(h): float(2 ** (-h / 2.6)) for h in [1, 10, 50, 100, 200]
        },
    }
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].loglog(ratio, diffusivity)
    axes[0].set(
        xlabel="Electron density / intrinsic density",
        ylabel="Synthetic tracer D (m² s⁻¹)",
    )
    axes[1].plot(times, enhancement)
    axes[1].set(xlabel="Time (s)", ylabel="Defect supersaturation x")
    for ax in axes:
        ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(ROOT / "assets/ch25-defects.svg", metadata={"Date": None})
    plt.close(fig)
    (ROOT / "code/ch25-output.json").write_text(
        json.dumps(out, indent=2) + "\n"
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
