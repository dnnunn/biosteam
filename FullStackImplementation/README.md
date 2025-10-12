# Full-Stack Implementation — Index

This folder collects plans/specs for the UI + API redesign of BioSTEAM.

- GUI Redesign Plan (blocks): `FullStackImplementation/GUI_Redesign_Plan.md`
- Icon Builder & Graphics: `FullStackImplementation/Graphics Designer — Implementation Spec (Icon Builder for Unit Ops).md`
- Initial bootstrap plan: `FullStackImplementation/bio_steam_app_main_branch_bootstrap_pr_specs_file_stubs.md`

Quick start for API trials (no UI yet):
- Activate env and set PYTHONPATH:
  - `conda activate /Users/davidnunn/Desktop/Apps/Biosteam/.conda-envs/biosteam310`
  - `export PYTHONPATH=.:pkgs/biosteam/src:pkgs/thermosteam/src`
- Run API: `uvicorn app.api.main:app --reload --port 8000`
- Browse buffers: `http://localhost:8000/docs` → try `/buffers`, `/buffers/{id}/recommendations`
- Run front end flow: `POST /runs/front_end` with overrides stub from recommendations

Next step: scaffold `/app/ui` (Next.js + React Flow) per the redesign plan.

