from app.algorithms.base import RouteStrategy
from app.algorithms.models import RouteInput, RouteResult


class ExpressRouteStrategy(RouteStrategy):
    """
    Optimizes for fastest delivery.

    Future implementation: shortest-path algorithm (e.g. nearest neighbor)
    ignoring access costs, prioritizing minimum total distance.
    """

    @property
    def name(self) -> str:
        return "express"

    def calculate_route(self, route_input: RouteInput) -> RouteResult:
        raise NotImplementedError
