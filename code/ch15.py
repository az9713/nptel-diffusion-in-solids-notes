"""One-phase planar Stefan problem; not a DICTRA reproduction."""

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq
from scipy.special import erf

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch15"
BASE = Path(__file__).resolve().parents[1]
D, time = 1e-14, 1e5
rows = []
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
times = np.linspace(0, 4e5, 401)
for beta in [0.1, 1.0]:
    lam = brentq(
        lambda v: v * np.exp(v * v) * erf(v) - beta / np.sqrt(np.pi), 1e-9, 2
    )
    exact = 2 * lam * np.sqrt(D * time)
    approximate = np.sqrt(2 * D * beta * time)
    assert (
        abs(lam * np.exp(lam * lam) * erf(lam) - beta / np.sqrt(np.pi)) < 1e-10
    )
    ax[0].plot(
        times / 1e5,
        2 * lam * np.sqrt(D * times) * 1e6,
        label=f"exact, beta={beta:g}",
    )
    ax[0].plot(
        times / 1e5,
        np.sqrt(2 * D * beta * times) * 1e6,
        "--",
        label=f"quasi-steady, beta={beta:g}",
    )
    u = np.linspace(0, 1, 201)
    profile = 1 - erf(lam * u) / erf(lam)
    ax[1].plot(u, profile, label=f"beta={beta:g}")
    rows.append(
        {
            "beta": beta,
            "lambda": float(lam),
            "exact_position_m": float(exact),
            "quasi_steady_position_m": float(approximate),
            "quasi_steady_relative_error": float(approximate / exact - 1),
        }
    )
ax[0].set(xlabel="Time / 100000 s", ylabel="Interface position (micrometers)")
ax[1].set(
    xlabel="Position / current layer thickness",
    ylabel="(c - c_interface) / (c_surface - c_interface)",
)
for panel in ax:
    panel.legend(fontsize=8)
fig.tight_layout()
fig.savefig(BASE / "assets/figures/ch15-stefan.svg", metadata={"Date": None})
out = {
    "synthetic": True,
    "D_m2_s": D,
    "time_s": time,
    "cases": rows,
    "four_component_binary_count": 6,
}
text = json.dumps(out, indent=2)
(BASE / "code/ch15-output.json").write_text(text + "\n", encoding="utf-8")
print(text)
