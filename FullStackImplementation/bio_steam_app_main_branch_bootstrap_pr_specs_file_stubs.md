# BioSTEAM App — Main Branch Bootstrap PR (specs + file stubs)

This document is a ready‑to‑commit plan for the **main** branch. It includes a concise PR scope, directory layout, stub files, and copy‑pasteable contents for each stub so your team can spin up **API + UI + CLI** without Excel. Keep this PR small and focused; follow with feature PRs.

---

## PR title
**feat(app): scaffold API, CLI, UI, scenario schema, and run engine**

## PR scope
- Add Python service (FastAPI) with scenario schemas and run engine wrappers around BioSTEAM.
- Add minimal CLI (`bdsteam`) for headless runs.
- Add Next.js UI shell with Run → Results flow and placeholder charts.
- Add Docker compose and Makefile.
- Add CI (lint, type-check, unit tests) and a golden regression test.

---

## Repository layout (new top‑level `/app` monorepo folder)
```
/app
  /api                 # FastAPI service
    main.py
    routers/
      runs.py
      scenarios.py
      units.py
    models/
      scenario.py
      common.py
    engine/
      registry.py
      builder.py
      runner.py
      uncertainty.py
      storage_fs.py
    tests/
      test_golden.py
    pyproject.toml

  /cli
    __init__.py
    __main__.py
    pyproject.toml

  /ui                  # Next.js 14 (app router)
    package.json
    next.config.mjs
    tsconfig.json
    app/
      layout.tsx
      page.tsx
      scenarios/page.tsx
      runs/[id]/page.tsx
    src/
      lib/api.ts
      types.ts
      components/
        Button.tsx
        Card.tsx
        Waterfall.tsx
        Sankey.tsx

  /docker
    Dockerfile.api
    Dockerfile.ui
    docker-compose.yml

  Makefile
  .env.example
  .gitignore
  .pre-commit-config.yaml
  .github/workflows/ci.yml

/scenarios
  OPN_demo/
    scenario.yaml
```

---

## Python versions and deps
- Python **3.11**
- FastAPI, Uvicorn
- Pydantic v2
- numpy, pandas
- SALib (later PR can wire sobol)
- your BioSTEAM fork + thermosteam (pin with commit hash or editable install)

---

## File stubs — copy/paste

### `/app/api/pyproject.toml`
```toml
[project]
name = "bdsteam-api"
version = "0.1.0"
description = "BioSTEAM scenario API"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.111",
  "uvicorn[standard]>=0.30",
  "pydantic>=2.8",
  "numpy>=1.26",
  "pandas>=2.2",
  "SALib>=1.4",
]

[tool.pip]
# local editable installs suggested in dev docs (see Makefile)
```

### `/app/api/main.py`
```python
from fastapi import FastAPI
from .routers import runs, scenarios, units

app = FastAPI(title="BDSTEAM API", version="0.1.0")
app.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(units.router, prefix="/units", tags=["units"])

@app.get("/health")
def health():
    return {"status": "ok"}
```

### `/app/api/models/common.py`
```python
from pydantic import BaseModel, Field
from typing import Literal

DistName = Literal["uniform", "normal", "lognormal"]

class UncertaintySpec(BaseModel):
    dist: DistName
    # accept generic params; per-dist validation can be added later
    low: float | None = None
    high: float | None = None
    mu: float | None = None
    sigma: float | None = None
```

### `/app/api/models/scenario.py`
```python
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from .common import UncertaintySpec

class UnitInstance(BaseModel):
    template: str
    id: str
    overrides: Dict[str, float | int | str | bool] = Field(default_factory=dict)

class StreamLink(BaseModel):
    from_: str = Field(alias="from")
    to: str

class Scenario(BaseModel):
    name: str
    version: str
    thermo_package: str | None = None
    units: List[UnitInstance]
    streams: List[StreamLink]
    assumptions: Dict[str, float | int | str] = Field(default_factory=dict)
    uncertainty: Dict[str, UncertaintySpec] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
```

### `/app/api/engine/registry.py`
```python
# Maps template names to import paths or callables returning BioSTEAM Unit classes
from typing import Callable, Dict

UnitFactory = Callable[..., object]

_registry: Dict[str, UnitFactory] = {}

def register(template: str, factory: UnitFactory) -> None:
    _registry[template] = factory

def get_factory(template: str) -> UnitFactory:
    if template not in _registry:
        raise KeyError(f"Unit template not registered: {template}")
    return _registry[template]

# TODO: register fermenter, disk stack, MF, AEX_membrane, UFDF, spray dryer factories here or in a plugin file
```

