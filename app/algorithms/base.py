from abc import ABC, abstractmethod
from app.algorithms.models import RouteInput, RouteResult


class VehicleCapacityExceededError(Exception):
    def __init__(self, total_weight: float, max_weight: float):
        self.total_weight = total_weight
        self.max_weight = max_weight
        super().__init__(
            f"Total package weight ({total_weight:.2f} kg) exceeds "
            f"vehicle capacity ({max_weight:.2f} kg). "
            f"Reduce the load by at least {total_weight - max_weight:.2f} kg."
        )


class RouteStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique strategy identifier used by the registry."""

    @abstractmethod
    def _calculate(self, route_input: RouteInput) -> RouteResult:
        """Strategy-specific routing logic. Called only after capacity is validated."""

    def calculate_route(self, route_input: RouteInput) -> RouteResult:
        """Validates vehicle capacity then delegates to the strategy implementation."""
        total_weight = sum(p.weight for p in route_input.packages)
        if total_weight > route_input.vehicle.max_weight:
            raise VehicleCapacityExceededError(total_weight, route_input.vehicle.max_weight)
        return self._calculate(route_input)
