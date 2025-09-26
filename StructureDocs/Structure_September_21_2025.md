# Project Structure - September 21, 2025

> **Doc Meta**
>
> - **Purpose:** Current project structure snapshot for BioSTEAM osteopontin migration project
> - **Scope:** Directory organization, key files, and project dependencies
> - **Owner:** @davidnunn
> - **Last-verified:** 2025-09-21

## Project Root Structure

```
/Users/davidnunn/Desktop/Apps/Biosteam/
├── .claude/                           # Claude Code configuration
│   ├── agents/                        # Specialized subagents
│   │   └── biosteam-migrator.md      # Excel-to-BioSTEAM migration expert
│   └── commands/
│       └── wrapup.md                 # Session wrap-up procedures
├── pkgs/
│   ├── biosteam/src/biosteam/        # Primary BioSTEAM source tree (src layout)
│   └── thermosteam/src/thermosteam/  # Thermosteam submodule (src layout)
├── migration/                        # Excel-to-BioSTEAM bring-up modules
├── SessionSummaries/                 # Session documentation
├── NextSteps/                        # Future task planning
├── StructureDocs/                    # Project structure snapshots
├── Archive/                          # Legacy analyses (see ARCHIVE_INDEX.md)
├── How2STEAM/ (optional)             # Workshop/tutorial material
├── Bioindustrial-Park/ (optional)    # Vendored reference biorefineries
├── CLAUDE.md                         # BioSTEAM development guidance
├── OSTEOPONTIN_MIGRATION_FINDINGS.md # Comprehensive analysis results
└── excel_parameter_extractor.py      # Latest parameter extraction script
```

## Core BioSTEAM Installation

```
pkgs/biosteam/src/biosteam/           # Main BioSTEAM package (src layout)
├── process_tools/                    # Process modeling utilities
│   ├── system_factory.py           # SystemFactory patterns (key for modularity)
│   ├── process_model.py             # Process modeling framework
│   └── [other process tools]
├── units/                           # Unit operation library
├── evaluation/                      # Economic analysis tools
├── facilities/                      # Utility facilities
└── [extensive BioSTEAM codebase]
```

## External Dependencies

```
pkgs/thermosteam/src/thermosteam/    # Thermodynamic engine (submodule)
├── thermosteam/                    # Core thermo calculations
└── tests/                          # Thermodynamic tests

Bioindustrial-Park/                 # Example biorefineries
├── biorefineries/
│   ├── BDO/                       # 1,4-Butanediol (reusable fermentation patterns)
│   ├── HP/                        # 3-Hydroxypropionic acid
│   ├── TAL/                       # Triacetic acid lactone
│   └── [other biorefinery examples]
└── [biorefinery implementations]
```

## Key Files and Organization

### Project Documentation
| File | Purpose | Status |
|------|---------|--------|
| **OSTEOPONTIN_MIGRATION_FINDINGS.md** | Comprehensive analysis and specifications | Complete |
| **CLAUDE.md** | BioSTEAM development commands and guidance | Current |
| **Session_summary_September_21_2025.md** | Session accomplishments and decisions | Complete |
| **NextSteps_September_21_2025.md** | Priority tasks and implementation roadmap | Complete |

### Implementation Templates
| File | Purpose | Status |
|------|---------|--------|
| **dairy_process_template.py** | Basic BioSTEAM process structure | Template ready |
| **biosteam_wrapper.py** | Python 3.9 compatibility wrapper | Experimental |

### Specialized Tools
| Component | Purpose | Status |
|-----------|---------|--------|
| **biosteam-migrator subagent** | Excel-to-BioSTEAM migration expert | Active |
| **SystemFactory patterns** | Modular process design framework | Available |
| **BDO biorefinery examples** | Fermentation system patterns | Reusable |

## Working Environments and Dependencies

### Primary Environment
- **Location**: `conda activate biosteam` (Python 3.10.18)
- **BioSTEAM**: Version 2.52.12 (fully functional)
- **ThermoSTEAM**: Version 0.52.5 (compatible)
- **Key Dependencies**: scipy 1.15.3, matplotlib 3.10.6, graphviz (system)

### Development Status
- **Installation**: Complete and verified ✅
- **Compatibility**: Python 3.10+ required for full functionality
- **Testing**: Basic import and execution verified
- **Documentation**: CLAUDE.md provides development guidance

### External Data Sources
- **Excel Model**: `/Users/davidnunn/Desktop/Apps/BetterDairy/TEAM/Revised Model_15052025v29.xlsx`
- **Parameter Count**: 289 parameters extracted across 8 worksheets
- **Current Baseline**: $1,210.91/kg osteopontin at 10,000 kg/year

## Notable Structural Changes

### Since Project Initialization
- **Added**: SessionSummaries, NextSteps, StructureDocs directories
- **Added**: OSTEOPONTIN_MIGRATION_FINDINGS.md (comprehensive analysis)
- **Added**: biosteam-migrator specialized subagent
- **Status**: Requirements and analysis phase complete

### Project Organization Evolution
- **Phase 0**: Initial BioSTEAM setup and environment configuration
- **Phase 1**: Requirements gathering and Excel model analysis
- **Current**: Ready for implementation with enhanced baseline
- **Next**: Core migration and validation phase

## Major Folders and Purpose

### Core Development (`/Biosteam/`)
- **Root**: Project coordination and high-level documentation
- **SessionSummaries**: Session-by-session progress tracking
- **NextSteps**: Forward-looking task planning and dependencies
- **StructureDocs**: Project organization snapshots

### BioSTEAM Framework (`pkgs/biosteam/src/biosteam/`)
- **process_tools**: Modular process design patterns (key for osteopontin project)
- **units**: Individual unit operation implementations
- **evaluation**: Economic analysis and optimization tools
- **facilities**: Utility and infrastructure modeling

### Reference Implementations (`Bioindustrial-Park/`, optional)
- **BDO**: Fermentation-based production (closest to osteopontin process)
- **HP, TAL**: Alternative biochemical production examples
- **Reusability**: SystemFactory patterns applicable to precision fermentation

## Dependencies Summary

### Required for Implementation
- **Python 3.10+**: Full BioSTEAM compatibility
- **BioSTEAM 2.52.12**: Core modeling framework
- **SystemFactory**: Modular process design patterns
- **biosteam-migrator**: Specialized Excel migration expertise

### Optional Enhancements
- **Graphviz**: Process flow diagram generation (installed)
- **Jupyter**: Interactive development and documentation
- **Monte Carlo tools**: Uncertainty analysis capabilities

### External Integration
- **Excel Model**: Source of parameters and validation baseline
- **CMO Pricing Data**: Industry benchmarks for cost modeling
- **Alternative Technology Data**: Unit operation parameter libraries

---

**Project Status**: Comprehensive foundation established. Ready for Phase 1 implementation with clear structure, complete analysis, and specialized tools activated.
