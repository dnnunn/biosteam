# NLS Dynamic Ontology — USP01-03 & DSP01-05
This package turns plain-language commands into scenario mutations, but — crucially —
it **loads unit/parameter synonyms from YAML specs** under `app/units/specs`. That means you can
cover *all* your USP01–USP03 and DSP01–DSP05 variations by editing YAML, without touching code.

## Where to put your specs
Drop your “Biosteam BD Module Specs” YAMLs into `app/units/specs/`. Each file should look like:
```yaml
template: AEX_Membrane_v1
synonyms: ["aex membrane","membrane aex","anion exchange membrane"]
parameters:
  - key: membrane_area_m2
    synonyms: ["area","membrane area"]
  - key: flux_L_m2_h
    synonyms: ["flux"]
```

Sample specs for USP01–03 and DSP01–05 are included — replace/extend with your real ones.

## Hooking it up
- Mount the router in your FastAPI app:
  ```python
  from app.api.routers import nls
  app.include_router(nls.router)
  ```
- Ensure `jsonpatch` is installed.

## Using the API
- `POST /nls/preview` with `{ "command_text": "...", "scenario": { ... } }`
- `POST /nls/apply` to receive the patched, validated scenario
- `GET /nls/help` to see the discovered templates + synonyms from your YAMLs

## Examples
- `replace aex membrane with chitosan capture`
- `add ufdf after dsp04`
- `set titer=8 on prod1`
- `connect mf1 -> dsp04`

## Why dynamic?
Your unit library evolves. Keeping synonyms in YAML avoids code churn and lets R&D folks update
language mappings directly from the module spec docs.
