from app.algorithms.base import RouteStrategy
from app.algorithms.models import RouteInput, RouteResult, RouteStop
from app.models.hub import Hub
from app.models.package import Package
from app.services.distance_calculator import DistanceCalculator, Locatable, Point

_REGIONAL_RADIUS = 10.0  # packages within this distance of a hub are considered regional


def _package_as_point(p: Package) -> Point:
    return Point(x=p.destination_x, y=p.destination_y)


def _nearest_hub(target: Locatable, hubs: list[Hub]) -> Hub:
    return min(hubs, key=lambda h: DistanceCalculator.calculate_distance(target, h))


def _nearest_neighbor_order(packages: list[Package], start: Locatable) -> list[Package]:
    remaining, ordered, current = list(packages), [], start
    while remaining:
        nearest = min(remaining, key=lambda p: DistanceCalculator.calculate_distance(current, _package_as_point(p)))
        ordered.append(nearest)
        remaining.remove(nearest)
        current = _package_as_point(nearest)
    return ordered


class StrategicHubRouteStrategy(RouteStrategy):
    """
    Routes through the nearest secondary hub on the way to the delivery region.

    Steps:
    1. Find secondary hubs (is_main=False). If none exist, fall back to nearest-neighbor.
    2. Identify the best hub: the secondary hub closest to the centroid of all packages.
    3. Collect packages whose destination lies within _REGIONAL_RADIUS of that hub
       AND whose combined weight (original + hub-regional) respects vehicle.max_weight.
    4. Route: origin → best_hub → deliver regional packages (nearest-neighbor)
       → deliver remaining packages (nearest-neighbor from last stop).
    5. Flags extra_package_collected=True if the hub stop produced ≥1 grouped package.
    """

    @property
    def name(self) -> str:
        return "strategic_hub"

    @staticmethod
    def _centroid(packages: list[Package]) -> Point:
        return Point(
            x=sum(p.destination_x for p in packages) / len(packages),
            y=sum(p.destination_y for p in packages) / len(packages),
        )

    @staticmethod
    def _regional_packages(packages: list[Package], hub: Hub) -> list[Package]:
        return [
            p for p in packages
            if DistanceCalculator.calculate_distance(_package_as_point(p), hub) <= _REGIONAL_RADIUS
        ]

    def calculate_route(self, route_input: RouteInput) -> RouteResult:
        packages  = list(route_input.packages)
        origin    = route_input.origin
        vehicle   = route_input.vehicle
        secondary = [h for h in route_input.available_hubs if not h.is_main]

        if not secondary:
            return self._fallback(packages, origin)

        centroid   = self._centroid(packages)
        best_hub   = _nearest_hub(centroid, secondary)
        regional   = self._regional_packages(packages, best_hub)
        remaining  = [p for p in packages if p not in regional]

        # Respect vehicle weight limit — evaluate only the regional cluster
        regional_weight = sum(p.weight for p in regional)
        if regional_weight > vehicle.max_weight:
            overload = regional_weight - vehicle.max_weight
            regional.sort(key=lambda p: p.weight, reverse=True)
            while regional and overload > 0:
                dropped = regional.pop(0)
                remaining.append(dropped)
                overload -= dropped.weight

        extra_package_collected = len(regional) > 0
        visited_hub = best_hub if extra_package_collected else None
        stops: list[RouteStop] = []
        total_distance = 0.0
        current: Locatable = origin

        # Leg 1: origin → hub (only if there are regional packages to pick up)
        if extra_package_collected:
            total_distance += DistanceCalculator.calculate_distance(current, best_hub)
            current = best_hub

        # Leg 2: deliver regional packages in nearest-neighbor order from hub
        for pkg in _nearest_neighbor_order(regional, current):
            total_distance += DistanceCalculator.calculate_distance(current, _package_as_point(pkg))
            current = _package_as_point(pkg)
            stops.append(RouteStop(hub=best_hub if extra_package_collected else None, packages=[pkg], sequence=len(stops) + 1))

        # Leg 3: deliver remaining packages in nearest-neighbor order
        for pkg in _nearest_neighbor_order(remaining, current):
            total_distance += DistanceCalculator.calculate_distance(current, _package_as_point(pkg))
            current = _package_as_point(pkg)
            stops.append(RouteStop(hub=None, packages=[pkg], sequence=len(stops) + 1))

        return RouteResult(
            stops=stops,
            total_distance=total_distance,
            total_cost=sum(p.access_cost for p in packages),
            strategy_name=self.name,
            extra_package_collected=extra_package_collected,
            visited_hub=visited_hub,
        )

    def _fallback(self, packages: list[Package], origin: Locatable) -> RouteResult:
        """No secondary hubs available — nearest-neighbor without hub detour."""
        stops: list[RouteStop] = []
        total_distance = 0.0
        current = origin
        for pkg in _nearest_neighbor_order(packages, current):
            total_distance += DistanceCalculator.calculate_distance(current, _package_as_point(pkg))
            current = _package_as_point(pkg)
            stops.append(RouteStop(hub=None, packages=[pkg], sequence=len(stops) + 1))
        return RouteResult(
            stops=stops,
            total_distance=total_distance,
            total_cost=sum(p.access_cost for p in packages),
            strategy_name=self.name,
            extra_package_collected=False,
            visited_hub=None,
        )
