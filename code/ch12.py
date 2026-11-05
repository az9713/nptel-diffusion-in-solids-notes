"""Boltzmann-Matano inversion of synthetic error-function data."""

import json
from pathlib import Path

import matplotlib

import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import cumulative_trapezoid, trapezoid
from scipy.special import erf

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch12"

BASE = Path(__file__).resolve().parents[1]
D, time = 2e-14, 1e5
scale = np.sqrt(D * time)
x = np.linspace(-10 * scale, 10 * scale, 20001)
y = (1 + erf(x / (2 * scale))) / 2
slope = np.exp(-x * x / (4 * D * time)) / (2 * np.sqrt(np.pi * D * time))
plane = trapezoid(x, y) / (y[-1] - y[0])
integral = cumulative_trapezoid(x - plane, y, initial=0)
estimate = -integral / (2 * time * slope)
interior = (y > 0.05) & (y < 0.95)
relative_error = np.max(np.abs(estimate[interior] / D - 1))
assert relative_error < 1e-5
shift = 0.1 * scale
wrong = -(integral - shift * (y - y[0])) / (2 * time * slope)
records = []
for value in [0.2, 0.5, 0.8]:
    i = np.argmin(abs(y - value))
    records.append(
        {
            "fraction": float(y[i]),
            "D_m2_s": float(estimate[i]),
            "wrong_plane_D_m2_s": float(wrong[i]),
        }
    )
# A smooth deterministic perturbation is an observation error, not dynamics.
perturbed = y + 0.001 * np.sin(50 * x / scale) * y * (1 - y)
observed_slope = np.gradient(perturbed, x)
observed_plane = trapezoid(x, perturbed) / (perturbed[-1] - perturbed[0])
observed_int = cumulative_trapezoid(x - observed_plane, perturbed, initial=0)
observed_D = -observed_int / (2 * time * observed_slope)
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
ax[0].plot(x / scale, y)
ax[0].set(xlim=(-4, 4), xlabel="x / sqrt(Dt)", ylabel="Normalized fraction")
ax[1].plot(y[interior], estimate[interior] / D, label="exact smooth data")
ax[1].plot(y[interior], wrong[interior] / D, label="plane displaced")
ax[1].plot(
    y[interior],
    observed_D[interior] / D,
    alpha=0.7,
    label="small profile ripple",
)
ax[1].set(xlabel="Normalized fraction", ylabel="Inferred D / true D")
ax[1].legend(fontsize=8)
fig.tight_layout()
fig.savefig(
    BASE / "assets/figures/ch12-inversion.svg", metadata={"Date": None}
)
out = {
    "synthetic": True,
    "D_true_m2_s": D,
    "time_s": time,
    "diffusion_scale_m": float(scale),
    "plane_m": float(plane),
    "max_relative_error_5_to_95_percent": float(relative_error),
    "plane_displacement_m": float(shift),
    "interior_values": records,
    "ripple_relative_D_range": [
        float(observed_D[interior].min() / D),
        float(observed_D[interior].max() / D),
    ],
}
text = json.dumps(out, indent=2)
(BASE / "code/ch12-output.json").write_text(text + "\n", encoding="utf-8")
print(text)
