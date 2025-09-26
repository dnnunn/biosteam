"""Registry of BioSTEAM unit builders keyed by Excel module identifiers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Optional

from .excel_defaults import ModuleKey, ModuleConfig, ParameterRecord

# Type alias for clarity: the callable receives the module configuration and should
# return a configured BioSTEAM object (e.g., Unit, TEA, or helper data structure).
ModuleBuilder = Callable[[ModuleConfig], object]


@dataclass
class RegisteredModule:
    """Metadata for a registered module builder."""

    key: ModuleKey
    builder: ModuleBuilder
    description: Optional[str] = None

    def build(self, config: ModuleConfig) -> object:
        return self.builder(config)


class ModuleRegistry:
    """Simple registry mapping (module, option) keys to builder callables."""

    def __init__(self) -> None:
        self._registry: Dict[ModuleKey, RegisteredModule] = {}

    def register(
        self,
        key: ModuleKey,
        builder: ModuleBuilder,
        *,
        description: Optional[str] = None,
        overwrite: bool = False,
    ) -> None:
        if not overwrite and key in self._registry:
            raise KeyError(f"Module {key.as_tuple()} is already registered")
        self._registry[key] = RegisteredModule(key=key, builder=builder, description=description)

    def get(self, key: ModuleKey) -> RegisteredModule:
        try:
            return self._registry[key]
        except KeyError as err:
            raise KeyError(f"Module {key.as_tuple()} is not registered") from err

    def has(self, key: ModuleKey) -> bool:
        return key in self._registry

    def keys(self) -> Iterable[ModuleKey]:
        return self._registry.keys()

    def build(self, config: ModuleConfig) -> object:
        entry = self.get(config.key)
        return entry.build(config)


class MissingModuleBuilder(Exception):
    """Raised when attempting to build a module without a registered builder."""


def require_registered(registry: ModuleRegistry, config: ModuleConfig) -> RegisteredModule:
    """Helper that enforces registration before building."""

    if not registry.has(config.key):
        raise MissingModuleBuilder(
            "No builder registered for module {0} with option {1}".format(
                config.key.module, config.key.option or "<default>"
            )
        )
    return registry.get(config.key)


__all__ = [
    "ModuleRegistry",
    "ModuleBuilder",
    "RegisteredModule",
    "MissingModuleBuilder",
    "require_registered",
]
