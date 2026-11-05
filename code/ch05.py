"""Synthetic crystal-geometry and defect-count checks; writes one owned SVG."""

import json
from pathlib import Path
import numpy as np
import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "ch05"
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def run():
    fcc_packing = np.pi / (3 * np.sqrt(2))
    bcc_packing = np.pi * np.sqrt(3) / 8
    octahedral_ratio = np.sqrt(2) - 1
    tetrahedral_ratio = np.sqrt(1.5) - 1
    a = 0.36e-9
    primitive = a / 2 * np.array([[0, 1, 1], [1, 0, 1], [1, 1, 0]])
    assert np.isclose(abs(np.linalg.det(primitive)) / a**3, 0.25)
    radius = a / (2 * np.sqrt(2))
    burgers = a / np.sqrt(2)
    angles = np.array([2.0, 10.0])
    spacing = 0.25 / (2 * np.sin(np.deg2rad(angles) / 2))
    small_angle = 0.25 / np.deg2rad(angles)
    pair_product = 1e-8
    vacancy_fraction = np.sqrt(3 * pair_product)
    interstitial_fraction = vacancy_fraction / 3
    assert np.isclose(vacancy_fraction * interstitial_fraction, pair_product)
    # A B2 triple combination removes one A and one B to a reservoir.
    n = 100
    atoms_a, atoms_b = n - 2 + 1, n - 1
    assert atoms_a == atoms_b == 99
    theta = np.linspace(0.25, 15, 301)
    distance = 0.25 / (2 * np.sin(np.deg2rad(theta) / 2))
    fig, ax = plt.subplots(figsize=(7, 3.8), layout="constrained")
    ax.plot(
        theta, distance, color="#176e8c", label="Exact edge-array geometry"
    )
    ax.set(
        xlabel="Misorientation (degrees)", ylabel="Dislocation spacing (nm)"
    )
    ax.set_title("Synthetic tilt boundary: Burgers magnitude 0.25 nm")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.savefig(
        ROOT / "assets/ch05-boundary-spacing.svg", metadata={"Date": None}
    )
    plt.close(fig)
    return dict(
        synthetic=True,
        fcc_packing=fcc_packing,
        bcc_packing=bcc_packing,
        fcc_octahedral_radius_ratio=octahedral_ratio,
        fcc_tetrahedral_radius_ratio=tetrahedral_ratio,
        fcc_radius_nm=radius / 1e-9,
        fcc_burgers_nm=burgers / 1e-9,
        fcc_primitive_to_conventional_volume=0.25,
        angles_degrees=angles.tolist(),
        spacing_nm=spacing.tolist(),
        small_angle_spacing_nm=small_angle.tolist(),
        frenkel_site_fractions=[vacancy_fraction, interstitial_fraction],
        triple_defect_atom_counts=[atoms_a, atoms_b],
    )


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
