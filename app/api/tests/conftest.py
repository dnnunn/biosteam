import pytest

# Configure a default ThermoSTEAM chemical package for tests
try:
    from migration.thermo_setup import set_migration_thermo
    set_migration_thermo()
except Exception:
    pass

# Apply compat shims early (guard None flows reaching ThermoSTEAM internals)
try:
    from app.api.engine import compat_shims  # noqa: F401
except Exception:
    pass
