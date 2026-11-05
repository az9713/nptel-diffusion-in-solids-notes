"""Synthetic correlated-walk moments and five-frequency sensitivity."""

import json
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch08"
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def finite_factor(n, rho):
    lag = np.arange(1, n)
    return float(1 + 2 * np.sum((1 - lag / n) * rho**lag))


def distribution_msd(n, rho):
    """Propagate the full two-direction position distribution."""
    keep = (1 + rho) / 2
    probability = np.zeros((2 * n + 1, 2))
    probability[n, :] = 0.5
    for _ in range(n):
        updated = np.zeros_like(probability)
        updated[1:, 1] = (
            keep * probability[:-1, 1] + (1 - keep) * probability[:-1, 0]
        )
        updated[:-1, 0] = (
            keep * probability[1:, 0] + (1 - keep) * probability[1:, 1]
        )
        probability = updated
    assert np.isclose(probability.sum(), 1)
    positions = np.arange(-n, n + 1)
    return float(np.sum(positions**2 * probability.sum(axis=1)))


def fcc_factor(w1, w2, w3, escape):
    numerator = 2 * w1 + 7 * escape * w3
    return numerator / (2 * w2 + numerator)


def run():
    rhos = [-0.5, 0.0, 0.5]
    checks = []
    for rho in rhos:
        moment = distribution_msd(40, rho)
        assert np.isclose(moment, 40 * finite_factor(40, rho))
        checks.append(
            {
                "rho": rho,
                "f_40": moment / 40,
                "f_200": finite_factor(200, rho),
                "f_infinity": (1 + rho) / (1 - rho),
            }
        )
    n = np.arange(1, 201)
    fig, ax = plt.subplots(figsize=(7, 3.8), layout="constrained")
    for rho in rhos:
        ax.plot(
            n,
            [finite_factor(int(count), rho) for count in n],
            label=f"rho = {rho:g}",
        )
    ax.set(
        xlabel="Number of jumps n",
        ylabel="Finite-step correlation factor",
        title="Exact synthetic two-direction Markov model",
    )
    ax.grid(alpha=0.25)
    ax.legend()
    fig.savefig(ROOT / "assets/ch08-correlation.svg", metadata={"Date": None})
    plt.close(fig)
    w1, w2, w3, escape = 1.0, 2.0, 0.5, 0.8
    immediate_reverse = w2 / (w2 + 4 * w1 + 7 * w3)
    factor = fcc_factor(w1, w2, w3, escape)
    assert fcc_factor(w1, 0, w3, escape) == 1
    assert fcc_factor(0, w2, 0, escape) == 0
    scale_check = fcc_factor(10 * w1, 10 * w2, 10 * w3, escape)
    assert np.isclose(factor, scale_check)
    return {
        "synthetic": True,
        "walk_checks": checks,
        "rough_fcc_1_minus_2_over_z": 1 - 2 / 12,
        "five_frequency_example": {
            "w1_per_s": w1,
            "w2_per_s": w2,
            "w3_per_s": w3,
            "externally_supplied_F": escape,
            "immediate_reverse_probability": immediate_reverse,
            "full_model_f": factor,
            "scaled_all_rates_f": scale_check,
            "note": "F is illustrative input, not a lattice-return solution.",
        },
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
