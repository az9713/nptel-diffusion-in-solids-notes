"""Synthetic binary thermodynamics; no material assessment is implied."""

import json
from pathlib import Path

import matplotlib

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch10"

BASE = Path(__file__).resolve().parents[1]
R = 8.31446261815324
T = 1000.0
omega = 3.0 * R * T


def energy(z):
    return R * T * (z * np.log(z) + (1 - z) * np.log(1 - z)) + omega * z * (
        1 - z
    )


def derivative(z):
    return R * T * np.log(z / (1 - z)) + omega * (1 - 2 * z)


z = np.linspace(0.0001, 0.9999, 1001)
za = brentq(derivative, 0.001, 0.2)
zb = 1 - za
spinodal = (1 - np.sqrt(1 - 2 / 3)) / 2
bulk = 0.3
fraction = (bulk - za) / (zb - za)
mu_a = energy(bulk) - bulk * derivative(bulk)
mu_b = energy(bulk) + (1 - bulk) * derivative(bulk)
assert abs(derivative(za)) < 1e-7
assert abs(energy(za) - energy(zb)) < 1e-8
assert abs((1 - fraction) * za + fraction * zb - bulk) < 1e-12
fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(z, energy(z) / 1000, label="homogeneous regular solution")
ax.plot([za, zb], [energy(za) / 1000] * 2, "--", label="two-phase tangent")
ax.scatter(
    [za, zb, bulk], [energy(za) / 1000, energy(zb) / 1000, energy(bulk) / 1000]
)
ax.set(xlabel="B mole fraction", ylabel="Mixing Gibbs energy (kJ/mol)")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.25))
fig.tight_layout()
(BASE / "assets/figures").mkdir(parents=True, exist_ok=True)
fig.savefig(
    BASE / "assets/figures/ch10-free-energy.svg", metadata={"Date": None}
)
out = {
    "synthetic": True,
    "temperature_K": T,
    "omega_J_mol": omega,
    "coexistence_mole_fractions": [za, zb],
    "spinodal_mole_fractions": [spinodal, 1 - spinodal],
    "bulk_mole_fraction": bulk,
    "B_rich_mole_fraction": fraction,
    "homogeneous_energy_J_mol": float(energy(bulk)),
    "two_phase_energy_J_mol": float(energy(za)),
    "mu_A_J_mol": float(mu_a),
    "mu_B_J_mol": float(mu_b),
    "ideal_equimolar_energy_J_mol": -R * T * np.log(2),
}
text = json.dumps(out, indent=2)
(BASE / "code/ch10-output.json").write_text(text + "\n", encoding="utf-8")
print(text)
