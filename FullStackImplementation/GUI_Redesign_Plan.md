# BioSTEAM Front-End GUI — Redesign Plan (Drag-and-Drop Blocks)

## Vision
- Intuitive, “fun to use” block-based designer for USP/DSP flows.
- Drag blocks, connect stages, configure parameters, and run simulations.
- One-click results overlay (yields, volumes, costs) with a clear TEA panel.
- Built-in buffer design and costing (dropdown + wizard), auto-planner guidance.
- Versioned overrides and revisions with easy diffs.

## Architecture
- Front-end: Next.js + React + React Flow (graph editor), TanStack Query (data), Zustand (UI state), Tailwind/Mantine (UI kit), ECharts/Recharts (charts).
- API: FastAPI (existing) with endpoints for buffers and runs.
- Runtime: local uvicorn + next dev (Docker Compose option later); Electron packaging optional.

## Core UX (MVP)
- Canvas (center): drag blocks (USP, DSP01–05, macro Front-End), connect ports; graph overlays KPIs on run.
- Palette (left): unit library with your icons; search and category filters.
- Inspector (right): parameters and guardrails; for DSP03, buffer selector (GET /buffers) and “Apply recommendations” (GET /buffers/{id}/recommendations).
- Results (bottom): TEA summary, materials breakdown, planner/costing notes.
- Toolbar: Run, Reset, Undo/Redo, Zoom, Save/Load, Theme.
- Revisions: snapshot timeline (graph + overrides) with parameter diffs.

## Data Model & Mapping
- Graph schema → Scenario/Overrides mapping:
  - Node: `{ id, template, overrides }`, Edge: `{ from, to }`.
  - Front-End mode uses a macro node that writes `baseline_overrides` for `migration.front_end`.
  - Scenario Builder mode maps the graph to `Scenario` (app/api/models/scenario.py), then POST /runs.

## API Integration (existing)
- `GET /buffers`: curated buffer recipes for dropdown (id, name, pH, components, estimated USD/m³).
- `GET /buffers/{id}`: details + derived ionic strength and conductivity.
- `GET /buffers/{id}/recommendations`: suggested planner targets and an overrides stub.
- `POST /buffers`: create buffer from templates (phosphate/Tris) or direct components.
- `POST /runs/front_end`: run with inline `baseline_overrides`; returns TEA metrics + dsp03 notes.

## MVP Roadmap (Sprints)
1) UI Shell + Graph
   - Next.js app skeleton, React Flow canvas, Palette + Inspector scaffold, icons hookup.
   - Exporter stub: graph → overrides stub.
2) API Wiring + DSP03 Flow
   - Wire /buffers and recommendations to Inspector; “Apply recommendations” backfills planner form.
   - Run pipeline via /runs/front_end; render TEA and dsp03_notes.
3) Revisions + TEA Overlays
   - Save/Load graph + overrides; revision timeline + param diffs.
   - Canvas overlays for yields/volumes/cost hotspots.
4) Scenario Builder (optional track)
   - Switch to full `Scenario` mapping; POST /runs for custom flows.
5) Polish & Guides
   - Buffer wizard (create from stocks), onboarding tour, theming, accessibility.

## Implementation Tasks (Initial)
- Create `/app/ui` (Next.js 14) with pages:
  - `/designer` (Canvas + Inspector + Palette)
  - `/buffers` (optional buffers browser)
- Core components:
  - GraphCanvas (React Flow), NodeRenderer (custom nodes), EdgeRenderer.
  - Palette (searchable list), InspectorPanel (forms via RHF/Zod), ResultsPanel (charts/tables).
  - RunButton (calls /runs/front_end), SaveLoad controls (local file + snapshots).
- State/Services:
  - `useGraphStore` (Zustand) for layout/selection/undo/redo.
  - `useApi` (TanStack Query) for buffers, recommendations, runs.
  - Mapper utils: graph ⇄ overrides (front-end macro node).

## UI Behaviors
- Buffer selection: dropdown from `GET /buffers`, show “Name (pH X.Y) – ~$YY/m³”. Apply planning via recommendations.
- Planner form: target I or conductivity + guardrails; viscosity & antifoam toggles.
- Results overlay: per-node yield and volume arrows; cost callouts.
- Revisions: annotate each run with a note and keep diffs of changed parameters.

## Dev Workflow
- Run API: `uvicorn app.api.main:app --reload --port 8000`.
- Run UI: `pnpm dev` (or npm/yarn) in `/app/ui`.
- Swagger: `http://localhost:8000/docs` to try endpoints.
- Example run: use recommendations overrides with `POST /runs/front_end`.

## Open Questions
- Web vs Electron packaging to start? (local is fine initially)
- Auth/users and persistence (local-first; later multi-user?)
- Revision storage (local JSON vs Git-backed);
- Final color palette & icon set (you’ll provide assets).

## Next Steps
1) Confirm stack (Next.js + React Flow) and layout.
2) Scaffold `/app/ui` with Canvas/Palette/Inspector shells.
3) Wire `GET /buffers` + `GET /buffers/{id}/recommendations` into Inspector.
4) Add Run hook to `POST /runs/front_end`; print TEA + notes.
5) Iterate on look-and-feel with your icons and theme.

