\
    # /app/api/nls/editor.py
    from copy import deepcopy
    from typing import Dict, Any, List
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
        base = unit_template.split("_")[0].lower()
        new_id = _ensure_unit_id(sc2, base)
        patches: List[dict] = []
        patches.append({"op": "add", "path": f"/units/-", "value": {"template": unit_template, "id": new_id, "overrides": {}}})
        if after:
            out_links = [sc2.streams[i] for i in _find_links(sc2, src=after)]
            for link in out_links:
                ridx = _find_links(sc2, src=after, dst=link.to)[0]
                patches.append({"op": "remove", "path": f"/streams/{ridx}"})
                patches.append({"op": "add", "path": "/streams/-", "value": {"from": after, "to": new_id}})
                patches.append({"op": "add", "path": "/streams/-", "value": {"from": new_id, "to": link.to}})
        elif before:
            in_links = [sc2.streams[i] for i in _find_links(sc2, dst=before)]
            for link in in_links:
                ridx = _find_links(sc2, src=link.from_, dst=before)[0]
                patches.append({"op": "remove", "path": f"/streams/{ridx}"})
                patches.append({"op": "add", "path": "/streams/-", "value": {"from": link.from_, "to": new_id}})
                patches.append({"op": "add", "path": "/streams/-", "value": {"from": new_id, "to": before}})
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
        for i in sorted(_find_links(sc2, src=unit_id) + _find_links(sc2, dst=unit_id), reverse=True):
            patches.append({"op": "remove", "path": f"/streams/{i}"})
        patches.append({"op": "remove", "path": f"/units/{idx}"})
        return patches

    def connect_units(sc: Scenario, from_id: str, to_id: str) -> List[dict]:
        for s in sc.streams:
            if s.from_ == from_id and s.to == to_id:
                return []
        return [{"op": "add", "path": "/streams/-", "value": {"from": from_id, "to": to_id}}]

    def disconnect_units(sc: Scenario, from_id: str, to_id: str) -> List[dict]:
        idxs = _find_links(sc, src=from_id, dst=to_id)
        if not idxs:
            return []
        return [{"op": "remove", "path": f"/streams/{idxs[-1]}"}]

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
