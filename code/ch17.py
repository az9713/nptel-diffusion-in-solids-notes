"""Mechanical and electrical probe checks with explicit conventions."""

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch17"
BASE = Path(__file__).resolve().parents[1]
R = 8.31446261815324
a, tau_s = 0.287e-9, 1e-6
snoek_d = a * a / (36 * tau_s)
d0, activation = 2.3e-4, 280e3
temperatures = np.array([300, 400]) + 273.15
diffusivities = d0 * np.exp(-activation / (R * temperatures))
thickness = np.array([0.5e-3, 1e-3])
gorsky_times = thickness**2 / (np.pi**2 * diffusivities)
ratio = gorsky_times[0] / gorsky_times[1]
e0, einf = 100.0, 120.0
y = np.logspace(-2, 2, 1001)
eprime = einf - (einf - e0) / (1 + y * y)
edouble = (einf - e0) * y / (1 + y * y)
loss = edouble / eprime
expected = np.sqrt(e0 / einf)
assert abs(y[np.argmax(loss)] / expected - 1) < 0.01
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
ax[0].semilogx(y, edouble / (einf - e0), label="normalized modulus loss")
ax[0].semilogx(y, loss, label="loss tangent")
ax[0].set(
    xlabel="Angular frequency × stress-relaxation time",
    ylabel="Dimensionless response",
)
ax[0].legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, 1.22))
theta = np.linspace(0, np.pi, 301)
resistance, capacitance = 1000.0, 1e-6
omega = np.logspace(-1, 7, 501)
z = resistance / (1 + 1j * omega * resistance * capacitance)
ax[1].plot(z.real, -z.imag)
ax[1].set(xlabel="Real impedance (ohm)", ylabel="Negative imaginary (ohm)")
ax[1].set_aspect("equal", adjustable="box")
fig.tight_layout()
fig.savefig(
    BASE / "assets/figures/ch17-relaxation.svg", metadata={"Date": None}
)
out = {
    "source_Snoek_D_m2_s": snoek_d,
    "Gorsky_host_mobility_proxy_assumption": True,
    "temperatures_K": temperatures.tolist(),
    "proxy_diffusivities_m2_s": diffusivities.tolist(),
    "proxy_Gorsky_times_s_Phi_equals_1": gorsky_times.tolist(),
    "time_ratio_sample1_over_sample2": float(ratio),
    "synthetic_modulus_loss_peak_omega_tau": 1.0,
    "synthetic_tan_delta_peak_omega_tau": float(expected),
    "synthetic_RC_peak_angular_frequency_rad_s": 1
    / (resistance * capacitance),
    "synthetic_RC_peak_negative_imaginary_ohm": resistance / 2,
}
text = json.dumps(out, indent=2)
(BASE / "code/ch17-output.json").write_text(text + "\n", encoding="utf-8")
print(text)