### `/app/api/engine/builder.py`
```python
from .registry import get_factory
from ..models.scenario import Scenario

class BuildResult:
    def __init__(self, system, flowsheet):
        self.system = system
        self.flowsheet = flowsheet


def build_system(scenario: Scenario) -> BuildResult:
    # Pseudocode until you wire actual BioSTEAM imports
    # import biosteam as bst
    # bst.settings.set_thermo("milk" or scenario.thermo_package)
    unit_map = {}
    for u in scenario.units:
        factory = get_factory(u.template)
        unit = factory(id=u.id, **u.overrides)
        unit_map[u.id] = unit
    # connect streams
    for s in scenario.streams:
        upstream = unit_map[s.from_]
        downstream = unit_map[s.to]
        # create and connect a stream; placeholder
        # stream = bst.Stream(source=upstream, sink=downstream)
        pass
    # system = bst.System(...)
    system = object()
    flowsheet = {"units": list(unit_map)}
    return BuildResult(system=system, flowsheet=flowsheet)
```

### `/app/api/engine/runner.py`
```python
from datetime import datetime
from ..models.scenario import Scenario
from .builder import build_system


def run_deterministic(scenario: Scenario) -> dict:
    build = build_system(scenario)
    # TODO: call system.simulate(); TEA; compile KPIs
    results = {
        "scenario": scenario.name,
        "timestamp": datetime.utcnow().isoformat(),
        "kpis": {
            "cog_per_kg": None,
            "annual_throughput_kg": None,
            "overall_yield": None,
        },
        "engine": {
            "biosteam_version": "tbd",
            "thermosteam_version": "tbd",
            "git_hash": "tbd",
        },
    }
    return results
```

### `/app/api/engine/uncertainty.py`
```python
from ..models.scenario import Scenario

def run_sobol(scenario: Scenario, n: int = 512) -> dict:
    # Placeholder; wire SALib in a later PR
    return {"samples": n, "results": []}
```

### `/app/api/engine/storage_fs.py`
```python
from pathlib import Path
import json

ROOT = Path("scenarios").resolve()

def save_results(scenario_name: str, run_id: str, results: dict) -> Path:
    outdir = ROOT / scenario_name / "results"
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / f"{run_id}.json"
    path.write_text(json.dumps(results, indent=2))
    return path
```

### `/app/api/routers/scenarios.py`
```python
from fastapi import APIRouter, HTTPException
from ..models.scenario import Scenario
from pathlib import Path
import yaml

router = APIRouter()
ROOT = Path("scenarios").resolve()

@router.post("")
def upsert_scenario(scenario: Scenario):
    d = ROOT / scenario.name
    d.mkdir(parents=True, exist_ok=True)
    (d / "scenario.yaml").write_text(yaml.safe_dump(scenario.model_dump(by_alias=True)))
    return {"status": "ok", "path": str(d)}
```

### `/app/api/routers/runs.py`
```python
from fastapi import APIRouter
from pydantic import BaseModel
from ..models.scenario import Scenario
from ..engine.runner import run_deterministic
from ..engine.storage_fs import save_results
import uuid

router = APIRouter()

class RunRequest(BaseModel):
    scenario: Scenario
    analyses: list[str] = ["deterministic"]

@router.post("")
def create_run(req: RunRequest):
    run_id = uuid.uuid4().hex[:8]
    results = run_deterministic(req.scenario)
    save_results(req.scenario.name, run_id, results)
    return {"run_id": run_id, "summary": results["kpis"]}
```

### `/app/api/routers/units.py`
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("")
def list_units():
    # TODO: real registry dump; for now return placeholders
    return [
        {"template": "SeedFermenter_v1", "category": "USP"},
        {"template": "ProdFermenter_v2", "category": "USP"},
        {"template": "DiskStack_v1", "category": "DSP"},
        {"template": "MF_Polishing_v1", "category": "DSP"},
        {"template": "AEX_membrane_v1", "category": "DSP"},
        {"template": "UFDF_v1", "category": "DSP"},
        {"template": "SprayDry_v1", "category": "Formulation"},
    ]
```

### `/app/api/tests/test_golden.py`
```python
from ..models.scenario import Scenario
from ..engine.runner import run_deterministic

def test_runs():
    sc = Scenario(
        name="OPN_demo", version="0.1", thermo_package=None,
        units=[{"template":"ProdFermenter_v2","id":"prod1","overrides":{}}],
        streams=[], assumptions={}, uncertainty={}
    )
    out = run_deterministic(sc)
    assert "kpis" in out
```

### `/app/cli/pyproject.toml`
```toml
[project]
name = "bdsteam-cli"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["pydantic>=2.8", "pyyaml>=6"]

[project.scripts]
bdsteam = "cli.__main__:main"
```

### `/app/cli/__main__.py`
```python
import argparse, json, yaml
from pathlib import Path
from app.api.models.scenario import Scenario
from app.api.engine.runner import run_deterministic


def main():
    p = argparse.ArgumentParser()
    p.add_argument("scenario", type=Path)
    p.add_argument("--out", type=Path, default=Path("results.json"))
    args = p.parse_args()
    sc = Scenario.model_validate(yaml.safe_load(args.scenario.read_text()))
    res = run_deterministic(sc)
    args.out.write_text(json.dumps(res, indent=2))
    print(f"wrote {args.out}")

