from abc import ABC, abstractmethod
from app.algorithms.models import RouteInput, RouteResult


class RouteStrategy(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique strategy identifier used by the registry."""

    @abstractmethod
    def calculate_route(self, route_input: RouteInput) -> RouteResult:
        """Calculate and return a route plan for the given input."""
