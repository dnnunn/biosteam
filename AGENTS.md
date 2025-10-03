# Repository Guidelines

## Project Structure & Module Organization
BioSTEAM's core logic now lives under `pkgs/biosteam/src/biosteam/`, organized by domains such as `units/`, `facilities/`, `wastewater/`, and computational helpers under `utils/` and `process_tools/`. Thermodynamic primitives are provided by the thermosteam submodule in `pkgs/thermosteam/src/thermosteam/`; keep cross-module updates coordinated. End-user tutorials, examples, and diagrams sit in `docs/`, while optional training material remains in `How2STEAM/`. Reusable flowsheets from Bioindustrial-Park remain vendored under `Bioindustrial-Park/` as reference content. Tests mirror the layout under `tests/` with diagram fixtures housed in `tests/Diagram Sources/`.

## Build, Test, and Development Commands
Create a development environment with `pip install -e .[dev]` (or `pip install -r requirements_test.txt` when Conda-free). Run the quick suite via `pytest -m "not slow"`; include `--cov=biosteam --cov-report term-missing` before pushing. Notebook-style regression checks run automatically through `pytest --nbval`; limit notebook changes or re-execute cells first. Use `python -m biosteam` only for manual sanity checks; CLI output should stay deterministic.

## Coding Style & Naming Conventions
Follow PEP 8 with 4-space indents, 88-character soft wraps, and descriptive snake_case identifiers for public APIs. Class names stay CamelCase and match unit or facility abbreviations already used in the module (e.g., `MixTank`, `HXNetwork`). Preserve rich docstrings that feed the Sphinx docs, including parameter units where relevant. Prefer explicit keyword arguments and avoid implicit state mutations across flowsheets.

## Testing Guidelines
Target pytest (unit + doctest) parity with existing modules; any new unit should ship with scenario coverage under `tests/test_<domain>.py`. Mark longer simulations with `@pytest.mark.slow` and keep them opt-in. Notebook edits must clear `--nbval` without relaxing tolerances; regenerate cached diagrams in `tests/Diagram Sources/` when graph structures change. Coverage must not drop; introduce regression cases when fixing bugs to document prior failures.

## Commit & Pull Request Guidelines
Commits should be concise, present-tense summaries (e.g., `fix pressure bug`, `add turbine TEA hook`) and reference issues with `#<id>` when applicable. Before opening a PR, ensure the checklist in `.github/PULL_REQUEST_TEMPLATE/pull_request_template.md` is satisfied: clear summary, updated docs, passing tests, and maintained coverage. Link notebooks or screenshots when UI diagrams shift, and call out any API-breaking change in both the PR body and module docstrings.

## Documentation & Support
Run `make html` inside `docs/` (after installing Sphinx extras) to validate documentation before release. Questions on modelling patterns should be captured in `SessionSummaries/` or escalated through GitHub Discussions rather than ad-hoc chats. Keep `SETUP_GUIDE.md` aligned with any environment assumptions you introduce.

## Agent Startup Checklist
> These commands must be run manually by the user before any Python tooling that
> depends on BioSTEAM/ThermoSTEAM. Agents should **not** execute them directly.

- Activate the shared Conda env before running tools:
  `conda activate /Users/davidnunn/Desktop/Apps/Biosteam/.conda-envs/biosteam310`
- Prime `PYTHONPATH` so BioSTEAM/ThermoSTEAM modules import correctly:
  `export PYTHONPATH=".:pkgs/biosteam/src:pkgs/thermosteam/src"`
- Refresh the regression snapshot whenever any front-end model or defaults change:
  `python3 -m migration.scripts.export_baseline_metrics`
  (run from the repo root after the environment steps above, then commit the regenerated `tests/opn/baseline_metrics.json`.)
