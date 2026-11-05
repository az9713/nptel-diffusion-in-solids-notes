"""Synthetic equilibrium, binding, strain and positron-trapping checks.

Writes assets/ch06-trapping.svg; prints machine-readable results.
"""

import json
from pathlib import Path
import numpy as np
from scipy.constants import Boltzmann, elementary_charge, Avogadro
import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch06"
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
KB_EV = Boltzmann / elementary_charge


def run():
    temperature = np.array([300.0, 1200.0])
    g_ev = 1.2
    odds = np.exp(-g_ev / (KB_EV * temperature))
    fractions = odds / (1 + odds)
    copper_t = 1273.15
    copper_x = 1 / (1 + np.exp(0.9 / (KB_EV * copper_t)))
    atom_density = 8400 / 0.0635 * Avogadro
    site_density = atom_density / (1 - copper_x)
    copper_vacancies = site_density * copper_x
    # Pair fractions per lattice site. Positive binding stabilizes a pair.
    pair_t = np.array([800.0, 1200.0, 1600.0])
    x1 = np.exp(-0.9 / (KB_EV * pair_t))
    x2 = 6 * np.exp(0.15 / (KB_EV * pair_t)) * x1**2
    assert np.all(x2 < x1)
    xb, z = 0.005, 12
    unpaired_linear = 1 - z * xb
    no_solute_neighbor = (1 - xb) ** z
    linear_strain, lattice_strain = 0.01, 0.0099
    site_ratio = ((1 + linear_strain) / (1 + lattice_strain)) ** 3
    strain_x = 1 - 1 / site_ratio
    linear_x = 3 * (linear_strain - lattice_strain)
    lf, lt, capture = 1e10, 5e9, 1e10
    mean = (1 + capture / lt) / (lf + capture)
    inferred = (1 - mean * lf) / (mean - 1 / lt)
    assert np.isclose(inferred / capture, 1)
    kappa = np.logspace(-3, 3, 301) * lf
    lifetime = (1 + kappa / lt) / (lf + kappa)
    assert np.all(np.diff(lifetime) > 0)
    fig, ax = plt.subplots(figsize=(7, 3.8), layout="constrained")
    ax.semilogx(kappa / lf, lifetime / 1e-12, color="#176e8c")
    ax.axhline(
        200, color="#8b5d18", linestyle="--", label="Trap lifetime limit"
    )
    ax.set(
        xlabel="Capture rate / free annihilation rate",
        ylabel="Mean lifetime (ps)",
        title="Synthetic irreversible single-trap model",
    )
    ax.grid(alpha=0.25)
    ax.legend()
    fig.savefig(ROOT / "assets/ch06-trapping.svg", metadata={"Date": None})
    plt.close(fig)
    return dict(
        synthetic=True,
        k_B_eV_per_K=KB_EV,
        temperatures_K=temperature.tolist(),
        vacancy_fractions_1_2eV=fractions.tolist(),
        copper_exercise=dict(
            temperature_K=copper_t,
            atomic_density_per_m3=atom_density,
            vacancy_fraction=copper_x,
            vacancy_number_per_m3=copper_vacancies,
        ),
        pair_temperatures_K=pair_t.tolist(),
        monovacancy_fractions=x1.tolist(),
        divacancy_pair_fractions=x2.tolist(),
        pair_to_mono_ratio=(x2 / x1).tolist(),
        unpaired_linear=unpaired_linear,
        independent_no_neighbor=no_solute_neighbor,
        exact_strain_vacancy_fraction=strain_x,
        linear_strain_estimate=linear_x,
        mean_positron_lifetime_ps=mean / 1e-12,
        recovered_capture_rate_per_s=inferred,
    )


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
