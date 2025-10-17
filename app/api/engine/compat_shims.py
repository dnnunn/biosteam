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

    import inspect

    sig = inspect.signature(orig)
    param_names = [p.name for p in list(sig.parameters.values())[1:]]  # skip self

    def _init_indexer_compat(self, *args, **kwargs):
        bound = sig.bind_partial(self, *args, **kwargs)
        # Try to coerce any parameter named 'flow' to [] if None
        if 'flow' in bound.arguments and bound.arguments['flow'] is None:
            bound.arguments['flow'] = []
        else:
            # Some versions positionally pass 'flow' (first arg after self) or use indexer/phase/... ordering
            if len(bound.arguments) < len(sig.parameters):
                # Rebuild args list to inspect positional slot for 'flow'
                pos_args = list(args)
                # Attempt to locate 'flow' positionally
                if 'flow' in param_names:
                    flow_idx = param_names.index('flow')
                    if flow_idx < len(pos_args):
                        if pos_args[flow_idx] is None:
                            pos_args[flow_idx] = []
                        return orig(self, *pos_args, **kwargs)
        return orig(*bound.args, **bound.kwargs)

    # Mark the wrapper to prevent re‑wrapping
    setattr(_init_indexer_compat, "__compat_patched__", True)
    Stream._init_indexer = _init_indexer_compat  # type: ignore[attr-defined]

    # Patch MultiStream as well (some versions check len(flow) first)
    MS = getattr(tmo, "MultiStream", None)
    if MS is not None:
        ms_orig = getattr(MS, "_init_indexer", None)
        if callable(ms_orig) and not getattr(ms_orig, "__compat_patched__", False):
            import inspect as _inspect
            ms_sig = _inspect.signature(ms_orig)
            ms_param_names = [p.name for p in list(ms_sig.parameters.values())[1:]]
            def _ms_init_indexer_compat(self, *args, **kwargs):
                bound = ms_sig.bind_partial(self, *args, **kwargs)
                if 'flow' in bound.arguments and bound.arguments['flow'] is None:
                    bound.arguments['flow'] = []
                else:
                    pos_args = list(args)
                    if 'flow' in ms_param_names:
                        flow_idx = ms_param_names.index('flow')
                        if flow_idx < len(pos_args) and pos_args[flow_idx] is None:
                            pos_args[flow_idx] = []
                            return ms_orig(self, *pos_args, **kwargs)
                return ms_orig(*bound.args, **bound.kwargs)
            setattr(_ms_init_indexer_compat, "__compat_patched__", True)
            MS._init_indexer = _ms_init_indexer_compat  # type: ignore[attr-defined]


def apply_all() -> None:
    _patch_thermosteam_init_indexer()


# Apply on import
apply_all()
