import pytest
import sys
import warnings

# Configure a default ThermoSTEAM chemical package for tests
try:
    from migration.thermo_setup import set_migration_thermo
    set_migration_thermo()
    print("✓ migration.thermo_setup loaded successfully", file=sys.stderr)
except Exception as e:
    warnings.warn(f"Could not load migration.thermo_setup: {e}")
    print(f"⚠ migration.thermo_setup failed: {e}", file=sys.stderr)

# Apply compat shims early (guard None flows reaching ThermoSTEAM internals)
try:
    from app.api.engine import compat_shims  # noqa: F401
    print("✓ compat_shims loaded successfully", file=sys.stderr)
except Exception as e:
    warnings.warn(f"Could not load compat_shims: {e}")
    print(f"⚠ compat_shims failed: {e}", file=sys.stderr)
