from pydantic import BaseModel, Field
from typing import Literal

DistName = Literal["uniform", "normal", "lognormal"]


class UncertaintySpec(BaseModel):
    dist: DistName
    # accept generic params; per-dist validation can be added later
    low: float | None = None
    high: float | None = None
    mu: float | None = None
    sigma: float | None = None
