from dataclasses import dataclass, field
from app.models.hub import Hub
from app.models.package import Package
from app.models.vehicle import Vehicle


@dataclass
class RouteInput:
    packages: list[Package]
    vehicle: Vehicle
    origin: Hub
    available_hubs: list[Hub] = field(default_factory=list)


@dataclass
class RouteStop:
    hub: Hub | None
    packages: list[Package]
    sequence: int


@dataclass
class RouteResult:
    stops: list[RouteStop]
    total_distance: float
    total_cost: float
    strategy_name: str
