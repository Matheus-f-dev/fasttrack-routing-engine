from app.algorithms.base import RouteStrategy
from app.algorithms.models import RouteInput, RouteResult


class StrategicHubRouteStrategy(RouteStrategy):
    """
    Optimizes by grouping deliveries through intermediate hubs.

    Future implementation: cluster packages by proximity to available_hubs,
    routing the vehicle through hub waypoints to reduce total travel distance
    in multi-hub scenarios.
    """

    @property
    def name(self) -> str:
        return "strategic_hub"

    def calculate_route(self, route_input: RouteInput) -> RouteResult:
        raise NotImplementedError
