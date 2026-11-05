"""Synthetic pulsed-gradient echo and local-correlation checks."""

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from scipy.integrate import trapezoid

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch18"
BASE = Path(__file__).resolve().parents[1]
gamma, delta, separation, diffusion = 1e8, 0.005, 0.05, 2e-12
gradient = np.linspace(0, 10, 21)
b = gamma**2 * gradient**2 * delta**2 * (separation - delta / 3)
signal = np.exp(-b * diffusion)
fitted = -np.polyfit(b, np.log(signal), 1)[0]
assert np.isclose(fitted, diffusion, rtol=1e-12, atol=0)
clock = np.linspace(0, separation + delta, 11001)
q = (
    gamma
    * 10
    * np.where(
        clock <= delta,
        clock,
        np.where(clock <= separation, delta, separation + delta - clock),
    )
)
numerical_b = trapezoid(q * q, clock)
assert abs(numerical_b / b[-1] - 1) < 1e-7
u = np.logspace(-3, 3, 601)
spectral = u / (1 + u * u)
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
ax[0].plot(b / 1e12, signal, "o-")
ax[0].set(
    xlabel="b / 10¹² s per square meter", ylabel="Normalized echo amplitude"
)
ax[1].semilogx(u, spectral)
ax[1].set(
    xlabel="Larmor angular frequency × correlation time",
    ylabel="Normalized exponential spectral density",
)
fig.tight_layout()
fig.savefig(BASE / "assets/figures/ch18-nmr.svg", metadata={"Date": None})
out = {
    "synthetic": True,
    "gamma_rad_s_T": gamma,
    "pulse_duration_s": delta,
    "pulse_leading_edge_separation_s": separation,
    "D_true_m2_s": diffusion,
    "D_fitted_m2_s": float(fitted),
    "b_at_10_T_m_s_m2": float(b[-1]),
    "echo_at_10_T_m": float(signal[-1]),
    "numerical_b_relative_error": float(numerical_b / b[-1] - 1),
    "narrow_pulse_b_relative_overestimate": delta / (3 * separation - delta),
    "equal_local_spectral_values_u_0p1_and_10": [0.1 / 1.01, 10 / 101],
}
text = json.dumps(out, indent=2)
(BASE / "code/ch18-output.json").write_text(text + "\n", encoding="utf-8")
print(text)
