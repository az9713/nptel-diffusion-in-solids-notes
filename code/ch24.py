"""Ideal mixing entropy and explicitly synthetic diffusion comparisons."""

from pathlib import Path
import json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch24"
ROOT = Path(__file__).resolve().parents[1]
R = 8.31446261815324


def entropy(fractions):
    x = np.asarray(fractions, dtype=float)
    if np.any(x < 0) or not np.isclose(x.sum(), 1):
        raise ValueError("Mole fractions must be nonnegative and sum to one")
    return float(-R * np.sum(x[x > 0] * np.log(x[x > 0])))


def main():
    # Synthetic materials A/B: SI prefactors; Q in J/mol; Tm in K.
    A = {"prefactor": 1e-6, "Q": 180000.0, "Tm": 1500.0}
    B = {"prefactor": 1e-8, "Q": 140000.0, "Tm": 2000.0}

    def rate(material, T):
        return material["prefactor"] * np.exp(-material["Q"] / (R * T))

    cross = (A["Q"] - B["Q"]) / (R * np.log(A["prefactor"] / B["prefactor"]))
    tests = {}
    for T in [800.0, 1200.0]:
        tests[str(T)] = {"A": float(rate(A, T)), "B": float(rate(B, T))}
    homologous = {
        "T_over_Tm": 0.6,
        "A_T_K": 900.0,
        "B_T_K": 1200.0,
        "A": float(rate(A, 900.0)),
        "B": float(rate(B, 1200.0)),
    }
    assert abs(rate(A, cross) / rate(B, cross) - 1) < 1e-13
    fractions = [0.4, 0.15, 0.15, 0.15, 0.15]
    out = {
        "status": "synthetic rate comparison; no empirical HEA fit",
        "entropy_equiatomic_5_J_mol_K": entropy([0.2] * 5),
        "entropy_nonequiatomic_J_mol_K": entropy(fractions),
        "crossover_K": float(cross),
        "absolute_comparisons": tests,
        "homologous_comparison": homologous,
        "materials": {"A": A, "B": B},
    }
    T = np.linspace(650, 1400, 200)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.semilogy(1000 / T, rate(A, T), label="Synthetic A")
    ax.semilogy(1000 / T, rate(B, T), label="Synthetic B")
    ax.axvline(1000 / cross, color="gray", linestyle=":")
    ax.set(xlabel="1000 / T (K⁻¹ ×1000)", ylabel="Tracer diffusivity (m² s⁻¹)")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(ROOT / "assets/ch24-crossover.svg", metadata={"Date": None})
    plt.close(fig)
    (ROOT / "code/ch24-output.json").write_text(
        json.dumps(out, indent=2) + "\n"
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
