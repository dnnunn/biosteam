"""Custom chemical definitions for the osteopontin migration."""

from __future__ import annotations

from typing import Iterable

from thermosteam import Chemical, Chemicals

try:  # ThermoSTEAM installed as a flat package
    from thermosteam._biorefinery_chemicals import register
except ModuleNotFoundError:  # pragma: no cover - legacy nested layout
    from thermosteam.thermosteam._biorefinery_chemicals import register  # type: ignore

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
        search_db=False,
        formula='C1494H2320N401O705S4P35',
        phase='s',
        MW=38391.01,
        rho=1112.6,  # Approximate protein density (kg/m3)
        Hf=(-5.34e3, 'J/g'),
        Cp=1.5,
        S0=(0.45, 'J/g/K'),
        **kwargs,
    )


@register('Chitosan', 'Chi')
def register_chitosan(ID: str, **kwargs) -> Chemical:
    """Return a Chemical object representing chitosan."""

    return Chemical(
        ID,
        search_db=False,
        formula='C6.2H11.2NO4.1',
        phase='s',
        MW=165.361,
        rho=1345.0,
        HHV=(17.618e3, 'J/g'),
        LHV=(16.129e3, 'J/g'),
        Cp=0.92,
        S0=(0.35, 'J/g/K'),
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
        'Cp': 1.46,
        'S0': (0.45, 'J/g/K'),
    },
    'Peptone': {
        'formula': 'CH1.8O0.5N0.3',
        'phase': 's',
        'MW': 120.0,
        'rho': 1250.0,
        'Hf': (-3.5e3, 'J/g'),
        'Cp': 1.46,
        'S0': (0.45, 'J/g/K'),
    },
    'CornSteepLiquor': {
        'formula': 'CH1.9O0.7N0.2',
        'phase': 'l',
        'MW': 150.0,
        'rho': 1210.0,
        'Hf': (-2.0e3, 'J/g'),
        'Cp': 3.6,
        'S0': (1.20, 'J/g/K'),
    },
    'YeastNitrogenBase': {
        'formula': 'CH1.5O0.6N0.4',
        'phase': 's',
        'MW': 110.0,
        'rho': 1250.0,
        'Hf': (-4.0e3, 'J/g'),
        'Cp': 1.60,
        'S0': (0.50, 'J/g/K'),
    },
    'SodiumHexametaphosphate': {
        'formula': 'Na6O18P6',
        'phase': 's',
        'MW': 611.77,
        'rho': 2120.0,
        'Hf': (-1.2e3, 'J/g'),
        'Cp': 0.90,
        'S0': (0.32, 'J/g/K'),
    },
    'Antifoam': {
        'formula': 'CH2',
        'phase': 'l',
        'MW': 100.0,
        'rho': 970.0,
        'Hf': (-2.5e3, 'J/g'),
        'Cp': 2.10,
        'S0': (0.70, 'J/g/K'),
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


FORCE_SOLID_STATE = {
    'Monosodium phosphate',
    'Disodium phosphate',
    'Trisodium phosphate',
    'Sodium acetate',
    'Sodium citrate',
}


def _make_component(name: str) -> Chemical:
    if name == 'Chitosan':
        return register_chitosan(name)
    if name == 'Osteopontin':
        return register_osteopontin(name)
    data = LUMP_COMPONENTS.get(name)
    if data is not None:
        return Chemical(name, search_db=False, **data)
    return Chemical(name)


def create_migration_chemicals(additional: Iterable[str] | None = None) -> Chemicals:
    """Return a ThermoSTEAM Chemicals package with project components."""

    components = list(DEFAULT_COMPONENTS)
    if additional:
        for item in additional:
            if item not in components:
                components.append(item)

    chemicals = Chemicals([_make_component(name) for name in components])
    set_synonym = getattr(chemicals, 'set_synonym', None)
    if callable(set_synonym):
        set_synonym('OPN', 'Osteopontin')
        set_synonym('Chi', 'Chitosan')
    for chemical in chemicals:
        if chemical.ID in FORCE_SOLID_STATE:
            chemical.at_state('s')
            chemical._locked_state = 's'  # type: ignore[attr-defined]
        missing = chemical.get_missing_properties(chemical.get_key_property_names())
        if missing:
            chemical.default(missing)
    return chemicals
