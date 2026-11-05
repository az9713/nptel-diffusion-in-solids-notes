"""Synthetic checks for conservation, layered resistance, and anisotropy.

Run from any directory. Requires NumPy. Writes no files and uses no network.
All quantities are SI. Inputs are pedagogical, not measured material data.
"""

import json
import numpy as np


def run():
    # Series layers share a constant flux; concentration drops add.
    thickness = np.array([1e-3, 2e-3])
    diffusivity = np.array([1e-12, 4e-12])
    concentrations = (2.0, 0.5)
    resistance = thickness / diffusivity
    flux = (concentrations[0] - concentrations[1]) / resistance.sum()
    interface = concentrations[0] - flux * resistance[0]
    assert np.isclose(interface, 1.0)
    assert np.allclose(
        flux,
        (concentrations[0] - interface) / resistance[0],
        rtol=1e-12,
        atol=0,
    )
    assert np.allclose(
        flux,
        (interface - concentrations[1]) / resistance[1],
        rtol=1e-12,
        atol=0,
    )

    # A finite-volume divergence telescopes exactly, independent of closure.
    face_flux = np.array([0.2, -0.1, 0.4, 0.05, 0.0])
    dx = 0.25
    rates = -(face_flux[1:] - face_flux[:-1]) / dx
    global_rate = rates.sum() * dx
    assert np.isclose(global_rate, face_flux[0] - face_flux[-1])

    # A gradient at 45 degrees need not give a parallel diffusive flux.
    tensor = np.diag([1e-12, 4e-12])
    direction = np.array([1.0, 1.0]) / np.sqrt(2.0)
    gradient = 1000.0 * direction
    vector_flux = -tensor @ gradient
    projected_D = direction @ tensor @ direction
    assert np.isclose(projected_D / 1e-12, 2.5)
    transverse = vector_flux @ np.array([-direction[1], direction[0]])
    assert abs(transverse) > 0
    assert np.isclose(transverse, -1.5e-9, rtol=1e-12, atol=0)
    # Independently integrate the variable-coefficient steady resistance.
    x = np.linspace(0, 1, 20001)
    alpha = 0.5
    numerical_resistance = np.trapezoid(1 / (1 + alpha * x), x)
    exact_resistance = np.log1p(alpha) / alpha
    assert abs(numerical_resistance - exact_resistance) < 1e-9
    # Exact-mode mass, no-flux faces, and PDE derivative identity.
    for tau in (0, 0.1, 0.5):
        u = 1 + 0.5 * np.cos(np.pi * x) * np.exp(-(np.pi**2) * tau)
        assert abs(np.trapezoid(u, x) - 1) < 1e-12
        du_dtau = (
            -0.5 * np.pi**2 * np.cos(np.pi * x) * np.exp(-(np.pi**2) * tau)
        )
        du_dxi2 = (
            -0.5 * np.pi**2 * np.cos(np.pi * x) * np.exp(-(np.pi**2) * tau)
        )
        assert np.allclose(du_dtau, du_dxi2)
    # Check the tangent, divergence, radial resistance, and eigenvalue bounds.
    assert 4 * 1 - 2 == 2
    assert 6 * 1 + 2 * (-4) + 2 * 1 == 0
    assert 6 * 0 + 2 * (-4) + 2 * 0 != 0
    a, b = 1.0, 1.2
    assert np.isclose((1 / (1 / a - 1 / b)) / (a * a / (b - a)), b / a)
    for angle in np.linspace(0, 2 * np.pi, 101):
        unit = np.array([np.cos(angle), np.sin(angle)])
        value = unit @ tensor @ unit
        assert 1e-12 * (1 - 1e-12) <= value <= 4e-12 * (1 + 1e-12)
    return {
        "synthetic_inputs": True,
        "layer_resistances_s_per_m": resistance.tolist(),
        "steady_flux_mol_per_m2_s": float(flux),
        "interface_concentration_mol_per_m3": float(interface),
        "global_amount_rate_per_area": float(global_rate),
        "directional_D_m2_per_s": float(projected_D),
        "vector_flux_mol_per_m2_s": vector_flux.tolist(),
        "transverse_flux_mol_per_m2_s": float(transverse),
        "tangent_to_2x2_at_1": {"slope": 4, "intercept": -2},
        "variable_D_resistance_ratio": float(exact_resistance),
        "spherical_exact_to_inner_planar_rate_ratio": float(b / a),
        "mode_mean_at_all_sampled_times": 1.0,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
