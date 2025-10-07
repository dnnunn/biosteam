from .registry import get_factory
from ..models.scenario import Scenario


class BuildResult:
    def __init__(self, system, flowsheet):
        self.system = system
        self.flowsheet = flowsheet


def build_system(scenario: Scenario) -> BuildResult:
    # Pseudocode until you wire actual BioSTEAM imports
    # import biosteam as bst
    # bst.settings.set_thermo("milk" or scenario.thermo_package)
    unit_map = {}
    for u in scenario.units:
        factory = get_factory(u.template)
        unit = factory(id=u.id, **u.overrides)
        unit_map[u.id] = unit
    # connect streams
    for s in scenario.streams:
        upstream = unit_map[s.from_]
        downstream = unit_map[s.to]
        # create and connect a stream; placeholder
        # stream = bst.Stream(source=upstream, sink=downstream)
        pass
    # system = bst.System(...)
    system = object()
    flowsheet = {"units": list(unit_map)}
    return BuildResult(system=system, flowsheet=flowsheet)
