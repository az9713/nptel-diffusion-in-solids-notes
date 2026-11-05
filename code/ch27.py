"""Ideal Frenkel/Schottky chemistry and correlation teaching checks."""

from pathlib import Path
import json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch27"
ROOT = Path(__file__).resolve().parents[1]
kB, e = 1.380649e-23, 1.602176634e-19


def populations(d, K):
    v = (d + np.sqrt(d * d + 4 * K)) / 2
    return v, K / v


def main():
    K, mobility_v, mobility_i = 1e-12, 1.0, 100.0
    d = np.linspace(0, 3e-5, 301)
    v, i = populations(d, K)
    cond = mobility_v * v + mobility_i * i
    v_min = np.sqrt(mobility_i * K / mobility_v)
    i_min = K / v_min
    d_min = v_min - i_min
    assert abs(v_min * i_min - K) < 1e-25
    # Association: total donor d0, free donor = free vacancy = x.
    d0, Kass = 1e-4, 1e6
    free = 2 * d0 / (1 + np.sqrt(1 + 4 * Kass * d0))
    bound = d0 - free
    assert abs(bound - Kass * free**2) < 1e-17
    T, n, Dsigma, f, fI = 600.0, 1e27, 1e-12, 0.6, 0.8
    sigma = n * e * e * Dsigma / (kB * T)
    HR = f / fI
    # Intrinsic/extrinsic crossover: sqrt(Ks)=d, Ks=exp(-Hs/RT).
    R, Hs, dopant = 8.31446261815324, 200000.0, 1e-4
    cross = -Hs / (2 * R * np.log(dopant))
    out = {
        "status": "synthetic ideal dilute defect chemistry",
        "Frenkel": {
            "K": K,
            "intrinsic_v": float(np.sqrt(K)),
            "minimum_d": float(d_min),
            "minimum_v": float(v_min),
            "minimum_i": float(i_min),
            "minimum_sigma_scaled": float(2 * mobility_v * v_min),
            "intrinsic_sigma_scaled": float(
                (mobility_v + mobility_i) * np.sqrt(K)
            ),
            "max_mass_action_error": float(np.max(abs(v * i - K))),
        },
        "association": {
            "total_dopant": d0,
            "K": Kass,
            "free_vacancy": float(free),
            "bound_fraction": float(bound / d0),
        },
        "correlations": {
            "f": f,
            "f_I": fI,
            "Haven_ratio": HR,
            "sigma_S_m": sigma,
            "D_tracer_m2_s": HR * Dsigma,
        },
        "Schottky_crossover_K": float(cross),
        "association_odds_example": {
            "p1": 0.5,
            "p2": 1.0,
            "fraction1": 1 / 3,
            "fraction2": 0.5,
            "ratio": 2 / 3,
        },
    }
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].plot(d, v, label="Vacancies")
    axes[0].plot(d, i, label="Interstitials")
    axes[0].set(
        xlabel="Donor fraction d", ylabel="Normalized defect concentration"
    )
    axes[0].legend()
    axes[1].plot(d, cond)
    axes[1].axvline(d_min, color="gray", linestyle=":")
    axes[1].set(xlabel="Donor fraction d", ylabel="Scaled conductivity")
    for ax in axes:
        ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(ROOT / "assets/ch27-minimum.svg", metadata={"Date": None})
    plt.close(fig)
    (ROOT / "code/ch27-output.json").write_text(
        json.dumps(out, indent=2) + "\n"
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