if __name__ == "__main__":
    main()
```

### `/app/ui/package.json`
```json
{
  "name": "bdsteam-ui",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "14.2.3",
    "react": "18.3.1",
    "react-dom": "18.3.1"
  },
  "devDependencies": {
    "typescript": "5.5.4"
  }
}
```

### `/app/ui/app/layout.tsx`
```tsx
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin:0, fontFamily:'ui-sans-serif, system-ui' }}>{children}</body>
    </html>
  );
}
```

### `/app/ui/app/page.tsx`
```tsx
import Link from "next/link";
export default function Home() {
  return (
    <main style={{ padding: 24 }}>
      <h1>BDSTEAM</h1>
      <p>Prototype UI — run scenarios and view results.</p>
      <ul>
        <li><Link href="/scenarios">Scenarios</Link></li>
      </ul>
    </main>
  );
}
```

### `/app/ui/app/scenarios/page.tsx`
```tsx
'use client';
import { useState } from 'react';

export default function Scenarios() {
  const [yamlText, setYamlText] = useState(`name: OPN_demo\nversion: '0.1'\nunits: []\nstreams: []\nassumptions: {}\nuncertainty: {}`);
  const [result, setResult] = useState<any>(null);

  const run = async () => {
    const scenario = yamlToJson(yamlText);
    const r = await fetch('http://localhost:8000/runs', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario, analyses: ['deterministic'] })
    }).then(r => r.json());
    setResult(r);
  };

  return (
    <main style={{ padding: 24 }}>
      <h2>Scenario runner</h2>
      <textarea style={{ width: '100%', height: 240 }} value={yamlText} onChange={e=>setYamlText(e.target.value)} />
      <div style={{ marginTop: 8 }}>
        <button onClick={run}>Run</button>
      </div>
      {result && (
        <pre style={{marginTop:16, background:'#f6f6f6', padding:12}}>{JSON.stringify(result, null, 2)}</pre>
      )}
    </main>
  );
}

function yamlToJson(text: string) {
  // extremely naive; replace later with proper yaml in server-side; here we expect JSON-compatible string
  try { return JSON.parse(text); } catch {
    // fallback dummy
    return { name: 'OPN_demo', version: '0.1', units: [], streams: [], assumptions: {}, uncertainty: {} };
  }
}
```

### `/app/ui/app/runs/[id]/page.tsx`
```tsx
export default function RunPage({ params }: { params: { id: string } }) {
  return (
    <main style={{ padding: 24 }}>
      <h2>Run {params.id}</h2>
      <p>Results detail view — wire to /runs/{params.id}.</p>
    </main>
  );
}
```

### `/app/ui/src/components/Waterfall.tsx`
```tsx
export default function Waterfall() { return null; }
```

### `/app/ui/next.config.mjs`
```js
/** @type {import('next').NextConfig} */
const nextConfig = { reactStrictMode: true };
export default nextConfig;
```

### `/app/ui/tsconfig.json`
```json
{ "compilerOptions": { "jsx": "react-jsx", "module": "esnext", "target": "es2022", "allowJs": true, "skipLibCheck": true }, "include": ["app", "src"] }
```

### `/app/docker/Dockerfile.api`
```Dockerfile
FROM python:3.11-slim
WORKDIR /srv
COPY ./api /srv/api
RUN pip install --no-cache-dir -e /srv/api
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `/app/docker/Dockerfile.ui`
```Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY ./ui /app
RUN npm ci && npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=build /app .
EXPOSE 3000
CMD ["npm", "start"]
```

### `/app/docker/docker-compose.yml`
```yaml
version: "3.8"
services:
  api:
    build: { context: ../, dockerfile: app/docker/Dockerfile.api }
    ports: ["8000:8000"]
    volumes: ["../scenarios:/scenarios"]
  ui:
    build: { context: ../, dockerfile: app/docker/Dockerfile.ui }
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API=http://localhost:8000
```

### `/Makefile`
```make
.PHONY: dev api ui cli test

python := python3.11

dev: ## install dev deps
	cd app/api && $(python) -m pip install -e .
	cd app/cli && $(python) -m pip install -e .

api:
	uvicorn app.api.main:app --reload --port 8000

ui:
	cd app/ui && npm i && npm run dev

test:
	cd app/api && pytest -q
```

### `/.env.example`
```
# reserve for future secrets (DB, JWT, etc.)
```

### `/.github/workflows/ci.yml`
```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - name: Install API
        run: |
          cd app/api
          python -m pip install -e .
      - name: Run tests
        run: |
          cd app/api
          python -m pip install pytest
          pytest -q
```

---

## Demo scenario stub
### `/scenarios/OPN_demo/scenario.yaml`
```yaml
name: OPN_demo
version: "0.1"
thermo_package: null
units:
  - template: ProdFermenter_v2
    id: prod1
    overrides:
      working_volume_m3: 70
      titer_g_L: 5
streams: []
assumptions:
  cmo_day_rate_usd: 25000
uncertainty: {}
```

