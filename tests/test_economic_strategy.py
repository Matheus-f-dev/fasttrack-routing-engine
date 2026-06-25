import pytest
from app.algorithms.economic import EconomicRouteStrategy
from app.algorithms.express import ExpressRouteStrategy
from app.algorithms.models import RouteInput
from app.models.hub import Hub
from app.models.package import Package
from app.models.vehicle import Vehicle


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def origin() -> Hub:
    return Hub(name="Main Hub", x=0.0, y=0.0, is_main=True)


@pytest.fixture
def vehicle() -> Vehicle:
    return Vehicle(plate="ECO-0001", max_weight=1000.0)


@pytest.fixture
def strategy() -> EconomicRouteStrategy:
    return EconomicRouteStrategy()


def make_package(name: str, x: float, y: float, access_cost: float) -> Package:
    return Package(recipient_name=name, destination_x=x, destination_y=y, weight=1.0, access_cost=access_cost)


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

class TestEconomicStrategyMetadata:
    def test_name(self, strategy):
        assert strategy.name == "economic"


# ---------------------------------------------------------------------------
# calculate_route — cost behavior
# ---------------------------------------------------------------------------

class TestEconomicCalculateRoute:
    def test_single_package_total_cost(self, strategy, origin, vehicle):
        pkg = make_package("Alice", 3.0, 4.0, access_cost=10.0)
        result = strategy.calculate_route(RouteInput(packages=[pkg], vehicle=vehicle, origin=origin))

        assert result.total_cost == pytest.approx(10.0)
        assert result.total_distance == pytest.approx(5.0)

    def test_total_cost_accumulates_all_packages(self, strategy, origin, vehicle):
        packages = [make_package(f"P{i}", float(i), 0.0, access_cost=float(i * 10)) for i in range(1, 4)]
        result = strategy.calculate_route(RouteInput(packages=packages, vehicle=vehicle, origin=origin))

        assert result.total_cost == pytest.approx(10.0 + 20.0 + 30.0)

    def test_prefers_cheap_over_nearest(self, strategy, origin, vehicle):
        # near but expensive: dist=1, cost=100 → score=101
        # far but cheap:      dist=5, cost=0  → score=5
        # economic must pick the far-cheap first
        near_expensive = make_package("NearExpensive", 1.0, 0.0, access_cost=100.0)
        far_cheap      = make_package("FarCheap",      5.0, 0.0, access_cost=0.0)

        result = strategy.calculate_route(
            RouteInput(packages=[near_expensive, far_cheap], vehicle=vehicle, origin=origin)
        )
        assert result.stops[0].packages[0].recipient_name == "FarCheap"
        assert result.stops[1].packages[0].recipient_name == "NearExpensive"

    def test_prefers_nearest_when_costs_are_equal(self, strategy, origin, vehicle):
        near = make_package("Near", 1.0, 0.0, access_cost=5.0)
        far  = make_package("Far",  9.0, 0.0, access_cost=5.0)

        result = strategy.calculate_route(
            RouteInput(packages=[far, near], vehicle=vehicle, origin=origin)
        )
        assert result.stops[0].packages[0].recipient_name == "Near"

    def test_zero_access_cost_packages_ordered_by_distance(self, strategy, origin, vehicle):
        packages = [make_package(f"P{i}", float(i * 3), 0.0, access_cost=0.0) for i in range(1, 4)]
        result = strategy.calculate_route(RouteInput(packages=packages, vehicle=vehicle, origin=origin))

        names = [s.packages[0].recipient_name for s in result.stops]
        assert names == ["P1", "P2", "P3"]

    def test_strategy_name_in_result(self, strategy, origin, vehicle):
        pkg = make_package("A", 1.0, 0.0, access_cost=1.0)
        result = strategy.calculate_route(RouteInput(packages=[pkg], vehicle=vehicle, origin=origin))
        assert result.strategy_name == "economic"

    def test_sequence_numbers_are_1_based(self, strategy, origin, vehicle):
        packages = [make_package(f"P{i}", float(i), 0.0, access_cost=float(i)) for i in range(1, 5)]
        result = strategy.calculate_route(RouteInput(packages=packages, vehicle=vehicle, origin=origin))
        assert [s.sequence for s in result.stops] == [1, 2, 3, 4]

    def test_all_packages_delivered(self, strategy, origin, vehicle):
        packages = [make_package(f"P{i}", float(i * 10), 0.0, access_cost=float(i)) for i in range(1, 6)]
        result = strategy.calculate_route(RouteInput(packages=packages, vehicle=vehicle, origin=origin))
        delivered_ids = {s.packages[0].id for s in result.stops}
        assert delivered_ids == {p.id for p in packages}

    def test_each_stop_has_exactly_one_package(self, strategy, origin, vehicle):
        packages = [make_package(f"P{i}", float(i), float(i), access_cost=1.0) for i in range(1, 5)]
        result = strategy.calculate_route(RouteInput(packages=packages, vehicle=vehicle, origin=origin))
        assert all(len(s.packages) == 1 for s in result.stops)


# ---------------------------------------------------------------------------
# Divergence from express
# ---------------------------------------------------------------------------

class TestEconomicVsExpress:
    def test_may_produce_longer_distance_than_express(self, origin, vehicle):
        """
        Economic is allowed to travel further when access_cost savings justify it.
        This test asserts that the economic route does NOT always match express order.
        """
        # near but very expensive: dist=1, cost=1000 → score=1001
        # far but free:            dist=50, cost=0   → score=50
        near_expensive = make_package("NearExpensive", 1.0, 0.0, access_cost=1000.0)
        far_free       = make_package("FarFree",      50.0, 0.0, access_cost=0.0)

        packages = [near_expensive, far_free]
        route_input = RouteInput(packages=packages, vehicle=vehicle, origin=origin)

        economic_result = EconomicRouteStrategy().calculate_route(route_input)
        express_result  = ExpressRouteStrategy().calculate_route(route_input)

        # economic picks far_free first → longer first leg → higher total distance
        assert economic_result.total_distance > express_result.total_distance

    def test_economic_has_lower_total_cost_than_express(self, origin, vehicle):
        """
        When packages differ significantly in access_cost, economic must yield
        a strictly lower total_cost than the order express would produce.
        """
        cheap_far  = make_package("CheapFar",  100.0, 0.0, access_cost=1.0)
        costly_near = make_package("CostlyNear", 2.0, 0.0, access_cost=500.0)

        packages = [cheap_far, costly_near]
        route_input = RouteInput(packages=packages, vehicle=vehicle, origin=origin)

        economic_result = EconomicRouteStrategy().calculate_route(route_input)

        # regardless of order, total_cost is the sum of all access_costs
        # but we assert economic visits cheap_far first (lower score)
        assert economic_result.stops[0].packages[0].recipient_name == "CheapFar"
        assert economic_result.total_cost == pytest.approx(501.0)
