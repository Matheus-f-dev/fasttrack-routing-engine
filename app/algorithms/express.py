from app.algorithms.base import RouteStrategy
from app.algorithms.models import RouteInput, RouteResult, RouteStop
from app.models.package import Package
from app.services.distance_calculator import DistanceCalculator, Locatable, Point


def _package_as_point(p: Package) -> Point:
    return Point(x=p.destination_x, y=p.destination_y)


class ExpressRouteStrategy(RouteStrategy):
    """
    Nearest-neighbor greedy algorithm.
    At each step picks the unvisited package closest to the current position.
    Ignores access_cost — optimizes purely for minimum total distance.
    """

    @property
    def name(self) -> str:
        return "express"

    def _calculate(self, route_input: RouteInput) -> RouteResult:
        remaining = list(route_input.packages)
        current: Locatable = route_input.origin
        stops: list[RouteStop] = []
        distance_accumulator = 0.0

        while remaining:
            nearest = min(remaining, key=lambda p: DistanceCalculator.calculate_distance(current, _package_as_point(p)))
            distance_accumulator += DistanceCalculator.calculate_distance(current, _package_as_point(nearest))
            remaining.remove(nearest)
            stops.append(RouteStop(hub=None, packages=[nearest], sequence=len(stops) + 1))
            current = _package_as_point(nearest)

        return RouteResult(
            stops=stops,
            total_distance=distance_accumulator,
            total_cost=0.0,
            strategy_name=self.name,
        )
