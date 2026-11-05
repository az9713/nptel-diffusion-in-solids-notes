"""Synthetic sublattice thermodynamics and independent kinetic clocks."""

import json
import math
from pathlib import Path

import matplotlib

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch14"

BASE = Path(__file__).resolve().parents[1]
R, temperature = 8.31446261815324, 1000.0
eta = np.linspace(0, 1, 501)
y = (1 + eta) / 2


def xlogx(v):
    a = np.asarray(v)
    return np.where(a > 0, a * np.log(np.maximum(a, 1e-300)), 0)


entropy = -R * (xlogx(y) + xlogx(1 - y))
coupling = 1.5 * R * temperature
g = -coupling * eta**2 / 2 - temperature * entropy
ordered = brentq(lambda q: np.arctanh(q) - 1.5 * q, 0.1, 0.99999)
ordered_y = (1 + ordered) / 2
ordered_s = float(-R * (xlogx(ordered_y) + xlogx(1 - ordered_y)))
assert ordered_s > 0
assert entropy[-1] == 0
time = np.linspace(0, 4e5, 401)
length = 1e-4
diffusivities = [1e-14, 4e-14]
amplitudes = [
    float(np.exp(-(np.pi**2) * d * 1e5 / length**2)) for d in diffusivities
]
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
ax[0].plot(eta, g / 1000)
ax[0].set(xlabel="Order parameter", ylabel="Synthetic g (kJ/mol)")
for d in diffusivities:
    ax[1].plot(
        time / 1e5,
        np.exp(-(np.pi**2) * d * time / length**2),
        label=f"D = {d:g} m²/s",
    )
ax[1].set(xlabel="Time / 100000 s", ylabel="Mode amplitude / initial")
ax[1].legend(fontsize=8)
fig.tight_layout()
fig.savefig(BASE / "assets/figures/ch14-models.svg", metadata={"Date": None})
out = {
    "synthetic": True,
    "temperature_K": temperature,
    "ordered_eta": float(ordered),
    "ordered_sublattice_A_fractions": [ordered_y, 1 - ordered_y],
    "ordered_configurational_entropy_J_mol_K": ordered_s,
    "disordered_entropy_J_mol_K": float(R * np.log(2)),
    "perfect_order_entropy_J_mol_K": float(entropy[-1]),
    "mode_amplitudes_at_100000_s": amplitudes,
    "eight_element_binary_count": math.comb(8, 2),
    "eight_element_ternary_count": math.comb(8, 3),
}
text = json.dumps(out, indent=2)
(BASE / "code/ch14-output.json").write_text(text + "\n", encoding="utf-8")
print(text)
