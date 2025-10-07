\
    # /app/api/tests/test_nls.py
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
