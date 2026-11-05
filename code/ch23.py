"""Synthetic metallic diffusion pathways, trapping, and hybrid transport."""

from pathlib import Path
import json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch23"
ROOT = Path(__file__).resolve().parents[1]
R = 8.31446261815324


def main():
    temperature = np.linspace(600, 1300, 300)
    A1, A2, Q1, Q2 = 1e-5, 1e-3, 180000.0, 220000.0
    D1 = A1 * np.exp(-Q1 / (R * temperature))
    D2 = A2 * np.exp(-Q2 / (R * temperature))
    apparent = (Q1 * D1 + Q2 * D2) / (D1 + D2)
    # Dilute reversible traps: c_trapped = K c_mobile.
    Dmobile, K = 1e-9, 99.0
    theta, Di, Ds = 1e-6, 1e-8, 1e-17
    hybrid = theta * Di + (1 - theta) * Ds
    T = 1000.0
    d1, d2 = A1 * np.exp(-Q1 / (R * T)), A2 * np.exp(-Q2 / (R * T))
    dx = 1e-3
    numeric_Q = (
        -R
        * (
            np.log(
                A1 * np.exp(-Q1 * (1 / T + dx / 1000) / R)
                + A2 * np.exp(-Q2 * (1 / T + dx / 1000) / R)
            )
            - np.log(
                A1 * np.exp(-Q1 * (1 / T - dx / 1000) / R)
                + A2 * np.exp(-Q2 * (1 / T - dx / 1000) / R)
            )
        )
        / (2 * dx / 1000)
    )
    exact_Q = (Q1 * d1 + Q2 * d2) / (d1 + d2)
    assert abs(numeric_Q - exact_Q) / exact_Q < 1e-6
    out = {
        "status": "synthetic coefficients, not material data",
        "at_1000K": {
            "D1_m2_s": float(d1),
            "D2_m2_s": float(d2),
            "Q_effective_J_mol": float(exact_Q),
            "Q_finite_difference_J_mol": float(numeric_Q),
        },
        "trap_example": {
            "Dmobile_m2_s": Dmobile,
            "K": K,
            "Dapparent_m2_s": Dmobile / (1 + K),
        },
        "hybrid": {
            "theta_i": theta,
            "D_eff_m2_s": hybrid,
            "interstitial_share": theta * Di / hybrid,
        },
        "divacancy_Q_J_mol": 2 * 100000 - 30000 + 60000,
        "composition_example": {
            "N": 0.02,
            "b1": 5.0,
            "linear_factor": 1.1,
            "exponential_factor": float(np.exp(0.1)),
        },
    }
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].semilogy(1000 / temperature, D1 + D2, label="Sum")
    axes[0].semilogy(1000 / temperature, D1, "--", label="Path1")
    axes[0].semilogy(1000 / temperature, D2, ":", label="Path2")
    axes[0].set(xlabel="1000 / T (K⁻¹ ×1000)", ylabel="D (m² s⁻¹)")
    axes[0].legend()
    axes[1].plot(temperature, apparent / 1000)
    axes[1].set(xlabel="Temperature (K)", ylabel="Apparent Q (kJ mol⁻¹)")
    for ax in axes:
        ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(ROOT / "assets/ch23-pathways.svg", metadata={"Date": None})
    plt.close(fig)
    (ROOT / "code/ch23-output.json").write_text(
        json.dumps(out, indent=2) + "\n"
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
