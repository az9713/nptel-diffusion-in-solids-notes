"""Exact moments and seeded synthetic random-walk checks for Chapter 7."""

import json
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch07"
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def run():
    rng = np.random.default_rng(7142026)
    walkers, steps = 40000, 200
    position = np.zeros((walkers, 3), dtype=np.int64)
    sample_steps = np.array([1, 5, 10, 25, 50, 100, 200])
    measured = []
    for count in range(1, steps + 1):
        direction = rng.integers(0, 6, walkers)
        axis = direction // 2
        sign = 2 * (direction % 2) - 1
        position[np.arange(walkers), axis] += sign
        if count in sample_steps:
            measured.append(float(np.mean(np.sum(position**2, axis=1))))
    measured = np.array(measured)
    assert np.all(np.abs(measured / sample_steps - 1) < 0.025)
    gamma, length = 6e6, 0.2e-9
    diffusivity = gamma * length**2 / 6
    tutorial_msd = 6 * 2e-9 * 1
    million_rms = np.sqrt(1e6) * 0.1e-9
    n, p = 100, 0.6
    step_mean = 2 * p - 1
    biased_mean = n * step_mean
    biased_variance = n * (1 - step_mean**2)
    biased_second = biased_variance + biased_mean**2
    q = np.array([0.1, 0.5, 2.0])
    decay_ratio = 2 * (1 - np.cos(q)) / q**2
    fcc_vectors = []
    for zero_axis in range(3):
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                vector = [s1, s2]
                vector.insert(zero_axis, 0)
                fcc_vectors.append(vector)
    # Unit directions: each integer vector above has squared length two.
    unit = np.array(fcc_vectors) / np.sqrt(2)
    second_moment = unit.T @ unit
    assert np.allclose(second_moment, 4 * np.eye(3))
    fig, ax = plt.subplots(figsize=(7, 3.8), layout="constrained")
    ax.plot(sample_steps, sample_steps, label="Exact independent-walk moment")
    ax.scatter(
        sample_steps, measured, label="Seeded ensemble", color="#9a5415"
    )
    ax.set(
        xlabel="Number of successful jumps",
        ylabel="Mean squared displacement / length squared",
        title="Synthetic cubic walk: 40,000 independent tracers",
    )
    ax.grid(alpha=0.25)
    ax.legend()
    fig.savefig(ROOT / "assets/ch07-walk-moments.svg", metadata={"Date": None})
    plt.close(fig)
    return {
        "synthetic": True,
        "seed": 7142026,
        "walkers": walkers,
        "sample_steps": sample_steps.tolist(),
        "sample_msd_over_length_squared": measured.tolist(),
        "final_sample_mean_over_length": position.mean(axis=0).tolist(),
        "gamma_per_s": gamma,
        "jump_length_m": length,
        "diffusivity_m2_per_s": diffusivity,
        "tutorial_msd_m2": tutorial_msd,
        "tutorial_rms_m": np.sqrt(tutorial_msd),
        "million_step_rms_nm": million_rms / 1e-9,
        "biased_walk": {
            "steps": n,
            "positive_probability": p,
            "mean_over_length": biased_mean,
            "variance_over_length_squared": biased_variance,
            "second_moment_over_length_squared": biased_second,
        },
        "dimensionless_wave_numbers": q.tolist(),
        "exact_to_diffusive_decay_ratio": decay_ratio.tolist(),
        "fcc_direction_second_moment": second_moment.tolist(),
        "ninefold_rms_step_ratio_fixed_length": 81,
        "ninefold_rms_step_ratio_tripled_length": 9,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
