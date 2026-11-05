"""Profile interpretation checks using declared synthetic inputs."""

import json
from pathlib import Path

import matplotlib

import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch11"

BASE = Path(__file__).resolve().parents[1]
amounts = np.array([2.0, 1.0])
fractions = np.array([0.2, 0.8])
mean = float(amounts @ fractions / amounts.sum())
c_left, c_right = 10000.0, 20000.0
j_left, j_right = 1e-8, 3e-8
velocity = (j_right - j_left) / (c_right - c_left)
assert abs(velocity * (c_right - c_left) - (j_right - j_left)) < 1e-22
x = np.linspace(-1, 1, 401)
spectator = 0.25 + 0.02 * np.sin(np.pi * x) ** 3
assert abs(spectator[0] - spectator[-1]) < 1e-14
assert spectator.max() > spectator[0] + 0.019
assert spectator.min() < spectator[0] - 0.019
spectator_excess = float(np.trapezoid(spectator - 0.25, x))
assert abs(spectator_excess) < 1e-14
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
for width, label in [
    (0.1, "narrow homogeneity range"),
    (0.5, "wide homogeneity range"),
]:
    xx = np.array([-1, -0.4, -0.4, 0.4, 0.4, 1])
    zz = np.array([0.05, 0.1, 0.5 - width / 2, 0.5 + width / 2, 0.9, 0.95])
    ax[0].plot(xx, zz, label=label)
ax[0].set(xlabel="Position / reference length", ylabel="B mole fraction")
ax[0].legend(fontsize=8)
ax[1].plot(x, spectator)
ax[1].set(
    xlabel="Position / reference length",
    ylabel="Spectator mole fraction",
    ylim=(0.225, 0.275),
)
fig.tight_layout()
fig.savefig(BASE / "assets/figures/ch11-profiles.svg", metadata={"Date": None})
out = {
    "synthetic": True,
    "closed_specimen_final_mole_fraction": mean,
    "interface_velocity_m_s": velocity,
    "spectator_endpoint": float(spectator[0]),
    "spectator_interior_maximum": float(spectator.max()),
    "spectator_interior_minimum": float(spectator.min()),
    "spectator_normalized_excess_integral": spectator_excess,
    "tutorial_mixing_energy_J_mol": 3.0 - 8.0,
    "tutorial_temperature_K": 5.0 / 0.005,
    "half_mole_mixture_endpoints": float(np.mean(fractions)),
}
text = json.dumps(out, indent=2)
(BASE / "code/ch11-output.json").write_text(text + "\n", encoding="utf-8")
print(text)
