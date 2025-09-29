# Recurring Environment & Stream Issue Log

Running list of host-side issues we keep hitting in the BioSTEAM migration workflow. Add a dated note whenever a recurring error resurfaces or a new workaround is required. When an item is closed out permanently, move it to the “Resolved” section with the date and reference commit.

## How to Update This Log
- Append entries chronologically under “Active Issues”. Each entry should capture:
  - **Symptom**: copy/paste the key error text (trim log noise).
  - **Context**: environment path, command, workbook, or branch involved.
  - **Workaround / Fix**: exact commands or code changes applied.
  - **Action Owner / Follow-up**: who is tracking the upstream Codex/runtime fix, if any.
- When a fix lands in source control, note the commit hash and relocate the issue to “Resolved”.
- Keep commands copy-pasteable; prefer absolute paths where ambiguity slows triage.

## Active Issues

### 2024-XX-XX – Module import failure when running compare script directly
- **Symptom**: `ModuleNotFoundError: No module named 'migration'` when running `python migration/scripts/compare_front_end.py ...` from the repo root.
- **Context**: Environment `/Users/davidnunn/Desktop/Apps/Biosteam/.conda-envs/biosteam310`.
- **Workaround / Fix**:
  ```bash
  python -m migration.scripts.compare_front_end \
    --mode baseline \
    --workbook /Users/davidnunn/Desktop/Apps/Biosteam/BaselineModel.xlsx
  ```
  (or install the project editable: `pip install -e .[dev]`).
- **Follow-up**: Keep using `python -m` until Codex paths are restored; no upstream ETA yet.

### 2024-XX-XX – `ChemicalMassFlowIndexer` has no `get`
- **Symptom**: `AttributeError: <DiscStackCentrifuge ...> 'ChemicalMassFlowIndexer' object has no attribute 'get'` when the new cell-removal units run.
- **Context**: Baseline comparison in `biosteam310` env after introducing disc-stack/depth units.
- **Workaround / Fix**: Use index access helpers (see `migration/cell_removal.py` helper `_get_component_mass`) instead of calling `.imass.get(...)`.
- **Follow-up**: Refactor any new unit code to use the helper; audit legacy modules if the error resurfaces elsewhere.

## Resolved Issues
- _None yet_
