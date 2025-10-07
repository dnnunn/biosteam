# Maps template names to import paths or callables returning BioSTEAM Unit classes
from typing import Callable, Dict

UnitFactory = Callable[..., object]

_registry: Dict[str, UnitFactory] = {}


def register(template: str, factory: UnitFactory) -> None:
    _registry[template] = factory


def get_factory(template: str) -> UnitFactory:
    if template not in _registry:
        raise KeyError(f"Unit template not registered: {template}")
    return _registry[template]


# TODO: register fermenter, disk stack, MF, AEX_membrane, UFDF, spray dryer factories here or in a plugin file
