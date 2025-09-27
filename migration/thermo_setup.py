"""Utilities to configure the ThermoSTEAM settings for the migration."""

from __future__ import annotations

import thermosteam as tmo

from .chemicals import create_migration_chemicals

__all__ = [
    "set_migration_thermo",
]


def set_migration_thermo(additional_components=None) -> tmo.Chemicals:
    """Create the chemicals package and set it as the global thermo."""

    chemicals = create_migration_chemicals(additional=additional_components)
    tmo.settings.set_thermo(chemicals)
    return chemicals
