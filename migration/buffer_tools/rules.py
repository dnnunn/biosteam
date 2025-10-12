from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BestPracticeRules:
    max_tmp_bar: float = 1.5
    antifoam_flux_derate_fraction: float = 0.25

    def apply_flux_derate(self, flux_lmh: float, antifoam_flag: bool) -> float:
        if not antifoam_flag:
            return float(flux_lmh)
        try:
            flux = float(flux_lmh)
        except (TypeError, ValueError):
            return 0.0
        return max(flux * (1.0 - self.antifoam_flux_derate_fraction), 0.0)