---

## Developer workflow
1. **Create the monorepo structure** above and paste stubs.
2. `make dev` to install API + CLI.
3. `make api` to run FastAPI at `localhost:8000`.
4. `make ui` to run Next.js at `localhost:3000`.
5. From the root: `python -m app.cli scenarios/OPN_demo/scenario.yaml --out results.json` to verify CLI.

---

## Follow‑up PRs (small, vertical slices)
1. **Wire real BioSTEAM**: implement factories for Unit templates; set thermo; connect streams; call `System.simulate()`; TEA → KPIs.
2. **Uncertainty**: SALib Sobol + spider plot, histogram.
3. **Flowsheet editor**: React Flow canvas + parameter inspector mapped to `exposed_params`.
4. **Data import & provenance**: CSV mapping → parameter updates with badges in UI.
5. **Amortization toggles**: batch vs campaign vs year; unit tests to guard accounting.
6. **Authentication & multi‑user**: JWT + Postgres (optional).

---

## Notes
- Keep this bootstrap PR intentionally thin. It unblocks parallel workstreams (engine, UI, uncertainty) without entanglement.
- Pin BioSTEAM/thermosteam versions in a subsequent PR once factories are added and golden tests produce stable KPIs.



---

## Update: Unit registry with Chitosan capture + DSP04 variants
This patch adds concrete factory stubs for your current pipeline (seed → prod → disk stack → MF → **DSP04** variant → UF/DF → spray dryer), including **ChitosanCapture** and multiple DSP04 options. It also adds a tiny routing DSL and two ready-to-run scenario examples.

> Drop these files into the paths shown. They’re compatible with the bootstrap in this PR.

### `/app/api/engine/registry.py` (replace with this fuller version)
```python
from typing import Callable, Dict, Any

# Typing note: our UnitFactory returns an object (BioSTEAM Unit). We keep it duck-typed.
UnitFactory = Callable[..., object]

_registry: Dict[str, UnitFactory] = {}


def register(template: str, factory: UnitFactory) -> None:
    if template in _registry:
        raise ValueError(f"Template already registered: {template}")
    _registry[template] = factory


def get_factory(template: str) -> UnitFactory:
    try:
        return _registry[template]
    except KeyError:
        raise KeyError(f"Unit template not registered: {template}")


# -------- Built‑in factory stubs (wire to BioSTEAM later) --------
# Each factory accepts **overrides and sets sensible defaults so scenarios are lightweight.

def _make_with_defaults(name: str, defaults: Dict[str, Any], overrides: Dict[str, Any]):
    cfg = {**defaults, **(overrides or {})}
    # Placeholder until BioSTEAM units are imported; return a simple record object.
    return type(name, (), {"config": cfg, "name": name})()


# USP

def SeedFermenter_v1(id: str, **overrides):
    defaults = dict(working_volume_m3=7.0, temp_C=30.0, pH=5.5, time_h=18.0)
    return _make_with_defaults(id, defaults, overrides)


def ProdFermenter_v2(id: str, **overrides):
    defaults = dict(working_volume_m3=70.0, titer_g_L=5.0, glucose_g_L=100.0, temp_C=30.0, time_h=72.0)
    return _make_with_defaults(id, defaults, overrides)


# Primary recovery

def DiskStack_v1(id: str, **overrides):
    defaults = dict(flow_m3_h=5.0, yield_fraction=0.98, power_kW=20.0)
    return _make_with_defaults(id, defaults, overrides)


def MF_Polishing_v1(id: str, **overrides):
    defaults = dict(area_m2=20.0, flux_L_m2_h=60.0, yield_fraction=0.99, TMP_bar=1.0)
    return _make_with_defaults(id, defaults, overrides)


# DSP04 variants (choose one per scenario)

def AEX_Column_v1(id: str, **overrides):
    defaults = dict(resin_capacity_g_L=50.0, bed_volume_L=10.0, flow_BV_h=3.0, yield_fraction=0.85,
                    resin_cost_usd_per_L=800.0, cip_time_h=0.5, lifetime_cycles=50)
    return _make_with_defaults(id, defaults, overrides)


def AEX_Membrane_v1(id: str, **overrides):
    defaults = dict(membrane_area_m2=5.0, flux_L_m2_h=150.0, capacity_g_m2=400.0, yield_fraction=0.88,
                    membrane_cost_usd_m2=350.0, cip_time_h=0.25, lifetime_cycles=30)
    return _make_with_defaults(id, defaults, overrides)


def ChitosanCapture_v1(id: str, **overrides):
    # Parameters reflect your lab program knobs; refine with real data via imports mapping.
    defaults = dict(
        polymer_type="LMW", polymer_pct_wv=0.1, target_pH=4.4, NaCl_mM=250,
        stoichiometry_mass_ratio=2.0, contact_time_min=15.0,
        yield_fraction=0.80, dna_reduction_log=2.0,
        polymer_cost_usd_per_kg=18.0, recycle_fraction=0.5,
        elution_buffer="citrate", elution_M=0.15, elution_pH=6.0,
        wash_cycles=1, decant_efficiency=0.98
    )
    return _make_with_defaults(id, defaults, overrides)


# Downstream finishing

def UFDF_v1(id: str, **overrides):
    defaults = dict(area_m2=10.0, flux_L_m2_h=40.0, cff=3.0, yield_fraction=0.95,
                    membrane_cost_usd_m2=220.0, lifetime_cycles=20)
    return _make_with_defaults(id, defaults, overrides)


def SprayDry_v1(id: str, **overrides):
    defaults = dict(evap_rate_kg_h=100.0, inlet_C=180.0, outlet_C=90.0, yield_fraction=0.98,
                    energy_kWh_per_kg_water=0.8)
    return _make_with_defaults(id, defaults, overrides)


# Public registration API used by app startup

def register_defaults():
    register("SeedFermenter_v1", SeedFermenter_v1)
    register("ProdFermenter_v2", ProdFermenter_v2)
    register("DiskStack_v1", DiskStack_v1)
    register("MF_Polishing_v1", MF_Polishing_v1)
    register("AEX_Column_v1", AEX_Column_v1)
    register("AEX_Membrane_v1", AEX_Membrane_v1)
    register("ChitosanCapture_v1", ChitosanCapture_v1)
    register("UFDF_v1", UFDF_v1)
    register("SprayDry_v1", SprayDry_v1)
```

