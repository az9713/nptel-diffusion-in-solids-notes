"""Synthetic two-region grain-boundary diffusion; run from any directory."""

from pathlib import Path
import json
import numpy as np
import matplotlib

import matplotlib.pyplot as plt

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch20"
ROOT = Path(__file__).resolve().parents[1]


def solve(fast, ny=61, nz=121, end=0.03):
    dy, dz = 2 / ny, 4 / nz
    y = (np.arange(ny) + 0.5) * dy - 1
    z = (np.arange(nz) + 0.5) * dz
    diffusivity = np.ones((ny, nz))
    if fast:
        diffusivity[np.abs(y) < 0.05, :] = 20
    c = np.zeros_like(diffusivity)
    c[:, 0] = 1 / dz
    initial = float(c.sum() * dy * dz)
    fy = (
        2
        * diffusivity[:-1]
        * diffusivity[1:]
        / (diffusivity[:-1] + diffusivity[1:])
    )
    fz = (
        2
        * diffusivity[:, :-1]
        * diffusivity[:, 1:]
        / (diffusivity[:, :-1] + diffusivity[:, 1:])
    )
    n = int(np.ceil(end / (0.2 / (diffusivity.max() * (dy**-2 + dz**-2)))))
    dt = end / n
    for _ in range(n):
        transfer_y = dt * fy * (c[1:] - c[:-1]) / dy**2
        transfer_z = dt * fz * (c[:, 1:] - c[:, :-1]) / dz**2
        change = np.zeros_like(c)
        change[:-1] += transfer_y
        change[1:] -= transfer_y
        change[:, :-1] += transfer_z
        change[:, 1:] -= transfer_z
        c += change
    mass = float(c.sum() * dy * dz)
    assert abs(mass - initial) < 1e-11 and c.min() >= -1e-14
    mean = c.mean(axis=0)
    return (
        z,
        mean,
        {
            "mass_initial": initial,
            "mass_final": mass,
            "minimum": float(c.min()),
            "depth_second_moment": float(np.sum(mean * z * z) * dz),
            "steps": n,
            "strip_fraction": float(np.mean(diffusivity[:, 0] > 1)),
        },
    )


def main():
    z, ordinary, a = solve(False)
    _, boundary, b = solve(True)
    # SI example: synthetic parameters, not a material measurement.
    D, db, delta, sb, t, grain = 1e-18, 1e-12, 5e-10, 10.0, 3600.0, 1e-5
    length = np.sqrt(D * t)
    P = sb * delta * db
    out = {
        "status": "synthetic teaching construction",
        "bulk": a,
        "boundary": b,
        "regime_example": {
            "sqrt_Dt_m": float(length),
            "alpha": float(sb * delta / (2 * length)),
            "beta": float(P / (2 * D * length)),
            "P_m3_per_s": P,
            "length_over_grain": float(length / grain),
        },
        "same_P_pairs": [
            {"s_delta_m": 5e-9, "D_b_m2_s": 1e-12},
            {"s_delta_m": 5e-8, "D_b_m2_s": 1e-13},
        ],
    }
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.semilogy(z, ordinary, label="Uniform D = 1")
    ax.semilogy(z, boundary, label="Central strip D = 20")
    ax.set(
        xlabel="Dimensionless depth z",
        ylabel="Section mean concentration",
        ylim=(1e-12, 10),
        xlim=(0, 3),
    )
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    target = ROOT / "assets" / "ch20-profiles.svg"
    target.parent.mkdir(exist_ok=True)
    fig.savefig(target, metadata={"Date": None})
    plt.close(fig)
    (ROOT / "code" / "ch20-output.json").write_text(
        json.dumps(out, indent=2) + "\n"
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
