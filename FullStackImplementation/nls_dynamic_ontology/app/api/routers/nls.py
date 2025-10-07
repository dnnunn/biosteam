# /app/api/routers/nls.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..models.scenario import Scenario
from ..nls.ontology_loader import load_from_specs
from ..nls.parser import parse
from ..nls.editor import apply as build_patch
import jsonpatch
from pathlib import Path

router = APIRouter(prefix="/nls", tags=["nls"])

SPEC_DIR = Path("app/units/specs")

class NLSRequest(BaseModel):
    command_text: str
    scenario: Scenario

class NLSBatch(BaseModel):
    commands: list[str]
    scenario: Scenario

def _onto():
    return load_from_specs(SPEC_DIR)

@router.get("/help")
def help():
    onto = _onto()
    return {
        "units": sorted(set(onto.unit_map.values())),
        "unit_synonyms": onto.unit_map,
        "param_synonyms": onto.param_map,
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
    onto = _onto()
    parsed = parse(req.command_text, onto)
    try:
        patch = build_patch(req.scenario, parsed)
    except Exception as e:
        raise HTTPException(400, str(e))
    return {"parsed": parsed.__dict__, "patch": patch}

@router.post("/apply")
def do_apply(req: NLSRequest):
    onto = _onto()
    parsed = parse(req.command_text, onto)
    try:
        patch_ops = build_patch(req.scenario, parsed)
    except Exception as e:
        raise HTTPException(400, str(e))
    data = req.scenario.model_dump(by_alias=True)
    try:
        data2 = jsonpatch.JsonPatch(patch_ops).apply(data, in_place=False)
        Scenario.model_validate(data2)
    except Exception as e:
        raise HTTPException(400, f"Patch failed: {e}")
    return {"parsed": parsed.__dict__, "patch": patch_ops, "scenario_after": data2}

@router.post("/batch")
def batch(req: NLSBatch):
    onto = _onto()
    data = req.scenario.model_dump(by_alias=True)
    combined = []
    try:
        for cmd in req.commands:
            parsed = parse(cmd, onto)
            ops = build_patch(Scenario.model_validate(data), parsed)
            combined.extend(ops)
            data = jsonpatch.JsonPatch(ops).apply(data, in_place=False)
        Scenario.model_validate(data)
    except Exception as e:
        raise HTTPException(400, f"Batch failed: {e}")
    return {"patch": combined, "scenario_after": data}
