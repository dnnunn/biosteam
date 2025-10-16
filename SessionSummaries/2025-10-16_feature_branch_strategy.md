# Feature Branch Strategy and Near‑Term Plan

Date: 2025‑10‑16
Branch: `feature/aex-membrane-ui`

## Why Feature Branches
- Isolate WIP UI work (AEX membrane, wiring, validations) from `main` to keep the baseline stable.
- Enable small, reviewable PRs with CI and targeted diffs.
- Allow rollback/pivot by deleting the branch without touching `main` history.
- Keep a clean commit log by squashing to a concise summary at merge time.

## Naming & Scope
- Prefix with `feature/` for new work, `fix/` for hotfixes, `chore/` for meta changes.
- This branch: `feature/aex-membrane-ui` — AEX membrane UI + topology-aware helpers and docs.

## Commit Style
- Present tense, concise messages (e.g., `add aex placement autodetect`).
- Group related changes (UI + overrides + docs) and avoid mixing unrelated refactors.
- Keep code + docs in the same PR when they belong together.

## PR Flow
1) Push branch: `git push -u origin feature/aex-membrane-ui`.
2) Open PR with summary, screenshots (UI), and checklist:
   - [ ] Build passes, no lint errors
   - [ ] Docs updated (SessionSummaries and/or README snippets)
   - [ ] Tests or at least smoke checks done locally
3) Prefer “Squash and merge” with a short, scoped title.

## Rebase / Merge Strategy
- Rebase the feature branch on `main` if it drifts significantly (keep linear history in the PR).
- Avoid force‑push to `main`. Force‑push on feature branch is OK before PR review starts.

## Guardrails
- No API‑breaking changes without updating docs and migration notes.
- Keep `pytest -m "not slow"` green; avoid touching nbval notebooks unless re‑executed.

## Near‑Term Technical Plan (Wiring & Execution)

Phase 1 — Stage Order from Topology (low effort)
- Topologically sort the mainline path from edges to produce `stage_order`.
- Export to overrides (e.g., `['cell_removal','mf_polish','sptff','aex_membrane','dsp03','sterile','spray']`).
- Backend: if `stage_order` present, honor it when running the baseline model.

Phase 2 — Validation & Guardrails (low effort)
- Validate DAG (no cycles), continuity (1‑in/1‑out mainline), and node type order (front‑end → DSP → finish).
- Inline warnings in Inspector when invalid for execution.

Phase 3 — Branches/Merges (medium)
- Treat utilities (tanks, pumps) as side branches — excluded from `stage_order` but available for sizing context.
- Later, allow explicit split/mix nodes with simple rules.

Phase 4 — Stream‑Level Flowsheet (higher effort, optional now)
- Construct an explicit BioSTEAM flowsheet from edges; pass streams between units for detailed mass balances.
- Keep optional until stage‑order execution is stable.

## Current Status (end of 2025‑10‑16)
- AEX Membrane UI added with:
  - Placement autodetect (pre/post‑SPTFF, DSP04 fallback)
  - Conductivity (mS/cm) with simple mM mapping
  - Post‑SPTFF volume suggestions (CF‑aware preview)
  - Overrides exported under `dsp04.membrane_aex` with placement + parameters
- Inspector compile issue fixed; palette and editor wired.

## Next Actions
- Implement Phase 1 (`stage_order` export + backend hook) and basic validations.
- Add an optional “Auto‑detect now” button to recompute placement/volume after rewiring.
- Open PR for review and merge to `main` once validated.

