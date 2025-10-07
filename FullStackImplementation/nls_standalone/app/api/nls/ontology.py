# /app/api/nls/ontology.py
# Synonyms for units and parameters used by the NLS parser.
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
