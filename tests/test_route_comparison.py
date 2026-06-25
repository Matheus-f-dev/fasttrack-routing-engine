import pytest
from app.schemas.route import DeliveryStop, RouteResponse
from app.services.route_comparison import RouteComparisonService
from uuid import uuid4


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_stop(seq: int) -> DeliveryStop:
    return DeliveryStop(
        sequence=seq,
        package_id=uuid4(),
        recipient_name="Test",
        destination_x=float(seq),
        destination_y=0.0,
    )


def make_route(strategy: str, distance: float, cost: float, stops: int = 3) -> RouteResponse:
    return RouteResponse(
        route_type=strategy,
        total_distance=distance,
        total_cost=cost,
        delivery_order=[make_stop(i) for i in range(1, stops + 1)],
    )


@pytest.fixture
def service() -> RouteComparisonService:
    return RouteComparisonService()


@pytest.fixture
def routes():
    return dict(
        express=make_route("express",      distance=10.0, cost=0.0),
        economic=make_route("economic",    distance=15.0, cost=5.0),
        strategic=make_route("strategic_hub", distance=12.0, cost=8.0),
    )


# ---------------------------------------------------------------------------
# shortest_route
# ---------------------------------------------------------------------------

class TestShortestRoute:
    def test_identifies_shortest_distance(self, service, routes):
        result = service.compare(**routes)
        assert result.shortest_route.strategy == "express"
        assert result.shortest_route.total_distance == 10.0

    def test_shortest_when_all_equal(self, service):
        r = make_route("express", distance=5.0, cost=0.0)
        result = service.compare(express=r, economic=r, strategic=r)
        assert result.shortest_route.total_distance == 5.0

    def test_shortest_route_summary_has_correct_stops(self, service, routes):
        result = service.compare(**routes)
        assert result.shortest_route.stops == 3


# ---------------------------------------------------------------------------
# cheapest_route
# ---------------------------------------------------------------------------

class TestCheapestRoute:
    def test_identifies_lowest_cost(self, service, routes):
        result = service.compare(**routes)
        assert result.cheapest_route.strategy == "express"
        assert result.cheapest_route.total_cost == 0.0

    def test_cheapest_distinct_from_shortest(self, service):
        express  = make_route("express",      distance=5.0,  cost=50.0)
        economic = make_route("economic",     distance=20.0, cost=1.0)
        strategic = make_route("strategic_hub", distance=15.0, cost=10.0)

        result = service.compare(express=express, economic=economic, strategic=strategic)

        assert result.shortest_route.strategy == "express"
        assert result.cheapest_route.strategy == "economic"

    def test_cheapest_route_summary_cost_matches(self, service, routes):
        result = service.compare(**routes)
        assert result.cheapest_route.total_cost == 0.0


# ---------------------------------------------------------------------------
# highest_utilization_route
# ---------------------------------------------------------------------------

class TestHighestUtilizationRoute:
    def test_more_stops_per_distance_unit_wins(self, service):
        # express: 2 stops / 10 dist = 0.2
        # economic: 6 stops / 10 dist = 0.6  ← highest
        # strategic: 3 stops / 15 dist = 0.2
        express   = make_route("express",       distance=10.0, cost=0.0, stops=2)
        economic  = make_route("economic",      distance=10.0, cost=5.0, stops=6)
        strategic = make_route("strategic_hub", distance=15.0, cost=8.0, stops=3)

        result = service.compare(express=express, economic=economic, strategic=strategic)
        assert result.highest_utilization_route.strategy == "economic"

    def test_zero_distance_does_not_crash(self, service):
        zero_dist = make_route("express", distance=0.0, cost=0.0, stops=3)
        other     = make_route("economic", distance=10.0, cost=5.0, stops=1)
        result = service.compare(express=zero_dist, economic=other, strategic=other)
        assert result.highest_utilization_route.strategy == "express"


# ---------------------------------------------------------------------------
# distance_saved / cost_saved
# ---------------------------------------------------------------------------

class TestSavings:
    def test_distance_saved_is_max_minus_min(self, service, routes):
        result = service.compare(**routes)
        assert result.distance_saved == pytest.approx(15.0 - 10.0)

    def test_cost_saved_is_max_minus_min(self, service, routes):
        result = service.compare(**routes)
        assert result.cost_saved == pytest.approx(8.0 - 0.0)

    def test_savings_are_zero_when_all_equal(self, service):
        r = make_route("express", distance=5.0, cost=10.0)
        result = service.compare(express=r, economic=r, strategic=r)
        assert result.distance_saved == 0.0
        assert result.cost_saved == 0.0


# ---------------------------------------------------------------------------
# recommended
# ---------------------------------------------------------------------------

class TestRecommendation:
    def test_recommended_has_strategy_and_reason(self, service, routes):
        result = service.compare(**routes)
        assert result.recommended.strategy
        assert result.recommended.reason

    def test_recommends_best_balanced_strategy(self, service):
        # express: dist=5,  cost=0   → norm_score = 5/20*0.5 + 0/10*0.5 = 0.125
        # economic: dist=20, cost=5  → norm_score = 20/20*0.5 + 5/10*0.5 = 0.75
        # strategic: dist=10, cost=10 → norm_score = 10/20*0.5 + 10/10*0.5 = 0.75
        express   = make_route("express",       distance=5.0,  cost=0.0)
        economic  = make_route("economic",      distance=20.0, cost=5.0)
        strategic = make_route("strategic_hub", distance=10.0, cost=10.0)

        result = service.compare(express=express, economic=economic, strategic=strategic)
        assert result.recommended.strategy == "express"

    def test_reason_contains_meaningful_text(self, service, routes):
        result = service.compare(**routes)
        reason = result.recommended.reason.lower()
        assert any(word in reason for word in ["distance", "cost", "balance"])

    def test_recommendation_strategy_is_one_of_three(self, service, routes):
        result = service.compare(**routes)
        assert result.recommended.strategy in {"express", "economic", "strategic_hub"}
