"""Accumulated diffusion time and a frame-verified glass tutorial."""

from pathlib import Path
import json
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch26"
ROOT = Path(__file__).resolve().parents[1]


def main():
    D0, end, amplitude = 1e-18, 3600.0, 0.8
    t = np.linspace(0, end, 501)
    tau_A = D0 * t
    tau_B = D0 * ((1 + amplitude) * t - amplitude * t * t / end)
    x = np.linspace(-10 * np.sqrt(D0 * end), 10 * np.sqrt(D0 * end), 2001)

    def profile(tau):
        return np.exp(-x * x / (4 * tau)) / np.sqrt(4 * np.pi * tau)

    pa, pb = profile(tau_A[-1]), profile(tau_B[-1])
    assert np.max(np.abs(pa - pb)) == 0
    norm = float(np.trapezoid(pa, x))
    moment = float(np.trapezoid(pa * x * x, x))
    assert abs(norm - 1) < 1e-10
    assert abs(moment / (2 * D0 * end) - 1) < 1e-8
    h = 48.0
    mean = (300 - h / 6 - h * h / 90) * 1e-15
    instant = (300 - h / 3 - h * h / 30) * 1e-15
    out = {
        "status": "synthetic histories; separate source tutorial calculation",
        "history_example": {
            "D0_m2_s": D0,
            "end_s": end,
            "amplitude": amplitude,
            "tau_final_m2": float(tau_A[-1]),
            "tau_A_half_time_m2": float(D0 * end / 2),
            "tau_B_half_time_m2": float(D0 * end * (0.5 + amplitude / 4)),
            "final_profile_max_difference": float(np.max(abs(pa - pb))),
            "normalization": norm,
            "variance_m2": moment,
            "rms_width_m": float(np.sqrt(moment)),
        },
        "lecture59_polynomial": {
            "time_h": h,
            "mean_D_m2_h": mean,
            "instant_D_m2_h": instant,
            "mean_D_m2_s": mean / 3600,
            "positive_time_limit_h": 90.0,
        },
    }
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    axes[0].plot(t / 3600, tau_A, label="Constant D")
    axes[0].plot(t / 3600, tau_B, label="Decreasing D")
    axes[0].set(xlabel="Time (h)", ylabel="Accumulated diffusion time (m²)")
    axes[0].legend()
    axes[1].plot(x * 1e9, pa * 1e-9, label="Both final profiles")
    axes[1].set(xlabel="Position (nm)", ylabel="Normalized density (nm⁻¹)")
    for ax in axes:
        ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(ROOT / "assets/ch26-histories.svg", metadata={"Date": None})
    plt.close(fig)
    (ROOT / "code/ch26-output.json").write_text(
        json.dumps(out, indent=2) + "\n"
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
