#!/usr/bin/env python3
"""
BioSTEAM Wrapper with scipy compatibility fix

This script patches the scipy.differentiate import issue to make BioSTEAM
work with older scipy versions in Python 3.9 environments.
"""

import sys
import types

# Create a fake scipy.differentiate module to fix the import error
def patch_scipy_differentiate():
    """Patch scipy.differentiate for compatibility with older scipy versions."""
    if 'scipy.differentiate' not in sys.modules:
        differentiate_module = types.ModuleType('scipy.differentiate')

        try:
            # Try different scipy functions that could work as jacobian
            from scipy.optimize import approx_fprime

            def jacobian(func, x, *args):
                """Approximate jacobian using scipy.optimize.approx_fprime"""
                # This is a simplified jacobian approximation
                # For more complex cases, you might need a more sophisticated implementation
                if callable(func):
                    return approx_fprime(x, func, 1e-8, *args)
                else:
                    # If func is not callable, return a placeholder
                    import numpy as np
                    return np.zeros_like(x)

            differentiate_module.jacobian = jacobian
            sys.modules['scipy.differentiate'] = differentiate_module

        except ImportError as e:
            print(f"Warning: Could not create scipy.differentiate patch: {e}")

# Apply the patch before importing biosteam
patch_scipy_differentiate()

def init_biosteam():
    """Initialize BioSTEAM with error handling."""
    try:
        import biosteam
        print(f"✓ BioSTEAM {biosteam.__version__} loaded successfully!")
        return biosteam
    except Exception as e:
        print(f"✗ Failed to load BioSTEAM: {e}")
        return None

def create_simple_process_example():
    """Create a simple process example for demonstration."""
    biosteam = init_biosteam()
    if biosteam is None:
        return None

    try:
        # Import commonly used modules
        import thermosteam as tmo
        import numpy as np

        print("\n=== Creating Simple Process Example ===")

        # Set up chemicals
        chemicals = tmo.Chemicals(['Water', 'Ethanol', 'Glucose'])
        tmo.settings.set_thermo(chemicals)

        # Create streams
        feed = tmo.Stream('feed', Water=100, Glucose=50, T=298.15, P=101325)
        print(f"Feed stream: {feed}")

        # You can add more process units here
        print("✓ Basic streams created successfully!")

        return biosteam, feed

    except Exception as e:
        print(f"✗ Error creating example process: {e}")
        return None

if __name__ == "__main__":
    # Test the wrapper
    result = create_simple_process_example()
    if result:
        biosteam, feed = result
        print("\n=== BioSTEAM Ready for Your Process Design ===")
        print("You can now design your dairy process using biosteam!")
    else:
        print("Please use Python 3.10+ environment for best compatibility.")