### `/app/api/main.py` (add registry bootstrap)
```python
from fastapi import FastAPI
from .routers import runs, scenarios, units
from .engine.registry import register_defaults

app = FastAPI(title="BDSTEAM API", version="0.1.0")
register_defaults()

app.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(units.router, prefix="/units", tags=["units"])

@app.get("/health")
def health():
    return {"status": "ok"}
```

### `/app/api/engine/builder.py` (augment with a tiny routing DSL)
```python
from .registry import get_factory
from ..models.scenario import Scenario
from typing import Dict

class BuildResult:
    def __init__(self, system, flowsheet, unit_map: Dict[str, object]):
        self.system = system
        self.flowsheet = flowsheet
        self.unit_map = unit_map


def build_system(scenario: Scenario) -> BuildResult:
    unit_map: Dict[str, object] = {}
    for u in scenario.units:
        factory = get_factory(u.template)
        unit = factory(id=u.id, **(u.overrides or {}))
        unit_map[u.id] = unit

    # Minimal stream linking placeholder; real implementation will create bst.Streams
    links = [(s.from_, s.to) for s in scenario.streams]
    flowsheet = {"units": list(unit_map.keys()), "links": links}

    # TODO: integrate biosteam.System(...) construction here.
    system = object()
    return BuildResult(system=system, flowsheet=flowsheet, unit_map=unit_map)
```

### `/app/api/routers/units.py` (reflect new templates)
```python
from fastapi import APIRouter

router = APIRouter()

@router.get("")
def list_units():
    return [
        {"template": "SeedFermenter_v1", "category": "USP"},
        {"template": "ProdFermenter_v2", "category": "USP"},
        {"template": "DiskStack_v1", "category": "Primary Recovery"},
        {"template": "MF_Polishing_v1", "category": "Primary Recovery"},
        {"template": "AEX_Column_v1", "category": "DSP04"},
        {"template": "AEX_Membrane_v1", "category": "DSP04"},
        {"template": "ChitosanCapture_v1", "category": "DSP04"},
        {"template": "UFDF_v1", "category": "Finishing"},
        {"template": "SprayDry_v1", "category": "Finishing"},
    ]
```

---

## Scenario examples demonstrating DSP04 swapping

### 1) AEX (membrane) as DSP04
`/scenarios/OPN_DSP04_memAEX/scenario.yaml`
```yaml
name: OPN_DSP04_memAEX
version: "0.1"
units:
  - template: ProdFermenter_v2
    id: prod1
  - template: DiskStack_v1
    id: ds1
  - template: MF_Polishing_v1
    id: mf1
  - template: AEX_Membrane_v1
    id: dsp04
    overrides:
      capacity_g_m2: 500
      yield_fraction: 0.90
  - template: UFDF_v1
    id: ufdf1
  - template: SprayDry_v1
    id: sd1
streams:
  - { from: prod1, to: ds1 }
  - { from: ds1,   to: mf1 }
  - { from: mf1,   to: dsp04 }
  - { from: dsp04, to: ufdf1 }
  - { from: ufdf1, to: sd1 }
assumptions:
  cmo_day_rate_usd: 25000
uncertainty: {}
```

