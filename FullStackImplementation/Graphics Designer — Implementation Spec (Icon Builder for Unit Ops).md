# Graphics Designer — Implementation Spec (Icon Builder for Unit Ops)

## 1) Purpose

An in-app editor for creating and managing **vector icons** (SVG) and **port layouts** for each process unit template (USP/DSP/utilities). Icons are stored as a small JSON schema (source of truth) and compiled to SVG for the flowsheet UI. Ports drive node handles (snap points) in the graph.

------

## 2) Package layout (additions)

```
/app
  /api
    /routers
      icons.py                 # REST for icon CRUD & compile
    /models
      icon.py                  # Pydantic models & JSON Schema
    /storage
      storage_fs.py            # (already exists) add icons folder helpers
  /ui
    /app/designer/icons/       # route for the icon designer
      page.tsx
      [template]/page.tsx
    /src/components/designer/  # reusable editor widgets
      IconStage.tsx
      LayersPanel.tsx
      PortEditor.tsx
      OverlayPicker.tsx
      Toolbar.tsx
    /src/lib/icons/
      renderer.ts              # JSON→<svg> compiler
      api.ts                   # fetch helpers for icons API
/public/icons/compiled/        # cached compiled SVGs (optional)
```

------

## 3) Data model

### 3.1 Pydantic models (`/app/api/models/icon.py`)

```
from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional, Tuple, Dict

LayerType = Literal["line","rect","ellipse","path","polyline","text"]
PortSide = Literal["left","right","top","bottom"]

class Layer(BaseModel):
    id: str
    type: LayerType
    # common
    stroke_width: float | None = None
    opacity: float | None = None
    # geometry (subset per type)
    x: float | None = None
    y: float | None = None
    w: float | None = None
    h: float | None = None
    rx: float | None = None
    ry: float | None = None
    x1: float | None = None
    y1: float | None = None
    x2: float | None = None
    y2: float | None = None
    d: str | None = None            # path data
    points: List[Tuple[float,float]] | None = None  # polyline
    text: str | None = None
    font_size: float | None = None

class Port(BaseModel):
    id: str
    pos: Tuple[float,float]
    side: PortSide
    label: Optional[str] = None

class Overlay(BaseModel):
    glyph: Literal["droplet","fan","spark","heat","cool","powder","valve"]
    pos: Tuple[float,float]
    size: float | None = None

class IconSpec(BaseModel):
    template: str                     # e.g., "AEX_Membrane_v1"
    name: str
    viewBox: Tuple[int,int,int,int] = (0,0,24,24)
    strokes: float = 1.8
    layers: List[Layer] = Field(default_factory=list)
    ports: List[Port] = Field(default_factory=list)
    overlays: List[Overlay] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    version: int = 1                  # bump on breaking schema changes

    @field_validator("ports")
    @classmethod
    def require_unique_port_ids(cls, ports):
        ids = [p.id for p in ports]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate port ids")
        return ports
```

### 3.2 JSON Schema (auto-exposed)

Expose at `/icons/schema` via `IconSpec.model_json_schema()` so the UI can validate client-side.

------

## 4) API (OpenAPI excerpt, `FastAPI`)

### 4.1 Router (`/app/api/routers/icons.py`)

```
from fastapi import APIRouter, HTTPException
from ..models.icon import IconSpec
from ..storage.storage_fs import icons_root
from pathlib import Path
import json

router = APIRouter(prefix="/icons", tags=["icons"])

def _icon_path(template: str) -> Path:
    d = icons_root() / template
    d.mkdir(parents=True, exist_ok=True)
    return d

@router.get("/schema")
def schema():
    return IconSpec.model_json_schema()

@router.get("")
def list_icons():
    root = icons_root()
    items = []
    for p in root.glob("*/icon.json"):
        data = json.loads(p.read_text())
        items.append({"template": data["template"], "name": data.get("name",""), "path": str(p)})
    return items

@router.get("/{template}")
def get_icon(template: str):
    p = _icon_path(template) / "icon.json"
    if not p.exists(): raise HTTPException(404, "not found")
    return json.loads(p.read_text())

@router.post("/{template}")
def upsert_icon(template: str, spec: IconSpec):
    if spec.template != template:
        raise HTTPException(400, "template mismatch")
    p = _icon_path(template) / "icon.json"
    p.write_text(spec.model_dump_json(indent=2))
    return {"status":"ok"}

@router.get("/{template}/svg")
def get_svg(template: str):
    # compile JSON → SVG string
    p = _icon_path(template) / "icon.json"
    if not p.exists(): raise HTTPException(404, "not found")
    data = json.loads(p.read_text())
    svg = compile_svg(data)  # implement in this module or import from a utility
    return {"svg": svg}
```

### 4.2 Storage helper (`/app/api/storage/storage_fs.py`)

```
from pathlib import Path

def icons_root() -> Path:
    return Path("icons").resolve()  # new top-level folder: /icons/<template>/icon.json
```

