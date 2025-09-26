# BioSTEAM Setup Guide for Dairy Process Design

## Current Installation Status

We encountered version compatibility issues between Python 3.9 and the latest BioSTEAM/ThermoSTEAM packages. The main issues are:

1. **scipy compatibility**: flexsolve library expects `scipy.differentiate.jacobian` which doesn't exist in scipy 1.13.1
2. **API changes**: Newer BioSTEAM versions have API changes not compatible with older dependency versions

## Recommended Installation Approach

### Option 1: Create New Python 3.10+ Environment (Recommended)

```bash
# Using conda (recommended)
conda create -n biosteam python=3.10
conda activate biosteam
pip install biosteam

# Or using pyenv + venv
pyenv install 3.10.12
pyenv local 3.10.12
python -m venv biosteam_env
source biosteam_env/bin/activate  # On macOS/Linux
pip install biosteam
```

### Option 2: Use Docker Container

```dockerfile
FROM python:3.10-slim

RUN pip install biosteam pandas matplotlib jupyter

WORKDIR /workspace
```

## Dairy Process Design Framework

Once BioSTEAM is properly installed, here's how you can structure your dairy process:

### Basic Dairy Process Components

1. **Raw Material Handling**
   - Milk reception and storage
   - Quality testing streams
   - Temperature conditioning

2. **Processing Units**
   - Pasteurization (heat treatment)
   - Separation (cream/skim)
   - Homogenization
   - Fermentation (for yogurt/cheese)
   - Concentration/drying

3. **Utilities**
   - Steam generation
   - Cooling water systems
   - CIP (Clean-in-place) systems
   - Refrigeration

4. **Economic Analysis**
   - Capital costs (equipment)
   - Operating costs (utilities, labor)
   - Product pricing and revenue

### Next Steps

1. Set up proper Python 3.10+ environment
2. Install BioSTEAM successfully
3. Define your specific dairy process requirements
4. Start with basic milk processing flowsheet
5. Add economic analysis
6. Perform sensitivity analysis

## Process Design Questions

To help you get started, consider:

1. **What type of dairy products?** (fluid milk, cheese, yogurt, powder)
2. **What capacity?** (L/day or kg/day)
3. **What level of automation?**
4. **What utilities are available?** (steam, electricity, cooling water)
5. **What economic parameters matter?** (ROI, payback period, NPV)

Would you like me to help you design a specific dairy process once you have BioSTEAM properly installed?