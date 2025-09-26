"""Custom chemical definitions for the osteopontin migration."""

from __future__ import annotations

from thermosteam import Chemical
from thermosteam.thermosteam._biorefinery_chemicals import register

__all__ = [
    "register_osteopontin",
]


@register('Osteopontin', 'OPN')
def register_osteopontin(ID: str, **kwargs) -> Chemical:
    """Return a Chemical object representing osteopontin."""

    return Chemical(
        ID,
        formula='C1494H2320N401O705S4P35',
        phase='s',
        MW=38391.01,
        rho=1112.6,  # Approximate protein density (kg/m3)
        Hf=(-5.34e3, 'J/g'),
        **kwargs,
    )
