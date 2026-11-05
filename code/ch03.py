"""Analytic diffusion profiles, inverse checks, and original figure data.

All material parameters are synthetic unless a result explicitly names a
caption-stated tutorial input. Empirical validation is separate.
Run with --figures to create original SVG plots in figures/.
"""

import argparse
import json
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from scipy.special import erf, erfc, erfinv


def run():
    D, time, dose = 2e-12, 10000.0, 3e-5

    def gaussian(x):
        return (
            dose
            / np.sqrt(4 * np.pi * D * time)
            * np.exp(-x * x / (4 * D * time))
        )

    scale = np.sqrt(D * time)
    mass = quad(lambda z: gaussian(z * scale) * scale, -12, 12, epsabs=1e-14)[
        0
    ]
    moment = quad(
        lambda z: (z * scale) ** 2 * gaussian(z * scale) * scale / dose,
        -12,
        12,
        epsabs=1e-18,
    )[0]
    assert np.isclose(mass, dose, rtol=1e-10, atol=0)
    assert np.isclose(moment, 2 * D * time, rtol=1e-10, atol=0)
    x = scale
    left, right = 0.8, 0.2
    couple = right + (left - right) / 2 * erfc(x / (2 * scale))
    assert np.isclose(
        couple, (left + right) / 2 - (left - right) / 2 * erf(x / (2 * scale))
    )
    uptake = 2 * (left - right) * np.sqrt(D * time / np.pi)
    numerical_uptake = quad(
        lambda z: (left - right) * erfc(z / 2) * scale, 0, 16
    )[0]
    assert np.isclose(uptake, numerical_uptake, rtol=1e-10, atol=0)

    # Independent integral checks: flux uptake and half-source moments.
    def flux_profile(z):
        return 2 / np.sqrt(np.pi) * np.exp(-z * z / 4) - z * erfc(z / 2)

    assert abs(quad(flux_profile, 0, 16)[0] - 1) < 1e-10
    half_mean = quad(lambda z: z * np.exp(-z * z / 4) / np.sqrt(np.pi), 0, 16)[
        0
    ]
    half_second = quad(
        lambda z: z * z * np.exp(-z * z / 4) / np.sqrt(np.pi), 0, 16
    )[0]
    assert np.isclose(half_mean, 2 / np.sqrt(np.pi))
    assert np.isclose(half_second - half_mean**2, 2 * (1 - 2 / np.pi))
    a = 0.4

    def top_hat(z):
        return 0.5 * (erf((z + a) / 2) - erf((z - a) / 2))

    assert abs(quad(top_hat, -16, 16)[0] - 2 * a) < 1e-10
    # Tutorial inverse-erf calculation retains the mass-percent convention.
    initial, surface, target, depth, D_carbon = 0.25, 1.2, 0.8, 0.5e-3, 1.6e-11
    deficit = (surface - target) / (surface - initial)
    z = erfinv(deficit)
    treatment_seconds = depth**2 / (4 * D_carbon * z * z)
    assert np.isclose(
        initial
        + (surface - initial)
        * erfc(depth / (2 * np.sqrt(D_carbon * treatment_seconds))),
        target,
    )
    # Couple tutorial: doubling depth at fixed composition requires 4t.
    z_couple = erfinv(0.5)
    D_couple = (20e-3) ** 2 / (4 * (40 * 3600) * z_couple * z_couple)
    approximate_D = (20e-3) ** 2 / (4 * (40 * 3600) * 0.5**2)
    # Natural log and base10 slopes need distinct conversion factors.
    positions = np.linspace(0, 4 * scale, 31)
    concentrations = np.array([gaussian(x) for x in positions])
    slope = np.polyfit(positions**2, np.log(concentrations), 1)[0]
    recovered_D = -1 / (4 * time * slope)
    assert np.isclose(recovered_D, D, rtol=1e-12, atol=0)
    return dict(
        synthetic_profile_parameters=dict(D=D, t=time, dose=dose),
        integrated_dose=mass,
        second_moment=moment,
        synthetic_couple_concentration_at_sqrt_Dt=float(couple),
        maintained_surface_excess_uptake=uptake,
        half_source_mean_in_sqrt_Dt_units=half_mean,
        half_source_centered_variance_in_Dt_units=half_second - half_mean**2,
        constant_flux_integral_check=1.0,
        finite_initial_layer_amount_check=2 * a,
        recovered_D_from_log_slope=float(recovered_D),
        tutorial_carburizing_hours=float(treatment_seconds / 3600),
        tutorial_carburizing_erf_argument=float(z),
        tutorial_couple_exact_D=float(D_couple),
        tutorial_couple_approximate_D=float(approximate_D),
        erf_at_0_5=float(erf(0.5)),
        erf_at_0_8=float(erf(0.8)),
    )


def figures():
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcParams["svg.hashsalt"] = "ch03"
    import matplotlib.pyplot as plt

    root = Path(__file__).resolve().parents[1]
    target = root / "figures"
    target.mkdir(exist_ok=True)
    plt.style.use("dark_background")
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6), constrained_layout=True)
    xx = np.linspace(-4, 4, 501)
    for tau, color in ((0.25, "#e3c88c"), (1, "#87d3c5"), (4, "#aaa0df")):
        axes[0].plot(
            xx,
            np.exp(-(xx**2) / (4 * tau)) / np.sqrt(4 * np.pi * tau),
            color=color,
            label=f"τ={tau:g}",
        )
        axes[1].plot(xx, 0.5 * erfc(xx / (2 * np.sqrt(tau))), color=color)
        positive = xx[xx >= 0]
        axes[2].plot(
            positive, erfc(positive / (2 * np.sqrt(tau))), color=color
        )
    for axis, title in zip(
        axes,
        (
            "Finite plane dose",
            "Infinite diffusion couple",
            "Maintained surface",
        ),
    ):
        axis.set_title(title)
        axis.set_xlabel("Dimensionless position")
        axis.set_ylabel("Normalized concentration")
        axis.grid(alpha=0.2)
    axes[0].legend()
    fig.savefig(
        target / "ch03-profile-families.svg",
        metadata={
            "Creator": "Original analytic teaching construction",
            "Date": None,
        },
    )
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--figures", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(), indent=2))
    if args.figures:
        figures()
