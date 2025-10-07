\
    # /app/api/routers/nls.py
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
            Scenario.model_validate(data2)
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
