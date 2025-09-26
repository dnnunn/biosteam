"""Custom chemical definitions for the osteopontin migration."""

from __future__ import annotations

from typing import Iterable

from thermosteam import Chemical, Chemicals
from thermosteam.thermosteam._biorefinery_chemicals import register

__all__ = [
    "register_osteopontin",
    "register_chitosan",
    "create_migration_chemicals",
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


LUMP_COMPONENTS = {
    'YeastExtract': {
        'formula': 'CH1.7O0.45N0.25',
        'phase': 's',
        'MW': 130.0,
        'rho': 1250.0,
        'Hf': (-3.0e3, 'J/g'),
    },
    'Peptone': {
        'formula': 'CH1.8O0.5N0.3',
        'phase': 's',
        'MW': 120.0,
        'rho': 1250.0,
        'Hf': (-3.5e3, 'J/g'),
    },
    'CornSteepLiquor': {
        'formula': 'CH1.9O0.7N0.2',
        'phase': 'l',
        'MW': 150.0,
        'rho': 1210.0,
        'Hf': (-2.0e3, 'J/g'),
    },
    'YeastNitrogenBase': {
        'formula': 'CH1.5O0.6N0.4',
        'phase': 's',
        'MW': 110.0,
        'rho': 1250.0,
        'Hf': (-4.0e3, 'J/g'),
    },
    'SodiumHexametaphosphate': {
        'formula': 'Na6O18P6',
        'phase': 's',
        'MW': 611.77,
        'rho': 2120.0,
        'Hf': (-1.2e3, 'J/g'),
    },
    'Antifoam': {
        'formula': 'CH2',
        'phase': 'l',
        'MW': 100.0,
        'rho': 970.0,
        'Hf': (-2.5e3, 'J/g'),
    },
}


DEFAULT_COMPONENTS = [
    'Water',
    'O2',
    'N2',
    'CO2',
    'Glucose',
    'Yeast',
    'YeastExtract',
    'Peptone',
    'Acetic acid',
    'Lactic acid',
    'Citric acid',
    'Hydrochloric acid',
    'Sodium acetate',
    'Sodium citrate',
    'Phosphoric acid',
    'Monosodium phosphate',
    'Disodium phosphate',
    'Trisodium phosphate',
    'CornSteepLiquor',
    'YeastNitrogenBase',
    'SodiumHexametaphosphate',
    'Antifoam',
    'Ethanol',
    'Peracetic acid',
    'EDTA',
    'Chitosan',
    'Osteopontin',
]


def _make_component(name: str) -> Chemical:
    if name == 'Chitosan':
        return register_chitosan(name)
    if name == 'Osteopontin':
        return register_osteopontin(name)
    data = LUMP_COMPONENTS.get(name)
    if data is not None:
        return Chemical(name, db=None, **data)
    return Chemical(name)


def create_migration_chemicals(additional: Iterable[str] | None = None) -> Chemicals:
    """Return a ThermoSTEAM Chemicals package with project components."""

    components = list(DEFAULT_COMPONENTS)
    if additional:
        for item in additional:
            if item not in components:
                components.append(item)

    chemicals = Chemicals([_make_component(name) for name in components])
    chemicals.set_synonym('OPN', 'Osteopontin')
    chemicals.set_synonym('Chi', 'Chitosan')
    return chemicals
