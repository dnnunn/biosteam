"""Lightweight BioSTEAM units used by the scenario engine.

These are deliberately simple so we can execute end-to-end simulations
without the full migration stack. Each unit consumes a single inlet stream
and produces a single outlet stream while tracking a configurable yield and
utility demand. The lost mass is routed to a ``Waste`` pseudo-component so
mass balances remain consistent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

import biosteam as bst


@dataclass
class UnitMetadata:
    """Metadata captured for KPI post-processing."""

    template: str
    category: str
    defaults: Dict[str, float | int | str | bool] = field(default_factory=dict)


class ScenarioUnit(bst.Unit):
    """Single-in/single-out unit with a simple yield model."""

    _N_ins = 1
    _N_outs = 1
    _ins_size_is_fixed = False
    _outs_size_is_fixed = False
    line = "ScenarioUnit"

    def __init__(
        self,
        ID: str,
        *,
        template: str,
        category: str,
        yield_fraction: float = 1.0,
        power_kW: float = 0.0,
        residence_time_h: float | None = None,
        metadata_defaults: Dict[str, float | int | str | bool] | None = None,
    ) -> None:
        super().__init__(ID)
        self.yield_fraction = max(float(yield_fraction), 0.0)
        self.power_kW = float(power_kW)
        self.residence_time_h = residence_time_h
        self.metadata = UnitMetadata(
            template=template,
            category=category,
            defaults=dict(metadata_defaults or {}),
        )

    def _run(self) -> None:
        feed = self.ins[0]
        product = self.outs[0]
        product.copy_like(feed)

        product_component = "Osteopontin"
        input_product = 0.0

        try:
            input_product = float(feed.imass["Osteopontin"])
        except Exception:
            try:
                input_product = float(feed.imass["Product"])
                product_component = "Product"
            except Exception:
                input_product = 0.0

        produced = input_product * self.yield_fraction
        produced = max(produced, 0.0)
        loss = max(input_product - produced, 0.0)

        product.imass["Osteopontin"] = produced
        if product_component != "Osteopontin":
            product.imass[product_component] = produced

        if loss > 0.0:
            try:
                product.imass["Waste"] += loss
            except Exception:
                try:
                    product.imass["Water"] += loss
                except Exception:
                    product.imass["Water"] = loss

    # Convenience hooks for KPI calculations
    @property
    def metadata_dict(self) -> Dict[str, object]:
        data = {
            "template": self.metadata.template,
            "category": self.metadata.category,
            "yield_fraction": self.yield_fraction,
            "power_kW": self.power_kW,
        }
        data.update(self.metadata.defaults)
        if self.residence_time_h is not None:
            data["residence_time_h"] = self.residence_time_h
        return data
