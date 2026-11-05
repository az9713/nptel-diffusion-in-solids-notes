"""Darken inference: verified lecture inputs, synthetic volume and clock."""

import json
from pathlib import Path

import matplotlib

import matplotlib.pyplot as plt
import numpy as np

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch13"

BASE = Path(__file__).resolve().parents[1]
na, grad_na, velocity, inter = 0.38, 2.5e2, 4.5e-12, 3.25e-14
delta = velocity / grad_na
db = inter - (1 - na) * delta
da = db + delta
vm = 7e-6  # Synthetic molar volume, not supplied by the source problem.
ja, jb = -da * grad_na / vm, db * grad_na / vm
jav = ja + na / vm * velocity
jbv = jb + (1 - na) / vm * velocity
assert np.isclose(na * db + (1 - na) * da, inter, rtol=1e-12, atol=0)
assert abs(jav + jbv) < 1e-20
assert np.isclose(jav, -inter * grad_na / vm, rtol=1e-12, atol=0)
time = np.linspace(0, 4e5, 401)
reference_time = 1e5
marker_at_reference = 2 * velocity * reference_time
k = marker_at_reference / np.sqrt(reference_time)
fig, ax = plt.subplots(figsize=(6.5, 3.5))
ax.plot(time / 1e5, k * np.sqrt(time) * 1e6, label="lattice-following marker")
ax.axhline(0, linestyle="--", label="fixed Matano plane")
ax.set(xlabel="Time / 100000 s", ylabel="Marker position (micrometers)")
ax.legend()
fig.tight_layout()
fig.savefig(BASE / "assets/figures/ch13-marker.svg", metadata={"Date": None})
out = {
    "source_inputs_frame_verified": True,
    "D_A_m2_s": da,
    "D_B_m2_s": db,
    "D_A_minus_D_B_m2_s": delta,
    "synthetic_molar_volume_m3_mol": vm,
    "intrinsic_fluxes_mol_m2_s": [ja, jb],
    "volume_fixed_fluxes_mol_m2_s": [jav, jbv],
    "synthetic_reference_time_s": reference_time,
    "marker_displacement_at_reference_m": marker_at_reference,
    "tutorial_Dtilde_over_DB": 0.2 + 0.8 * 2,
    "doubling_time_position_ratio": float(np.sqrt(2)),
}
text = json.dumps(out, indent=2)
(BASE / "code/ch13-output.json").write_text(text + "\n", encoding="utf-8")
print(text)
