# 2025-10-07 — Full Stack Implementation Kickoff Plan

## Immediate Priorities
- Bootstrap the `/app` monorepo skeleton described in `FullStackImplementation/bio_steam_app_main_branch_bootstrap_pr_specs_file_stubs.md` (API, CLI, UI, Docker, CI).
- Wire the BioSTEAM engine placeholders:
  - Register real unit factories in `app/api/engine/registry.py`.
  - Build actual systems/flowsheets in `app/api/engine/builder.py` and return runnable `System` objects.
  - Implement TEA/KPI extraction in `app/api/engine/runner.py` and update the golden test accordingly.
- Seed the Next.js pages with live API calls and basic KPI displays so we can demo Run → Results end-to-end.

## NLS Integration Tasks
- Drop the latest BD module YAMLs into `app/units/specs/` and run `nls_adapter_kit/tools/validate_specs.py` to confirm synonym coverage.
- Expose the dynamic ontology router in the API (`app.include_router(nls.router)`) and add regression tests around add/replace/remove/set/connect commands.
- Extend the parser/editor for remaining verbs (`add before`, `duplicate`, `run sobol`) and connect the Sobol handler to `uncertainty.py` once SALib is wired.

## Tooling & Ops
- Finalize Dockerfiles + `docker-compose.yml` so API/UI launch with a single `docker compose up`.
- Expand `.github/workflows/ci.yml` to run linting, tests, and UI build; ensure Makefile targets (`dev`, `api`, `ui`, `test`) function on CI.
- Document the developer workflow (install, run, test, NLS smoke test) in a top-level README before merging.

## Stretch Goals (If Time Allows)
- Add an uncertainty demo (Sobol results + placeholder charts) to the UI.
- Prototype the flowsheet editor (React Flow canvas) that consumes the same `Scenario` model the NLS layer edits.
- Explore persistence: capture runs to a simple store (filesystem or Postgres) with metadata for quick recall.

Keep this plan handy for the next session; we can work down the Immediate Priorities, then fan out into NLS enhancements and tooling once the scaffold is merged.
