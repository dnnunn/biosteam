"""Compatibility shims to smooth over minor API differences at runtime.

Applied on import by engine modules used in tests.
"""
from __future__ import annotations

def _patch_thermosteam_init_indexer() -> None:
    try:
        import thermosteam as tmo
    except Exception:
        return

    Stream = getattr(tmo, "Stream", None)
    if Stream is None:
        return

    orig = getattr(Stream, "_init_indexer", None)
    if not callable(orig):
        return

    # Avoid double‑patching
    if getattr(orig, "__compat_patched__", False):
        return

    def _init_indexer_compat(self, indexer, phase, chemicals, flow):
        # Some releases call len(flow) without guarding None
        if flow is None:
            flow = []
        return orig(self, indexer, phase, chemicals, flow)

    # Mark the wrapper to prevent re‑wrapping
    setattr(_init_indexer_compat, "__compat_patched__", True)
    Stream._init_indexer = _init_indexer_compat  # type: ignore[attr-defined]


def apply_all() -> None:
    _patch_thermosteam_init_indexer()


# Apply on import
apply_all()

