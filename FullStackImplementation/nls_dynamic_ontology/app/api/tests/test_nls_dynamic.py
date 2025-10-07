# /app/api/tests/test_nls_dynamic.py
import jsonpatch, pathlib
from app.api.models.scenario import Scenario
from app.api.nls.ontology_loader import load_from_specs
from app.api.nls.parser import parse
from app.api.nls.editor import apply as build_patch

SPEC_DIR = pathlib.Path("app/units/specs")

def _apply(sc: Scenario, cmd: str):
    onto = load_from_specs(SPEC_DIR)
    p = parse(cmd, onto)
    ops = build_patch(sc, p)
    data = jsonpatch.JsonPatch(ops).apply(sc.model_dump(by_alias=True), in_place=False)
    return Scenario.model_validate(data)

def test_swap_and_set():
    sc = Scenario(name="demo", version="0.1", units=[
        {"template":"AEX_Membrane_v1","id":"dsp04","overrides":{}},
    ], streams=[], assumptions={}, uncertainty={})
    sc2 = _apply(sc, "replace aex membrane with chitosan capture")
    assert sc2.units[0].template == "ChitosanCapture_v1"
    sc3 = _apply(sc2, "set pH=4.4, recycle=0.5 on dsp04")
    assert sc3.units[0].overrides["target_pH"] == 4.4
