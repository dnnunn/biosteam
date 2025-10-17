"""
Minimal setup.py for vendored BioSTEAM.

This allows the vendored package to be installed in editable mode
while maintaining compatibility with both local development and CI.
"""
from setuptools import setup, find_packages

setup(
    name="biosteam-vendored",
    version="0.1.0",
    description="Vendored BioSTEAM for BioSTEAM BD project",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        # Core dependencies (thermosteam is vendored separately)
        "numba<0.60",
        "llvmlite",
        "matplotlib",
        "plotly",
        "ipython",
        "SALib",
        "pydantic",
    ],
    # Prevent conflicts with PyPI biosteam
    provides=["biosteam"],
)
