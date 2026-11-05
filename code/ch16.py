"""Fit the visually verified L40 tutorial and synthetic broadening model."""

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch16"
BASE = Path(__file__).resolve().parents[1]
depth_um = np.array([0.2, 0.5, 1, 1.5, 2, 2.5, 3, 4, 5])
activity = np.array([1e6, 5e5, 2e5, 1.2e5, 6e4, 1e4, 5.8e3, 5.1e2, 1e2])
time = 3 * 24 * 3600
xx, yy = depth_um**2, np.log(activity)
slope, intercept = np.polyfit(xx, yy, 1)
predicted = intercept + slope * xx
residual = yy - predicted
r_squared = 1 - np.sum(residual**2) / np.sum((yy - yy.mean()) ** 2)
coefficient = -1 / (4 * time * slope * 1e12)
trim_slope, _ = np.polyfit(xx[2:], yy[2:], 1)
trim_coefficient = -1 / (4 * time * trim_slope * 1e12)
log10_slope = np.polyfit(xx, np.log10(activity), 1)[0]
assert np.isclose(slope, log10_slope * np.log(10), rtol=1e-12)
d_synthetic, t_synthetic = 1e-18, 2e5
initial_sigma, instrument_sigma = 0.1e-6, 0.2e-6
variance = (
    initial_sigma**2 + 2 * d_synthetic * t_synthetic + instrument_sigma**2
)
naive = variance / (2 * t_synthetic)
assert np.isclose(
    (variance - initial_sigma**2 - instrument_sigma**2) / (2 * t_synthetic),
    d_synthetic,
    rtol=1e-12,
    atol=0,
)
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
ax[0].scatter(xx, yy, label="source tutorial values")
ax[0].plot(xx, predicted, label="unweighted natural-log fit")
ax[0].set(
    xlabel="Depth squared (micrometers squared)",
    ylabel="ln(activity / 1 Bq per mg)",
)
ax[0].legend(fontsize=8)
ax[1].axhline(0, color="gray", linewidth=1)
ax[1].scatter(xx, residual)
ax[1].set(xlabel="Depth squared (micrometers squared)", ylabel="Log residual")
fig.tight_layout()
fig.savefig(
    BASE / "assets/figures/ch16-tracer-fit.svg", metadata={"Date": None}
)
out = {
    "source_table_frame_verified": True,
    "depth_um": depth_um.tolist(),
    "specific_activity_Bq_mg": activity.tolist(),
    "anneal_time_s": time,
    "slope_per_um2": float(slope),
    "intercept": float(intercept),
    "r_squared": float(r_squared),
    "D_nominal_m2_s": float(coefficient),
    "D_excluding_first_two_m2_s": float(trim_coefficient),
    "log_residuals": residual.tolist(),
    "synthetic_broadening": {
        "D_true_m2_s": d_synthetic,
        "time_s": t_synthetic,
        "observed_sigma_m": float(np.sqrt(variance)),
        "naive_D_m2_s": naive,
        "half_gaussian_variance_factor": 1 - 2 / np.pi,
    },
}
text = json.dumps(out, indent=2)
(BASE / "code/ch16-output.json").write_text(text + "\n", encoding="utf-8")
print(text)
