"""Synthetic temperature/pressure fits and activation-volume checks."""

import json
from pathlib import Path

import numpy as np
from scipy.constants import R, Avogadro, Boltzmann
import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch09"
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def run():
    # Exact synthetic inputs, distinct from the source tutorial below.
    temperature = np.array([800.0, 900.0, 1000.0, 1100.0, 1200.0])
    prefactor, enthalpy = 2e-6, 150e3
    diffusivity = prefactor * np.exp(-enthalpy / (R * temperature))
    slope, intercept = np.polyfit(1 / temperature, np.log(diffusivity), 1)
    recovered_h = -R * slope
    recovered_a = np.exp(intercept)
    assert np.isclose(recovered_h, enthalpy)
    assert np.isclose(recovered_a, prefactor)
    path_prefactors = np.array([1e-8, 1e-5])
    path_h = np.array([100e3, 180e3])
    selected_t = np.array([800.0, 1000.0, 1600.0])
    contributions = path_prefactors * np.exp(
        -path_h / (R * selected_t[:, None])
    )
    weights = contributions / contributions.sum(axis=1)[:, None]
    apparent_h = weights @ path_h
    crossover = (path_h[1] - path_h[0]) / (
        R * np.log(path_prefactors[1] / path_prefactors[0])
    )
    pressure = np.array([0.0, 0.25, 0.5, 0.75, 1.0]) * 1e9
    pressure_t, molar_volume = 1000.0, 4e-6
    pressure_ratio = np.exp(-pressure * molar_volume / (R * pressure_t))
    pressure_slope = np.polyfit(pressure, np.log(pressure_ratio), 1)[0]
    recovered_volume = -R * pressure_t * pressure_slope
    assert np.isclose(recovered_volume / molar_volume, 1)
    per_atom_volume = molar_volume / Avogadro
    assert np.isclose(
        pressure_ratio[-1],
        np.exp(-pressure[-1] * per_atom_volume / (Boltzmann * pressure_t)),
    )
    radius = 0.128e-9
    atomic_volume = 4 * np.sqrt(2) * radius**3
    sphere_volume = 4 * np.pi * radius**3 / 3
    assert np.isclose(sphere_volume / atomic_volume, np.pi / (3 * np.sqrt(2)))
    q_melt, melting_t, melting_slope = 200e3, 1500.0, 30e-9
    melting_volume = q_melt / melting_t * melting_slope
    grid_t = np.linspace(700, 1800, 301)
    paths = path_prefactors * np.exp(-path_h / (R * grid_t[:, None]))
    fig, ax = plt.subplots(figsize=(7, 3.8), layout="constrained")
    ax.plot(1000 / grid_t, np.log(paths.sum(axis=1)), label="Sum of two paths")
    for index in range(2):
        ax.plot(
            1000 / grid_t,
            np.log(paths[:, index]),
            linestyle="--",
            label=f"Path {index + 1}",
        )
    ax.set(
        xlabel="1000 / temperature (1/K)",
        ylabel="ln[D / (1 m²/s)]",
        title="Synthetic competing Arrhenius contributions",
    )
    ax.grid(alpha=0.25)
    ax.legend()
    fig.savefig(ROOT / "assets/ch09-arrhenius.svg", metadata={"Date": None})
    plt.close(fig)
    # Transcribed from the inspected L20 1690 s slide, not measured by us.
    source_celsius = np.array([700, 800, 900, 1000, 1100], dtype=float)
    source_t = source_celsius + 273.15
    source_d = np.array([7e-20, 5.50e-19, 3.40e-18, 4.20e-17, 2.10e-16])
    source_fit, source_cov = np.polyfit(
        1 / source_t, np.log(source_d), 1, cov=True
    )
    source_residual = np.log(source_d) - np.polyval(source_fit, 1 / source_t)
    source_r2 = 1 - np.sum(source_residual**2) / np.sum(
        (np.log(source_d) - np.mean(np.log(source_d))) ** 2
    )
    source_p_units = np.array([0.5, 500, 2500, 4000, 5500])
    source_p = source_p_units * 1e5
    source_pd = np.array([5e-17, 4.60e-17, 3e-17, 2.50e-17, 2e-17])
    source_pfit, source_pcov = np.polyfit(
        source_p, np.log(source_pd), 1, cov=True
    )
    source_p_residual = np.log(source_pd) - np.polyval(source_pfit, source_p)
    source_pr2 = 1 - np.sum(source_p_residual**2) / np.sum(
        (np.log(source_pd) - np.mean(np.log(source_pd))) ** 2
    )
    source_volume_molar = -R * 800 * source_pfit[0]
    source_volume_atom = -Boltzmann * 800 * source_pfit[0]
    return {
        "scope": "Synthetic examples plus labeled source tutorial data",
        "source_tutorial": {
            "source_frame": "L20 at 1690 s, inspected 720p",
            "temperatures_C": source_celsius.tolist(),
            "D_temperature_m2_per_s": source_d.tolist(),
            "Q_kJ_per_mol": -R * source_fit[0] / 1000,
            "D0_m2_per_s": np.exp(source_fit[1]),
            "Q_fit_standard_error_kJ_per_mol": R
            * np.sqrt(source_cov[0, 0])
            / 1000,
            "temperature_log_residuals": source_residual.tolist(),
            "temperature_fit_R_squared": source_r2,
            "pressure_temperature_K": 800,
            "pressures_in_1e5_Pa": source_p_units.tolist(),
            "D_pressure_m2_per_s": source_pd.tolist(),
            "pressure_slope_per_1e5_Pa": source_pfit[0] * 1e5,
            "pressure_fit_R_squared": source_pr2,
            "activation_volume_m3_per_mol": source_volume_molar,
            "activation_volume_m3_per_particle": source_volume_atom,
            "volume_fit_standard_error_m3_per_mol": R
            * 800
            * np.sqrt(source_pcov[0, 0]),
            "pressure_log_residuals": source_p_residual.tolist(),
        },
        "R_J_per_mol_K": R,
        "single_path": {
            "temperatures_K": temperature.tolist(),
            "D_m2_per_s": diffusivity.tolist(),
            "recovered_prefactor_m2_per_s": recovered_a,
            "recovered_enthalpy_J_per_mol": recovered_h,
        },
        "two_path": {
            "temperatures_K": selected_t.tolist(),
            "weights": weights.tolist(),
            "apparent_enthalpy_kJ_per_mol": (apparent_h / 1000).tolist(),
            "crossover_temperature_K": crossover,
        },
        "pressure": {
            "temperature_K": pressure_t,
            "pressures_GPa": (pressure / 1e9).tolist(),
            "D_over_D_at_zero_P": pressure_ratio.tolist(),
            "recovered_volume_m3_per_mol": recovered_volume,
            "per_atom_volume_m3": per_atom_volume,
            "slope_per_GPa": pressure_slope * 1e9,
        },
        "fcc_volume_example": {
            "radius_nm": radius / 1e-9,
            "lattice_volume_per_atom_nm3": atomic_volume / 1e-27,
            "hard_sphere_volume_nm3": sphere_volume / 1e-27,
            "ratio": sphere_volume / atomic_volume,
        },
        "melting_curve_volume_m3_per_mol": melting_volume,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