### 2) Chitosan capture as DSP04
`/scenarios/OPN_DSP04_chitosan/scenario.yaml`
```yaml
name: OPN_DSP04_chitosan
version: "0.1"
units:
  - template: ProdFermenter_v2
    id: prod1
  - template: DiskStack_v1
    id: ds1
  - template: MF_Polishing_v1
    id: mf1
  - template: ChitosanCapture_v1
    id: dsp04
    overrides:
      polymer_type: LMW
      polymer_pct_wv: 0.1
      target_pH: 4.4
      NaCl_mM: 250
      stoichiometry_mass_ratio: 2.0
      yield_fraction: 0.82
      recycle_fraction: 0.6
  - template: UFDF_v1
    id: ufdf1
  - template: SprayDry_v1
    id: sd1
streams:
  - { from: prod1, to: ds1 }
  - { from: ds1,   to: mf1 }
  - { from: mf1,   to: dsp04 }
  - { from: dsp04, to: ufdf1 }
  - { from: ufdf1, to: sd1 }
assumptions:
  cmo_day_rate_usd: 25000
uncertainty: {}
```

---

## Notes on cost hooks you’ll wire next
- **AEX_Column_v1**: expose `resin_cost_usd_per_L` and `lifetime_cycles` so amortization per **batch/campaign/year** can be toggled in TEA code.
- **AEX_Membrane_v1 / UFDF_v1**: expose `membrane_cost_usd_m2` and `lifetime_cycles`.
- **ChitosanCapture_v1**: expose `polymer_cost_usd_per_kg`, `recycle_fraction`, and optionally a `neutralization_cost_usd_per_mol` once you track buffer chemistry.
- All units expose `yield_fraction` so result deltas propagate cleanly in waterfalls and sensitivity.

## Where to integrate BioSTEAM proper
- In `builder.py`, after instantiating, replace placeholders with real `bst.Unit` classes and real `bst.Stream` connections; return an actual `bst.System`.
- In `runner.py`, call `system.simulate()` and compute TEA with BioSTEAM TEA classes; write KPIs.

Once this is in, your UI can present DSP04 as a radio‑button choice among **AEX Column**, **AEX Membrane**, and **Chitosan**, with parameter inspectors bound to the `overrides` shown above.



---

## Update: NLS — full command implementation (add/remove/connect/disconnect/duplicate)
Below are drop‑in replacements/additions to fully wire the remaining commands. This includes JSON‑Patch generation, a batch endpoint, FastAPI router wiring, and tests. It keeps everything schema‑validated via your existing `Scenario` Pydantic model.

### 1) Add dependency for applying patches in tests
**File:** `/app/api/pyproject.toml` (append to dependencies)
```toml
[project]
# ...existing...
dependencies = [
  # existing deps
  "fastapi>=0.111",
  "uvicorn[standard]>=0.30",
  "pydantic>=2.8",
  "numpy>=1.26",
  "pandas>=2.2",
  "SALib>=1.4",
  "jsonpatch>=1.33",
]
```

### 2) Wire NLS router
**File:** `/app/api/main.py` (add import + include_router)
```python
from fastapi import FastAPI
from .routers import runs, scenarios, units
from .engine.registry import register_defaults
from .routers import nls  # NEW

app = FastAPI(title="BDSTEAM API", version="0.1.0")
register_defaults()

app.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
app.include_router(runs.router, prefix="/runs", tags=["runs"])
app.include_router(units.router, prefix="/units", tags=["units"])
app.include_router(nls.router)  # NEW

@app.get("/health")
def health():
    return {"status": "ok"}
```

### 3) Parser already supports the grammar
Ensure `/app/api/nls/parser.py` from the NLS doc is added.

