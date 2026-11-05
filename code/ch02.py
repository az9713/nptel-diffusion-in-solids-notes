"""Exact symbolic and independent quadrature checks for transform examples."""

import json
import numpy as np
import sympy as sp
from scipy.integrate import quad


def run():
    t, s = sp.symbols("t s", positive=True)
    examples = [
        (sp.exp(2 * t) / 3 + 2 * sp.exp(-t) / 3, -1, -2, sp.Integer(0), 1, 0),
        (
            2 * sp.cos(t) + sp.Rational(5, 3) * sp.sin(t) - sp.sin(2 * t) / 3,
            0,
            1,
            sp.sin(2 * t),
            2,
            1,
        ),
        (
            sp.exp(3 * t / 2)
            * (
                sp.cos(sp.sqrt(7) * t / 2)
                + sp.sqrt(7) * sp.sin(sp.sqrt(7) * t / 2)
            ),
            -3,
            4,
            sp.Integer(0),
            1,
            5,
        ),
    ]
    checks = []
    for y, a, b, forcing, initial, initial_derivative in examples:
        residual = sp.simplify(
            sp.diff(y, t, 2) + a * sp.diff(y, t) + b * y - forcing
        )
        assert residual == 0
        assert sp.simplify(y.subs(t, 0)) == initial
        assert sp.simplify(sp.diff(y, t).subs(t, 0)) == initial_derivative
        checks.append(
            dict(
                residual=str(residual),
                initial_value=initial,
                initial_derivative=initial_derivative,
            )
        )
    rational = (8 * s**2 - 4 * s + 12) / (s * (s**2 + 4))
    recovered = 3 + 5 * sp.cos(2 * t) - 2 * sp.sin(2 * t)
    assert (
        sp.simplify(
            sp.laplace_transform(recovered, t, s, noconds=True) - rational
        )
        == 0
    )
    primitive = -(t**4) * sp.cos(2 * t**4) / 8 + sp.sin(2 * t**4) / 16
    assert sp.simplify(sp.diff(primitive, t) - t**7 * sp.sin(2 * t**4)) == 0
    eta = 3.0

    def integrand(u):
        if u == 1:
            return eta
        return np.expm1(eta * np.log(u)) / np.log(u)

    integral, error = quad(integrand, 0, 1, epsabs=1e-11)
    assert abs(integral - np.log1p(eta)) < 1e-10
    # Test transform of t^n by quadrature rather than the symbolic table.
    power_checks = []
    import math

    for n in range(5):
        rate = 2.5
        observed, _ = quad(
            lambda time: time**n * np.exp(-rate * time), 0, np.inf
        )
        expected = math.factorial(n) / rate ** (n + 1)
        assert np.isclose(observed, expected, rtol=1e-10, atol=1e-12)
        power_checks.append(dict(n=n, transform_at_s_2_5=observed))
    return dict(
        synthetic_checks=True,
        ode_checks=checks,
        tutorial_inverse="3 + 5*cos(2*t) - 2*sin(2*t)",
        parameter_integral=integral,
        log_4=float(np.log(4)),
        quadrature_error_estimate=error,
        power_transforms=power_checks,
        antiderivative_verified=True,
    )


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
