# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BioSTEAM (The Biorefinery Simulation and Techno-Economic Analysis Modules) is a Python package for the design, simulation, techno-economic analysis, and life cycle assessment of biorefineries. It's built on top of the ThermoSTEAM thermodynamic engine and integrates with the chemicals and thermo libraries.

## Development Commands

### Testing
```bash
# Run all tests (excludes slow tests by default)
pytest . -v --cov-report html --cov=biosteam --cov-report term-missing -m "not slow"

# Run tests with notebook validation
pytest . --doctest-modules --nbval --current-env

# Run all tests including slow ones
pytest . -v --cov-report html --cov=biosteam --cov-report term-missing

# Run a specific test file
pytest tests/test_specific_file.py -v
```

### Installation and Setup
```bash
# Install in development mode with all dependencies
pip install -e .

# Install development dependencies
pip install -r requirements_test.txt

# Install documentation dependencies
pip install -r requirements.txt
```

### Documentation
```bash
# Build documentation (from docs/ directory)
cd docs && make html

# Clean documentation build
cd docs && make clean
```

## Architecture Overview

### Core Components

- **`biosteam/_system.py`**: Core system simulation engine, handles process flowsheets and convergence
- **`biosteam/_unit.py`**: Base Unit class for all process equipment
- **`biosteam/_flowsheet.py`**: Manages flowsheet organization and unit connectivity
- **`biosteam/_tea.py`**: Techno-economic analysis calculations
- **`biosteam/units/`**: Library of specific unit operations (reactors, separators, heat exchangers, etc.)
- **`biosteam/facilities/`**: Utility facilities (boilers, cooling towers, etc.)
- **`biosteam/evaluation/`**: Tools for uncertainty analysis and optimization
- **`biosteam/process_tools/`**: High-level process modeling utilities

### Key Dependencies

- **ThermoSTEAM**: Thermodynamic property calculations and stream management
- **chemicals/thermo**: Chemical property databases and estimation methods
- **graphviz**: Process flow diagram generation
- **numba**: JIT compilation for performance-critical calculations
- **flexsolve**: Equation solving algorithms

### Data Flow

1. **Chemical Definition**: Uses ThermoSTEAM's Chemical and Chemicals classes
2. **Stream Objects**: Material and energy balances via Stream and MultiStream
3. **Unit Operations**: Process equipment that transforms streams
4. **System Assembly**: Units connected into flowsheets for simulation
5. **TEA Integration**: Economic analysis of the complete process

## Testing Structure

- Tests are organized in the `tests/` directory
- Uses pytest with doctest integration
- Notebook validation via nbval
- Coverage reporting with pytest-cov
- Slow tests are marked and excluded by default
- Numba JIT compilation is configurable via conftest.py

## Installation Status

### Current Environment Issues
- **Python 3.9 Compatibility**: The current Python 3.9 environment has compatibility issues with recent BioSTEAM versions
- **scipy.differentiate Error**: flexsolve library expects `scipy.differentiate.jacobian` which doesn't exist in scipy 1.13.1
- **Dependency Conflicts**: Version mismatches between ThermoSTEAM, flexsolve, and other dependencies

### Successful Installation Steps
```bash
# Install with dependency bypass (partially successful)
pip install --user --ignore-installed biosteam

# Install system Graphviz for diagrams
brew install graphviz  # macOS
# sudo apt-get install graphviz  # Ubuntu
```

### Recommended Solution
Create a Python 3.10+ environment for full compatibility:
```bash
conda create -n biosteam python=3.10
conda activate biosteam
pip install biosteam
```

## Important Notes

- **Graphviz**: System dependency installed and configured for process diagrams
- **JIT Compilation**: Uses extensive numba compilation for performance
- **Stream Utilities**: Globally configurable pricing and utilities
- **Process Templates**: dairy_process_template.py provides structure for dairy process design
- **Jupyter Integration**: Key feature for interactive process development