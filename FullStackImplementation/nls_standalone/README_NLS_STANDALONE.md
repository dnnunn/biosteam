# NLS (Natural Language → Scenario) Standalone Drop-In

This archive contains a self-contained Natural Language interface for your BioSTEAM app.
It parses simple commands (add/replace/remove/set/connect/duplicate/run) and returns JSON-Patch
mutations against your `Scenario` model. It also ships a FastAPI router and tests.

## Files
- `app/api/nls/ontology.py` — synonyms for units/parameters
- `app/api/nls/parser.py`   — command grammar → Parsed intent
- `app/api/nls/editor.py`   — Parsed intent → JSON-Patch
- `app/api/routers/nls.py`  — `/nls/preview`, `/nls/apply`, `/nls/batch`, `/nls/help`
- `app/api/tests/test_nls.py` — basic tests

## Install
1) Copy these folders into your repo root (preserving paths).
2) Add dependency to API `pyproject.toml`:
   ```toml
   jsonpatch>=1.33
   ```
   (or `pip install jsonpatch` in your API env)
3) Wire router in `app/api/main.py`:
   ```python
   from .routers import nls
   app.include_router(nls.router)
   ```

## Try it
- Run API, then POST to `/nls/preview` with:
  ```json
  { "command_text": "replace aex membrane with chitosan capture", "scenario": { "...": "..." } }
  ```
- You’ll get a JSON-Patch; send `/nls/apply` to return the patched, Pydantic-validated scenario.

## Notes
- Stream rewiring for `add before/after` inserts the new unit between existing links.
- `duplicate` copies overrides but doesn’t auto-connect (to avoid cycles).
- Extend `ontology.py` with your preferred synonyms, units, and parameter nicknames.
