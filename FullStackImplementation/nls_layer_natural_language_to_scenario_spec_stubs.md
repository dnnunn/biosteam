# Natural‑Language → Scenario (NLS) Layer
A thin command grammar + parser that turns plain English edits into validated scenario patches. Edits round‑trip through the same Pydantic `Scenario` model used by the UI graph editor.

## Goals
- Non‑experts propose process variants with short commands.
- Changes are typed, validated, reversible, auditable.
- One mutation path for chat, UI, and CLI.

## Concepts
- **Command**: add/replace/remove/tune/connect/run/duplicate/compare.
- **Resolver**: maps fuzzy terms ("membrane aex", "anion exchange") → canonical templates (e.g., `AEX_Membrane_v1`).
- **Editor**: applies commands to a `Scenario` and returns an RFC‑6902 JSON Patch array.

## API (FastAPI)
- `POST /nls/preview` → `{command_text, scenario}` → `{patch, summary}` (no save).
- `POST /nls/apply` → `{command_text, scenario}` → `{scenario_after, patch, summary}`.
- `POST /nls/batch` → `{commands[], scenario}` → transactional apply; combined patch.
- `GET  /nls/help` → lists grammar, synonyms, unit templates, tunable parameters.

## Minimal Command Grammar
```
<cmd> ::= add <unit> [after <unit_id>|before <unit_id>|at <position>]
        | replace <unit|unit_id> with <unit>
        | remove <unit|unit_id>
        | set <param>[, <param>...] [on <unit|unit_id>]
        | connect <from_id> -> <to_id>
        | disconnect <from_id> -> <to_id>
        | duplicate <unit|unit_id> as <new_id>
        | run [deterministic|sobol n=<int>]

<unit> ::= canonical name or synonym (e.g., "aex membrane", "chitosan capture")
<param> ::= <name> '=' <value>  (e.g., titer_g_L=6, target_pH=4.4)
```

**Examples**
- `replace aex membrane with chitosan capture`
- `set titer_g_L=8, time_h=60 on prod1`
- `add ufdf after dsp04`
- `connect mf1 -> dsp04`
- `remove mf1`
- `run sobol n=512`

## Resolver (Synonyms/Ontology)
**File:** `/app/api/nls/ontology.py`
```python
UNIT_SYNONYMS = {
  "aex membrane": "AEX_Membrane_v1",
  "membrane aex": "AEX_Membrane_v1",
  "aex column": "AEX_Column_v1",
  "column aex": "AEX_Column_v1",
  "chitosan": "ChitosanCapture_v1",
  "chitosan capture": "ChitosanCapture_v1",
  "ufdf": "UFDF_v1",
  "spray dryer": "SprayDry_v1",
}

PARAM_SYNONYMS = {
  "titer": "titer_g_L",
  "pH": "target_pH",
  "polymer %": "polymer_pct_wv",
  "recycle": "recycle_fraction",
}
```

## Parser
**File:** `/app/api/nls/parser.py`
```python
import re
from dataclasses import dataclass
from typing import Dict, Any
from .ontology import UNIT_SYNONYMS, PARAM_SYNONYMS

@dataclass
class Parsed:
    type: str
    args: Dict[str, Any]

_ID = r"[A-Za-z0-9_\-]+"
_NUM = r"-?[0-9]+(?:\.[0-9]+)?"

RE_REPLACE = re.compile(r"^replace\s+(.+?)\s+with\s+(.+)$", re.I)
RE_ADD     = re.compile(rf"^add\s+(.+?)(?:\s+after\s+({_ID})|\s+before\s+({_ID})|\s+at\s+({_ID}))?$", re.I)
RE_REMOVE  = re.compile(r"^remove\s+(.+)$", re.I)
RE_CONNECT = re.compile(rf"^connect\s+({_ID})\s*->\s*({_ID})$", re.I)
RE_DISCONN = re.compile(rf"^disconnect\s+({_ID})\s*->\s*({_ID})$", re.I)
RE_DUP     = re.compile(rf"^duplicate\s+({_ID}|.+?)\s+as\s+({_ID})$", re.I)
RE_SET     = re.compile(rf"^set\s+(.+?)(?:\s+on\s+({_ID}|.+))?$", re.I)
RE_RUN     = re.compile(r"^run(?:\s+(deterministic|sobol))?(?:\s+n=([0-9]+))?$", re.I)


def resolve_unit(name: str) -> str:
    key = name.strip().lower()
    return UNIT_SYNONYMS.get(key, key)

def resolve_param(name: str) -> str:
    key = name.strip()
    return PARAM_SYNONYMS.get(key, key)


def parse_kv_list(s: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for part in re.split(r"\s*,\s*", s.strip()):
        if not part or "=" not in part:
            continue
        k, v = map(str.strip, part.split("=", 1))
        k = resolve_param(k)
        if v.lower() in {"true","false"}:
            out[k] = (v.lower()=="true")
        elif re.fullmatch(_NUM, v):
            out[k] = float(v)
        else:
            out[k] = v
    return out


def parse(text: str) -> Parsed:
    t = text.strip()
    m = RE_REPLACE.match(t)
    if m:
        return Parsed("replace", {"source": resolve_unit(m.group(1)), "dest": resolve_unit(m.group(2))})
    m = RE_ADD.match(t)
    if m:
        return Parsed("add", {"unit": resolve_unit(m.group(1)), "after": m.group(2), "before": m.group(3), "at": m.group(4)})
    m = RE_REMOVE.match(t)
    if m:
        return Parsed("remove", {"target": m.group(1).strip()})
    m = RE_CONNECT.match(t)
    if m:
        return Parsed("connect", {"from": m.group(1), "to": m.group(2)})
    m = RE_DISCONN.match(t)
    if m:
        return Parsed("disconnect", {"from": m.group(1), "to": m.group(2)})
    m = RE_DUP.match(t)
    if m:
        return Parsed("duplicate", {"target": m.group(1), "new_id": m.group(2)})
    m = RE_SET.match(t)
    if m:
        return Parsed("set", {"params": parse_kv_list(m.group(1)), "scope": m.group(2)})
    m = RE_RUN.match(t)
    if m:
        return Parsed("run", {"mode": (m.group(1) or "deterministic"), "n": int(m.group(2) or 0)})
    return Parsed("unknown", {"raw": t})
```

