import pytest

try:
    # Configure a default ThermoSTEAM chemical package for tests
    from migration.thermo_setup import set_migration_thermo
    set_migration_thermo()
except Exception:
    # Allow tests to proceed; engine/runner also applies a fallback
    pass

