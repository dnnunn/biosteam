from pydantic import BaseModel, Field
from typing import Dict, List
from .common import UncertaintySpec


class UnitInstance(BaseModel):
    template: str
    id: str
    overrides: Dict[str, float | int | str | bool] = Field(default_factory=dict)


class StreamLink(BaseModel):
    from_: str = Field(alias="from")
    to: str


class Scenario(BaseModel):
    name: str
    version: str
    thermo_package: str | None = None
    units: List[UnitInstance]
    streams: List[StreamLink]
    assumptions: Dict[str, float | int | str] = Field(default_factory=dict)
    uncertainty: Dict[str, UncertaintySpec] = Field(default_factory=dict)

    class Config:
        populate_by_name = True
