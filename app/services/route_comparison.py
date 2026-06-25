from app.schemas.route import RouteComparison, RouteRecommendation, RouteResponse


class RouteComparisonService:
    """
    Compares three pre-calculated routes and produces a logistics decision summary.

    Metrics:
    - shortest_route        : lowest total_distance
    - cheapest_route        : lowest total_cost
    - highest_utilization   : highest stops-per-distance-unit (packages delivered per map unit)
    """

    def compare(
        self,
        express: RouteResponse,
        economic: RouteResponse,
        strategic: RouteResponse,
    ) -> RouteComparison:
        routes = [express, economic, strategic]

        shortest  = min(routes, key=lambda r: r.total_distance)
        cheapest  = min(routes, key=lambda r: r.total_cost)
        highest_u = max(routes, key=lambda r: self._utilization(r))

        distance_saved   = max(r.total_distance for r in routes) - shortest.total_distance
        cost_saved       = max(r.total_cost for r in routes) - cheapest.total_cost
        recommended      = self._recommend(express, economic, strategic)

        return RouteComparison(
            shortest_route=_summarize(shortest),
            cheapest_route=_summarize(cheapest),
            highest_utilization_route=_summarize(highest_u),
            distance_saved=round(distance_saved, 4),
            cost_saved=round(cost_saved, 4),
            recommended=recommended,
        )

    @staticmethod
    def _utilization(route: RouteResponse) -> float:
        """Packages delivered per map unit. Returns 0 when distance is 0 (origin == destination)."""
        if route.total_distance == 0:
            return float(len(route.delivery_order))
        return len(route.delivery_order) / route.total_distance

    @staticmethod
    def _recommend(
        express: RouteResponse,
        economic: RouteResponse,
        strategic: RouteResponse,
    ) -> RouteRecommendation:
        """
        Selects the recommended route based on a composite score:
            score = normalised_distance * 0.5 + normalised_cost * 0.5

        Lower is better. Ties are broken by: express > economic > strategic.
        """
        routes = [express, economic, strategic]
        max_dist = max(r.total_distance for r in routes) or 1.0
        max_cost = max(r.total_cost for r in routes) or 1.0

        def score(r: RouteResponse) -> float:
            return (r.total_distance / max_dist) * 0.5 + (r.total_cost / max_cost) * 0.5

        best = min(routes, key=score)

        reasons: list[str] = []
        if best.total_distance == min(r.total_distance for r in routes):
            reasons.append("shortest total distance")
        if best.total_cost == min(r.total_cost for r in routes):
            reasons.append("lowest total cost")
        if not reasons:
            reasons.append("best balance between distance and cost")

        return RouteRecommendation(
            strategy=best.route_type,
            reason=f"Recommended because it offers the {' and '.join(reasons)}.",
        )


def _summarize(route: RouteResponse) -> "RouteSummary":  # noqa: F821 — forward ref resolved at runtime
    from app.schemas.route import RouteSummary
    return RouteSummary(
        strategy=route.route_type,
        total_distance=route.total_distance,
        total_cost=route.total_cost,
        stops=len(route.delivery_order),
    )
