from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_units():
    return [
        {"template": "SeedFermenter_v1", "category": "USP"},
        {"template": "ProdFermenter_v2", "category": "USP"},
        {"template": "DiskStack_v1", "category": "Primary Recovery"},
        {"template": "MF_Polishing_v1", "category": "Primary Recovery"},
        {"template": "AEX_Column_v1", "category": "DSP04"},
        {"template": "ChitosanCapture_v1", "category": "DSP04"},
        {"template": "UFDF_v1", "category": "Finishing"},
        {"template": "PreDry_TFF_v1", "category": "Finishing"},
        {"template": "SprayDry_v1", "category": "Finishing"},
    ]
