"""Nuclear lifetime and synthetic jump-scattering linewidth checks."""

import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from scipy.constants import c, electron_volt, hbar
from scipy.special import voigt_profile

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch19"
BASE = Path(__file__).resolve().parents[1]
half_life = 98e-9
mean_life = half_life / np.log(2)
natural_fwhm_ev = hbar / mean_life / electron_volt
resonance_ev = 14412.95
doppler_fwhm = c * natural_fwhm_ev / resonance_ev
ell, residence = 0.3e-9, 1e-9
diffusion = ell**2 / (6 * residence)
u = np.linspace(0, 12, 601)
rate_iso = 1 - np.sinc(u / np.pi)
rate_100 = (1 - np.cos(u)) / 3
rate_111 = 1 - np.cos(u / np.sqrt(3))
small = 0.01
small_ratio = (1 - np.sinc(small / np.pi)) / (small**2 / 6)
assert abs(small_ratio - 1) < 1e-5
q = 1e9
angular_hwhm = diffusion * q * q
energy_hwhm_ev = hbar * angular_hwhm / electron_volt
freq = np.linspace(-2, 2, 1001)
fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
ax[0].plot(u, rate_iso, label="isotropic fixed length")
ax[0].plot(u, rate_100, label="cubic, q along [100]")
ax[0].plot(u, rate_111, label="cubic, q along [111]")
ax[0].plot(u, u * u / 6, "--", label="continuum low-q limit")
ax[0].set(
    xlabel="Wavevector magnitude × jump length",
    ylabel="Angular HWHM × residence time",
    ylim=(0, 2.2),
)
ax[0].legend(fontsize=7)
ax[1].plot(
    freq, 0.1 / (np.pi * (freq * freq + 0.1**2)), label="sample Lorentzian"
)
ax[1].plot(
    freq,
    0.3 / (np.pi * (freq * freq + 0.3**2)),
    label="convolved with Lorentzian resolution",
)
ax[1].plot(
    freq,
    voigt_profile(freq, 0.2, 0.1),
    label="convolved with Gaussian resolution",
)
ax[1].set(
    xlabel="Angular frequency / reference rate",
    ylabel="Normalized spectral density",
)
ax[1].legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, 1.25))
fig.tight_layout()
fig.savefig(
    BASE / "assets/figures/ch19-scattering.svg", metadata={"Date": None}
)
out = {
    "Fe57_evaluated_half_life_s": half_life,
    "Fe57_mean_life_s": float(mean_life),
    "natural_single_line_FWHM_eV": float(natural_fwhm_ev),
    "natural_single_line_Doppler_FWHM_m_s": float(doppler_fwhm),
    "synthetic_jump_length_m": ell,
    "synthetic_residence_time_s": residence,
    "synthetic_D_m2_s": diffusion,
    "test_q_per_m": q,
    "continuum_angular_HWHM_per_s": angular_hwhm,
    "continuum_energy_HWHM_eV": float(energy_hwhm_ev),
    "small_q_jump_to_continuum_ratio": float(small_ratio),
}
text = json.dumps(out, indent=2)
(BASE / "code/ch19-output.json").write_text(text + "\n", encoding="utf-8")
print(text)