------

## 5) Renderer (UI) — compile JSON → `<svg>` (`/app/ui/src/lib/icons/renderer.ts`)

```
export type Layer =
  | ({ type: "rect"; id: string; x: number; y: number; w: number; h: number; rx?: number; ry?: number; stroke_width?: number; opacity?: number })
  | ({ type: "line"; id: string; x1: number; y1: number; x2: number; y2: number; stroke_width?: number; opacity?: number })
  | ({ type: "ellipse"; id: string; x: number; y: number; w: number; h: number; stroke_width?: number; opacity?: number })
  | ({ type: "polyline"; id: string; points: [number,number][]; stroke_width?: number; opacity?: number })
  | ({ type: "path"; id: string; d: string; stroke_width?: number; opacity?: number })
  | ({ type: "text"; id: string; x: number; y: number; text: string; font_size?: number; opacity?: number });

export interface Port { id: string; pos: [number,number]; side: "left"|"right"|"top"|"bottom"; label?: string }
export interface IconSpec {
  template: string; name: string; viewBox: [number,number,number,number];
  strokes: number; layers: Layer[]; ports: Port[];
  overlays: { glyph: "droplet"|"fan"|"spark"|"heat"|"cool"|"powder"|"valve"; pos: [number,number]; size?: number }[];
  tags: string[]; version: number;
}

// Returns raw SVG string (outline stroke = currentColor)
export function renderIcon(spec: IconSpec): string {
  const [x,y,w,h] = spec.viewBox;
  const sw = (v?: number) => (v ?? spec.strokes);
  const esc = (s: string) => s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  const parts: string[] = [];
  for (const L of spec.layers) {
    if (L.type === "rect") parts.push(`<rect x="${L.x}" y="${L.y}" width="${L.w}" height="${L.h}" rx="${L.rx??0}" ry="${L.ry??0}" stroke-width="${sw(L.stroke_width)}" opacity="${L.opacity??1}" />`);
    else if (L.type === "line") parts.push(`<line x1="${L.x1}" y1="${L.y1}" x2="${L.x2}" y2="${L.y2}" stroke-width="${sw(L.stroke_width)}" opacity="${L.opacity??1}" />`);
    else if (L.type === "ellipse") parts.push(`<ellipse cx="${L.x}" cy="${L.y}" rx="${L.w/2}" ry="${L.h/2}" stroke-width="${sw(L.stroke_width)}" opacity="${L.opacity??1}" />`);
    else if (L.type === "polyline") parts.push(`<polyline points="${L.points.map(p=>p.join(",")).join(" ")}" fill="none" stroke-width="${sw(L.stroke_width)}" opacity="${L.opacity??1}" />`);
    else if (L.type === "path") parts.push(`<path d="${esc(L.d||"")}" stroke-width="${sw(L.stroke_width)}" fill="none" opacity="${L.opacity??1}" />`);
    else if (L.type === "text") parts.push(`<text x="${L.x}" y="${L.y}" font-size="${L.font_size??8}" fill="currentColor" stroke="none" opacity="${L.opacity??1}">${esc(L.text||"")}</text>`);
  }
  // optional overlays (simple glyphs)
  for (const O of spec.overlays) {
    if (O.glyph === "droplet") parts.push(`<path d="M12 6c-3 4-4 5-4 7a4 4 0 0 0 8 0c0-2-1-3-4-7z" fill="none" />`);
    if (O.glyph === "fan") parts.push(`<path d="M12 8a4 4 0 1 1-4 4" fill="none" />`);
    if (O.glyph === "spark") parts.push(`<path d="M12 5v14M5 12h14M7 7l10 10M17 7L7 17" opacity="0.3" />`);
    // …add others similarly
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${x} ${y} ${w} ${h}" width="${w}" height="${h}" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round">${parts.join("")}</svg>`;
}
```

------

## 6) Designer UI contract

### 6.1 Route: `/designer/icons`

- Left **Toolbar**: select, line, rect, ellipse, polyline, path, text, port, overlay, transform, delete.
- Center **IconStage** (`react-konva`): grid 8px, snap, drag, scale, rotate.
- Right **Inspector**: layer props (geometry/opacity/stroke width), port id/side, overlay glyph/size, global strokes/viewBox.
- Bottom **Assign to template** (dropdown fetching `/units/library`), **Save**, **Preview**, **Export SVG**.

### 6.2 Component interfaces

```
// IconStage.tsx
export interface IconStageProps {
  spec: IconSpec;
  onChange: (next: IconSpec) => void;
  grid?: number; // 8 default
}