## Editor (Patch generator)
**File:** `/app/api/nls/editor.py`
```python
from copy import deepcopy
from typing import Dict, Any, List
from ..models.scenario import Scenario
from .parser import Parsed

# JSON Pointer helpers for RFC-6902

def _unit_index(sc: Scenario, unit_id: str) -> int:
    for i, u in enumerate(sc.units):
        if u.id == unit_id:
            return i
    raise KeyError(unit_id)


def replace_unit(sc: Scenario, template_from: str | None, template_to: str) -> List[dict]:
    sc2 = deepcopy(sc)
    target_idx = None
    for i, u in enumerate(sc2.units):
        if u.id == template_from or u.template == template_from:
            target_idx = i
            break
    if target_idx is None:
        raise KeyError(f"Unit not found: {template_from}")
    return [{"op": "replace", "path": f"/units/{target_idx}/template", "value": template_to}]


def set_params(sc: Scenario, params: Dict[str, Any], scope: str | None) -> List[dict]:
    sc2 = deepcopy(sc)
    patches: List[dict] = []
    targets: List[int] = []
    if scope:
        try:
            targets = [_unit_index(sc2, scope)]
        except KeyError:
            for i, u in enumerate(sc2.units):
                if u.template.lower() == (scope or "").lower():
                    targets = [i]
                    break
    else:
        targets = [0]
    for idx in targets:
        for k, v in params.items():
            patches.append({"op": "add", "path": f"/units/{idx}/overrides/{k}", "value": v})
    return patches


def apply(sc: Scenario, p: Parsed) -> List[dict]:
    if p.type == "replace":
        return replace_unit(sc, p.args["source"], p.args["dest"])
    if p.type == "set":
        return set_params(sc, p.args["params"], p.args.get("scope"))
    # TODO: implement add/remove/connect/duplicate
    raise NotImplementedError(p.type)
```

## Router (FastAPI)
**File:** `/app/api/routers/nls.py`
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..models.scenario import Scenario
from ..nls.parser import parse
from ..nls.editor import apply

router = APIRouter(prefix="/nls", tags=["nls"])

class NLSRequest(BaseModel):
    command_text: str
    scenario: Scenario

@router.post("/preview")
def preview(req: NLSRequest):
    parsed = parse(req.command_text)
    try:
        patch = apply(req.scenario, parsed)
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"parsed": parsed.__dict__, "patch": patch}

@router.post("/apply")
def do_apply(req: NLSRequest):
    parsed = parse(req.command_text)
    try:
        patch = apply(req.scenario, parsed)
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"parsed": parsed.__dict__, "patch": patch}
```

## UI Integration (sketch)
- Chat panel posts to `/nls/preview` while typing and renders a human summary.
- On **Apply**, call `/nls/apply`, then update the in‑memory scenario and graph.
- Keep a command history (undo/redo by replaying inverse patches).

## Validation & Safety
- Parser constrained to known templates/params via ontology.
- Pydantic validation after patch application; errors surfaced in chat.
- Stream connectivity checks before commit (no orphan nodes).

## Tests
- Parser unit tests → `Parsed` objects.
- Editor tests assert RFC‑6902 patches and validate updated scenarios.

## Future
- Replace regex with PEG grammar.
- Optional LLM assist for free‑form language; still emit the same `Parsed` schema.
- Internationalization via extended ontology.