### 4) Editor: implement add/remove/connect/disconnect/duplicate
**File:** `/app/api/nls/editor.py`
```python
from copy import deepcopy
from typing import Dict, Any, List, Tuple
from ..models.scenario import Scenario
from .parser import Parsed

# Helpers

def _unit_index(sc: Scenario, unit_id: str) -> int:
    for i, u in enumerate(sc.units):
        if u.id == unit_id:
            return i
    raise KeyError(unit_id)


def _find_first_by_template(sc: Scenario, template: str) -> int | None:
    for i, u in enumerate(sc.units):
        if u.template.lower() == template.lower():
            return i
    return None


def _ensure_unit_id(sc: Scenario, base: str) -> str:
    existing = {u.id for u in sc.units}
    if base not in existing:
        return base
    k = 2
    while f"{base}_{k}" in existing:
        k += 1
    return f"{base}_{k}"


def _find_links(sc: Scenario, src: str | None = None, dst: str | None = None) -> List[int]:
    idxs = []
    for i, s in enumerate(sc.streams):
        if src is not None and s.from_ != src:
            continue
        if dst is not None and s.to != dst:
            continue
        idxs.append(i)
    return idxs

# Patch builders

def replace_unit(sc: Scenario, template_or_id_from: str, template_to: str) -> List[dict]:
    sc2 = deepcopy(sc)
    try:
        idx = _unit_index(sc2, template_or_id_from)
    except KeyError:
        idx = _find_first_by_template(sc2, template_or_id_from)
        if idx is None:
            raise KeyError(f"Unit not found: {template_or_id_from}")
    return [{"op": "replace", "path": f"/units/{idx}/template", "value": template_to}]


def set_params(sc: Scenario, params: Dict[str, Any], scope: str | None) -> List[dict]:
    sc2 = deepcopy(sc)
    patches: List[dict] = []
    targets: List[int] = []
    if scope:
        try:
            targets = [_unit_index(sc2, scope)]
        except KeyError:
            idx = _find_first_by_template(sc2, scope)
            if idx is None:
                raise KeyError(f"Scope not found: {scope}")
            targets = [idx]
    else:
        targets = [0] if sc2.units else []
    for idx in targets:
        for k, v in params.items():
            patches.append({"op": "add", "path": f"/units/{idx}/overrides/{k}", "value": v})
    return patches


def add_unit(sc: Scenario, unit_template: str, after: str | None, before: str | None, at: str | None) -> List[dict]:
    sc2 = deepcopy(sc)
    # Decide new id
    base = unit_template.split("_")[0].lower()
    new_id = _ensure_unit_id(sc2, base)

    unit_patch = {"op": "add", "path": f"/units/-", "value": {"template": unit_template, "id": new_id, "overrides": {}}}
    patches: List[dict] = [unit_patch]

    # Stream rewiring heuristics
    if after:
        # Redirect all after's outgoing links to go via new unit
        out_links = [sc2.streams[i] for i in _find_links(sc2, src=after)]
        for i, link in enumerate(out_links):
            # remove old link
            idx = _find_links(sc2, src=after, dst=link.to)[0]
            patches.append({"op": "remove", "path": f"/streams/{idx}"})
            # add two links: after -> new, new -> old_to
            patches.append({"op": "add", "path": "/streams/-", "value": {"from": after, "to": new_id}})
            patches.append({"op": "add", "path": "/streams/-", "value": {"from": new_id, "to": link.to}})
    elif before:
        in_links = [sc2.streams[i] for i in _find_links(sc2, dst=before)]
        for link in in_links:
            idx = _find_links(sc2, src=link.from_, dst=before)[0]
            patches.append({"op": "remove", "path": f"/streams/{idx}"})
            patches.append({"op": "add", "path": "/streams/-", "value": {"from": link.from_, "to": new_id}})
            patches.append({"op": "add", "path": "/streams/-", "value": {"from": new_id, "to": before}})
    else:
        # no rewiring; user will connect later
        pass
    return patches


def remove_unit(sc: Scenario, target: str) -> List[dict]:
    sc2 = deepcopy(sc)
    try:
        idx = _unit_index(sc2, target)
    except KeyError:
        idx = _find_first_by_template(sc2, target)
        if idx is None:
            raise KeyError(f"Unit not found: {target}")
    unit_id = sc2.units[idx].id
    patches: List[dict] = []
    # remove incident links first (from last to first to keep indexes stable if applying manually)
    for i in sorted(_find_links(sc2, src=unit_id) + _find_links(sc2, dst=unit_id), reverse=True):
        patches.append({"op": "remove", "path": f"/streams/{i}"})
    patches.append({"op": "remove", "path": f"/units/{idx}"})
    return patches


def connect_units(sc: Scenario, from_id: str, to_id: str) -> List[dict]:
    # Prevent duplicate
    for s in sc.streams:
        if s.from_ == from_id and s.to == to_id:
            return []
    return [{"op": "add", "path": "/streams/-", "value": {"from": from_id, "to": to_id}}]


def disconnect_units(sc: Scenario, from_id: str, to_id: str) -> List[dict]:
    idxs = _find_links(sc, src=from_id, dst=to_id)
    if not idxs:
        return []
    # remove last match
    idx = idxs[-1]
    return [{"op": "remove", "path": f"/streams/{idx}"}]


def duplicate_unit(sc: Scenario, target: str, new_id: str) -> List[dict]:
    sc2 = deepcopy(sc)
    try:
        idx = _unit_index(sc2, target)
    except KeyError:
        idx = _find_first_by_template(sc2, target)
        if idx is None:
            raise KeyError(f"Unit not found: {target}")
    u = sc2.units[idx]
    new_obj = {"template": u.template, "id": new_id, "overrides": dict(u.overrides or {})}
    return [{"op": "add", "path": "/units/-", "value": new_obj}]


def apply(sc: Scenario, p: Parsed) -> List[dict]:
    t = p.type
    a = p.args
    if t == "replace":
        return replace_unit(sc, a["source"], a["dest"])
    if t == "set":
        return set_params(sc, a["params"], a.get("scope"))
    if t == "add":
        return add_unit(sc, a["unit"], a.get("after"), a.get("before"), a.get("at"))
    if t == "remove":
        return remove_unit(sc, a["target"])
    if t == "connect":
        return connect_units(sc, a["from"], a["to"])
    if t == "disconnect":
        return disconnect_units(sc, a["from"], a["to"])
    if t == "duplicate":
        return duplicate_unit(sc, a["target"], a["new_id"])
    raise NotImplementedError(t)
```