// LayersPanel.tsx
export interface LayersPanelProps {
  layers: Layer[];
  activeId?: string;
  onReorder: (ids: string[]) => void;
  onSelect: (id: string) => void;
  onDuplicate: (id: string) => void;
  onDelete: (id: string) => void;
}
```

------

## 7) Flowsheet integration

### 7.1 Node renderer (React Flow)

```
import { renderIcon } from "@/src/lib/icons/renderer";
function UnitNode({ data }: any) {
  const svg = data.iconSpec ? renderIcon(data.iconSpec) : null;
  return (
    <div className="rounded-xl p-2 border shadow-sm" style={{ color: data.color }}>
      {svg ? <span dangerouslySetInnerHTML={{ __html: svg }} /> : <div className="w-6 h-6" />}
      <div className="text-xs mt-1">{data.label}</div>
    </div>
  );
}
```

### 7.2 Ports → Handles

- For each `spec.ports`, add `Handle` with `position` derived from `side` and `pos` normalized to node width/height.

------

## 8) Persistence & caching

- **Source of truth**: `/icons/<template>/icon.json` (the `IconSpec`).
- **Optional cache**: compiled SVG at `/public/icons/compiled/<template>.svg` for fast SSR.
- API `GET /icons/{template}/svg` compiles on demand; UI can store result in SW cache.

------

## 9) Theming & accessibility

- Icons use `stroke="currentColor"`.
- Category colors (USP/DSP/Finishing/Utilities) applied via CSS classes on the node wrapper.
- Provide `aria-label` from `spec.name` and tooltips for ports (use `port.label`).

------

## 10) Validation rules

- Unique `port.id` per icon.
- Ports must lie **inside** viewBox (`0 ≤ x ≤ w`, `0 ≤ y ≤ h` after translating to local coords).
- For templates with required ports, validate on save (e.g., AEX has exactly 1 in, 1 out).

------

## 11) Versioning & migration

- `IconSpec.version` starts at `1`.
- If schema evolves: write a tiny migration in `/app/api/routers/icons.py` that reads old JSON and up-converts.

------

## 12) Example specs

### 12.1 AEX Membrane (starter)

```
{
  "template": "AEX_Membrane_v1",
  "name": "AEX Membrane (grid)",
  "viewBox": [0,0,24,24],
  "strokes": 1.8,
  "layers": [
    {"id":"frame","type":"rect","x":4.5,"y":4.5,"w":15,"h":15,"rx":2},
    {"id":"bar1","type":"line","x1":7,"y1":8,"x2":17,"y2":8},
    {"id":"bar2","type":"line","x1":7,"y1":12,"x2":17,"y2":12},
    {"id":"bar3","type":"line","x1":7,"y1":16,"x2":17,"y2":16}
  ],
  "ports": [
    {"id":"in","pos":[2,12],"side":"left","label":"feed"},
    {"id":"out","pos":[22,12],"side":"right","label":"permeate"}
  ],
  "overlays":[{"glyph":"droplet","pos":[18.5,7]}],
  "tags":["DSP","membrane","anion-exchange"],
  "version":1
}
```

### 12.2 Chitosan (starter)

```
{
  "template":"ChitosanCapture_v1",
  "name":"Chitosan capture",
  "viewBox":[0,0,24,24],
  "strokes":1.8,
  "layers":[
    {"id":"vessel","type":"rect","x":5,"y":6,"w":14,"h":12,"rx":2},
    {"id":"lid","type":"line","x1":8,"y1":6,"x2":16,"y2":6},
    {"id":"mesh1","type":"polyline","points":[[7,14],[9,12],[11,14],[13,12],[15,14]]}
  ],
  "ports":[
    {"id":"in","pos":[2,12],"side":"left"},
    {"id":"out","pos":[22,12],"side":"right"}
  ],
  "overlays":[{"glyph":"powder","pos":[18,8]}],
  "tags":["DSP","polymer"],
  "version":1
}
```

------

## 13) Acceptance criteria (MVP)

1. **CRUD**: `GET /icons`, `GET /icons/{template}`, `POST /icons/{template}`, `GET /icons/{template}/svg` working with validation and file storage.
2. **Schema**: `GET /icons/schema` returns a JSON Schema you can feed into client validation.
3. **Designer**: `/designer/icons` lets a user draw/edit layers, place ports, preview SVG, assign to a template, and save.
4. **Flowsheet**: nodes render from stored `IconSpec` (or compiled SVG) and expose handles at port positions; edges snap.
5. **Theming**: nodes adopt `currentColor`, with per-category color classes.
6. **Tests**: unit tests for icon validator (ports unique & in bounds) and router round-trip save/load.

------

## 14) Stretch goals (post-MVP)

- **SVG import**: map `<path id="layer-...">` and `<circle id="port-...">` into layers/ports.
- **Parametric overlays**: simple rules: show certain layers when a parameter threshold is met (e.g., `capacity_g_m2 > 450`).
- **Batch export**: compile all icons to `/public/icons/compiled/*.svg`.
- **Design tokens**: CSS variables for brand palette; dark/light themes.

------

## 15) Quick glue to mount in API

```
# app/api/main.py
from .routers import icons  # new
app.include_router(icons.router)
```