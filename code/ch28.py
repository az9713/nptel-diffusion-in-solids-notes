"""Cumulative inverse problem: identical profiles, different carriers."""

from pathlib import Path
import json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch28"
ROOT = Path(__file__).resolve().parents[1]


def main():
    fraction = np.array([1e-6, 1e-4])
    mobility = np.array([1e-10, 1e-12])
    diffusion = fraction * mobility
    assert diffusion[0] == diffusion[1]
    initial_width, resolution, time = 20e-9, 15e-9, 3600.0
    observed_var = initial_width**2 + 2 * diffusion * time + resolution**2
    coordinate = np.linspace(
        -5 * np.sqrt(observed_var[0]), 5 * np.sqrt(observed_var[0]), 1201
    )
    profiles = np.exp(
        -(coordinate[None, :] ** 2) / (2 * observed_var[:, None])
    )
    profiles /= np.sqrt(2 * np.pi * observed_var[:, None])
    times = np.array([900.0, 1800.0, 3600.0, 7200.0])
    variances = initial_width**2 + resolution**2 + 2 * diffusion[0] * times
    slope, intercept = np.polyfit(times, variances, 1)
    coefficient = 0.5
    independent_signal = coefficient * fraction
    profile_J = np.array([[1.0, 1.0]])
    augmented_J = np.array([[1.0, 1.0], [1.0, 0.0]])
    out = {
        "status": "synthetic identifiability construction; no material fit",
        "models": [
            {
                "vacancy_fraction": float(v),
                "mobility_factor_m2_s": float(b),
                "tracer_D_m2_s": float(d),
                "independent_signal": float(y),
            }
            for v, b, d, y in zip(
                fraction, mobility, diffusion, independent_signal
            )
        ],
        "at_3600s": {
            "observed_variance_m2": float(observed_var[0]),
            "observed_width_m": float(np.sqrt(observed_var[0])),
            "profile_max_difference": float(
                np.max(abs(profiles[0] - profiles[1]))
            ),
        },
        "time_series": {
            "times_s": times.tolist(),
            "variances_m2": variances.tolist(),
            "recovered_D_m2_s": float(slope / 2),
            "recovered_initial_plus_resolution_var_m2": float(intercept),
        },
        "log_parameter_ranks": {
            "profile_only": int(np.linalg.matrix_rank(profile_J)),
            "augmented": int(np.linalg.matrix_rank(augmented_J)),
        },
    }
    assert np.isclose(slope / 2, diffusion[0], rtol=1e-12, atol=0)
    assert np.max(abs(profiles[0] - profiles[1])) == 0
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].plot(coordinate * 1e6, profiles[0] * 1e-6, label="Model A")
    axes[0].plot(coordinate * 1e6, profiles[1] * 1e-6, "--", label="Model B")
    axes[0].set(
        xlabel="Depth coordinate (µm)", ylabel="Normalized density (µm⁻¹)"
    )
    axes[0].legend()
    axes[1].bar(["A", "B"], independent_signal)
    axes[1].set(ylabel="Synthetic independent vacancy signal", yscale="log")
    for ax in axes:
        ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(
        ROOT / "assets/ch28-identifiability.svg", metadata={"Date": None}
    )
    plt.close(fig)
    (ROOT / "code/ch28-output.json").write_text(
        json.dumps(out, indent=2) + "\n"
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
