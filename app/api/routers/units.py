from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_units():
    # TODO: real registry dump; for now return placeholders
    return [
        {"template": "SeedFermenter_v1", "category": "USP"},
        {"template": "ProdFermenter_v2", "category": "USP"},
        {"template": "DiskStack_v1", "category": "DSP"},
        {"template": "MF_Polishing_v1", "category": "DSP"},
        {"template": "AEX_membrane_v1", "category": "DSP"},
        {"template": "UFDF_v1", "category": "DSP"},
        {"template": "SprayDry_v1", "category": "Formulation"},
    ]
