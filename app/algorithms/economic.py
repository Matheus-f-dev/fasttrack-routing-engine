from app.algorithms.base import RouteStrategy
from app.algorithms.models import RouteInput, RouteResult, RouteStop
from app.models.package import Package
from app.services.distance_calculator import DistanceCalculator, Locatable, Point


def _package_as_point(p: Package) -> Point:
    return Point(x=p.destination_x, y=p.destination_y)


class EconomicRouteStrategy(RouteStrategy):
    """
    Weighted nearest-neighbor greedy algorithm.

    At each step picks the unvisited package that minimizes:
        score = distance_from_current + access_cost

    This allows a geographically longer route when cheaper packages
    (low access_cost) compensate for the extra distance traveled.
    """

    @property
    def name(self) -> str:
        return "economic"

    @staticmethod
    def _score(current: Locatable, package: Package) -> float:
        return DistanceCalculator.calculate_distance(current, _package_as_point(package)) + package.access_cost

    def _calculate(self, route_input: RouteInput) -> RouteResult:
        remaining = list(route_input.packages)
        current: Locatable = route_input.origin
        stops: list[RouteStop] = []
        total_distance = 0.0
        total_cost = 0.0

        while remaining:
            cheapest = min(remaining, key=lambda p: self._score(current, p))
            leg = DistanceCalculator.calculate_distance(current, _package_as_point(cheapest))
            total_distance += leg
            total_cost += cheapest.access_cost
            remaining.remove(cheapest)
            stops.append(RouteStop(hub=None, packages=[cheapest], sequence=len(stops) + 1))
            current = _package_as_point(cheapest)

        return RouteResult(
            stops=stops,
            total_distance=total_distance,
            total_cost=total_cost,
            strategy_name=self.name,
        )