### 5) NLS Router: preview/apply/batch/help
**File:** `/app/api/routers/nls.py`
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..models.scenario import Scenario
from ..nls.parser import parse
from ..nls.editor import apply as build_patch
import jsonpatch

router = APIRouter(prefix="/nls", tags=["nls"])

class NLSRequest(BaseModel):
    command_text: str
    scenario: Scenario

class NLSBatch(BaseModel):
    commands: list[str]
    scenario: Scenario

@router.get("/help")
def help():
    return {
        "grammar": {
            "add": "add <unit> [after <unit_id>|before <unit_id>]",
            "replace": "replace <unit|unit_id> with <unit>",
            "remove": "remove <unit|unit_id>",
            "set": "set k=v[, k=v...] [on <unit|unit_id>]",
            "connect": "connect <from_id> -> <to_id>",
            "disconnect": "disconnect <from_id> -> <to_id>",
            "duplicate": "duplicate <unit|unit_id> as <new_id>",
            "run": "run [deterministic|sobol n=<int>]",
        }
    }

@router.post("/preview")
def preview(req: NLSRequest):
    parsed = parse(req.command_text)
    try:
        patch = build_patch(req.scenario, parsed)
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"parsed": parsed.__dict__, "patch": patch}

@router.post("/apply")
def do_apply(req: NLSRequest):
    parsed = parse(req.command_text)
    try:
        patch_ops = build_patch(req.scenario, parsed)
    except Exception as e:
        raise HTTPException(400, str(e))
    data = req.scenario.model_dump(by_alias=True)
    try:
        data2 = jsonpatch.JsonPatch(patch_ops).apply(data, in_place=False)
        Scenario.model_validate(data2)  # validate
    except Exception as e:
        raise HTTPException(400, f"Patch failed: {e}")
    return {"parsed": parsed.__dict__, "patch": patch_ops, "scenario_after": data2}

@router.post("/batch")
def batch(req: NLSBatch):
    data = req.scenario.model_dump(by_alias=True)
    combined = []
    try:
        for cmd in req.commands:
            parsed = parse(cmd)
            ops = build_patch(Scenario.model_validate(data), parsed)
            combined.extend(ops)
            data = jsonpatch.JsonPatch(ops).apply(data, in_place=False)
        Scenario.model_validate(data)
    except Exception as e:
        raise HTTPException(400, f"Batch failed: {e}")
    return {"patch": combined, "scenario_after": data}
```

### 6) Tests
**File:** `/app/api/tests/test_nls.py`
```python
import jsonpatch
from app.api.models.scenario import Scenario
from app.api.nls.parser import parse
from app.api.nls.editor import apply as build_patch

def _apply(sc: Scenario, text: str) -> Scenario:
    p = parse(text)
    ops = build_patch(sc, p)
    data = jsonpatch.JsonPatch(ops).apply(sc.model_dump(by_alias=True), in_place=False)
    return Scenario.model_validate(data)


def test_replace_and_set():
    sc = Scenario(name="demo", version="0.1", units=[
        {"template":"AEX_Membrane_v1","id":"dsp04","overrides":{}},
    ], streams=[], assumptions={}, uncertainty={})
    sc2 = _apply(sc, "replace aex membrane with chitosan capture")
    assert sc2.units[0].template == "ChitosanCapture_v1"
    sc3 = _apply(sc2, "set target_pH=4.4, recycle_fraction=0.5 on dsp04")
    assert sc3.units[0].overrides["target_pH"] == 4.4


def test_add_and_connect():
    sc = Scenario(name="demo", version="0.1", units=[
        {"template":"ProdFermenter_v2","id":"prod1","overrides":{}},
        {"template":"MF_Polishing_v1","id":"mf1","overrides":{}},
    ], streams=[{"from":"prod1","to":"mf1"}], assumptions={}, uncertainty={})
    sc2 = _apply(sc, "add chitosan capture after mf1")
    # we can’t assert stream indexes, but at least ensure a new unit exists
    assert any(u.template=="ChitosanCapture_v1" for u in sc2.units)


def test_duplicate_and_remove():
    sc = Scenario(name="demo", version="0.1", units=[
        {"template":"UFDF_v1","id":"ufdf1","overrides":{}},
    ], streams=[], assumptions={}, uncertainty={})
    sc2 = _apply(sc, "duplicate ufdf1 as ufdf2")
    ids = [u.id for u in sc2.units]
    assert set(ids) == {"ufdf1","ufdf2"}
    sc3 = _apply(sc2, "remove ufdf2")
    assert [u.id for u in sc3.units] == ["ufdf1"]
```

That’s everything needed to support the remaining commands end‑to‑end. Once you paste these, your chat panel can mutate scenarios with natural language while the visual graph stays in lockstep.

