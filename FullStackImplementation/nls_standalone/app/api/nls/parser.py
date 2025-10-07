\
    # /app/api/nls/parser.py
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
