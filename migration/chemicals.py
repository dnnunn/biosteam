"""Custom chemical definitions for the osteopontin migration."""

from __future__ import annotations

from thermosteam import Chemical
from thermosteam.thermosteam._biorefinery_chemicals import register

__all__ = [
    "register_osteopontin",
    "register_chitosan",
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


@register('Chitosan', 'Chi')
def register_chitosan(ID: str, **kwargs) -> Chemical:
    """Return a Chemical object representing chitosan."""

    return Chemical(
        ID,
        formula='C6.2H11.2NO4.1',
        phase='s',
        MW=165.361,
        rho=1345.0,
        HHV=(17.618e3, 'J/g'),
        LHV=(16.129e3, 'J/g'),
        Cp=0.90,
        Hf=(-42.051e3, 'J/g'),
        **kwargs,
    )
