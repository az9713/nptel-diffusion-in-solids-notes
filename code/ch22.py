"""Ordered-jump and shared-boundary geometry teaching calculations."""

from pathlib import Path
import json
import numpy as np
import matplotlib

import matplotlib.pyplot as plt

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch22"
ROOT = Path(__file__).resolve().parents[1]


def main():
    # Two-dimensional alternating square: vacancy at0, three A/B atoms.
    sites = ["A", "B", "A", "B"]
    state = [None, "B", "A", "B"]
    vacancy = 0
    history = []
    for target in [1, 2, 3, 0, 1, 2]:
        state[vacancy], state[target] = state[target], None
        vacancy = target
        history.append(
            {
                "vacancy_site": vacancy,
                "antisites": sum(
                    v is not None and v != s for v, s in zip(state, sites)
                ),
            }
        )
    assert history[-1]["antisites"] == 0
    delta = 0.5e-9
    d = np.geomspace(5e-9, 1e-6, 150)
    g = 1 - (1 - delta / d) ** 3
    D, Db = 1e-20, 1e-14
    parallel = (1 - g) * D + g * Db
    series = 1 / ((1 - g) / D + g / Db)
    examples = {}
    for size in [10e-9, 100e-9]:
        fraction = 1 - (1 - delta / size) ** 3
        examples[str(size)] = {
            "boundary_fraction": fraction,
            "thin_limit": 3 * delta / size,
            "parallel_m2_s": (1 - fraction) * D + fraction * Db,
            "series_m2_s": 1 / ((1 - fraction) / D + fraction / Db),
        }
    out = {
        "status": "synthetic ideal structures and transport coefficients",
        "six_jump_history": history,
        "grain_examples": examples,
        "golden_ratio": float((1 + np.sqrt(5)) / 2),
        "fibonacci_ratio_34_over_21": 34 / 21,
        "L12_A_neighbors": {"A": 8, "B": 4},
        "L12_B_neighbors": {"A": 12},
    }
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.loglog(d * 1e9, parallel, label="Parallel")
    ax.loglog(d * 1e9, series, label="Series")
    ax.set(
        xlabel="Cubic grain repeat length (nm)",
        ylabel="Effective diffusivity (m² s⁻¹)",
    )
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(ROOT / "assets/ch22-geometry.svg", metadata={"Date": None})
    plt.close(fig)
    (ROOT / "code/ch22-output.json").write_text(
        json.dumps(out, indent=2) + "\n"
    )
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
