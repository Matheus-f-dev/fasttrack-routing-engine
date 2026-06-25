from app.algorithms.base import RouteStrategy
from app.algorithms.models import RouteInput, RouteResult


class EconomicRouteStrategy(RouteStrategy):
    """
    Optimizes for lowest total delivery cost.

    Future implementation: weighted-path algorithm that factors in
    each package's access_cost to minimize the overall route expense.
    """

    @property
    def name(self) -> str:
        return "economic"

    def calculate_route(self, route_input: RouteInput) -> RouteResult:
        raise NotImplementedError
