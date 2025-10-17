"""
Minimal setup.py for vendored ThermoSTEAM.

This allows the vendored package to be installed in editable mode
while maintaining compatibility with both local development and CI.
"""
from setuptools import setup, find_packages

setup(
    name="thermosteam-vendored",
    version="0.1.0",
    description="Vendored ThermoSTEAM for BioSTEAM BD project",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.22,<1.27",
        "pandas>=2.2",
        "chemicals",
        "thermo",
        "fluids",
        "scipy",
        "pyyaml",
    ],
    # Prevent conflicts with PyPI thermosteam
    provides=["thermosteam"],
)
