import pytest
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
    return Vehicle(plate="TST-0001", max_weight=1000.0)


@pytest.fixture
def strategy() -> ExpressRouteStrategy:
    return ExpressRouteStrategy()


def make_package(name: str, x: float, y: float) -> Package:
    return Package(recipient_name=name, destination_x=x, destination_y=y, weight=1.0, access_cost=999.0)


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

class TestExpressStrategyMetadata:
    def test_name(self, strategy):
        assert strategy.name == "express"


# ---------------------------------------------------------------------------
# calculate_route
# ---------------------------------------------------------------------------

class TestExpressCalculateRoute:
    def test_single_package(self, strategy, origin, vehicle):
        pkg = make_package("Alice", 3.0, 4.0)
        result = strategy.calculate_route(RouteInput(packages=[pkg], vehicle=vehicle, origin=origin))

        assert result.strategy_name == "express"
        assert len(result.stops) == 1
        assert result.stops[0].packages[0] == pkg
        assert result.total_distance == pytest.approx(5.0)  # (0,0)→(3,4) = 5

    def test_two_packages_picks_nearest_first(self, strategy, origin, vehicle):
        near = make_package("Near", 1.0, 0.0)   # dist from origin = 1
        far  = make_package("Far",  10.0, 0.0)  # dist from origin = 10
        result = strategy.calculate_route(RouteInput(packages=[far, near], vehicle=vehicle, origin=origin))

        assert result.stops[0].packages[0] == near
        assert result.stops[1].packages[0] == far

    def test_total_distance_two_packages(self, strategy, origin, vehicle):
        # (0,0)→(3,0)=3 then (3,0)→(3,4)=4 → total=7
        a = make_package("A", 3.0, 0.0)
        b = make_package("B", 3.0, 4.0)
        result = strategy.calculate_route(RouteInput(packages=[a, b], vehicle=vehicle, origin=origin))

        assert result.total_distance == pytest.approx(7.0)

    def test_three_packages_nearest_neighbor_order(self, strategy, origin, vehicle):
        # origin=(0,0); p1=(1,0) d=1; p2=(2,0) d=2; p3=(10,0) d=10
        # expected: p1 → p2 → p3
        p1 = make_package("P1", 1.0, 0.0)
        p2 = make_package("P2", 2.0, 0.0)
        p3 = make_package("P3", 10.0, 0.0)
        result = strategy.calculate_route(RouteInput(packages=[p3, p1, p2], vehicle=vehicle, origin=origin))

        names = [s.packages[0].recipient_name for s in result.stops]
        assert names == ["P1", "P2", "P3"]

    def test_sequence_numbers_are_1_based(self, strategy, origin, vehicle):
        packages = [make_package(f"P{i}", float(i), 0.0) for i in range(1, 4)]
        result = strategy.calculate_route(RouteInput(packages=packages, vehicle=vehicle, origin=origin))

        assert [s.sequence for s in result.stops] == [1, 2, 3]

    def test_access_cost_does_not_affect_order(self, strategy, origin, vehicle):
        # cheap package is far, expensive is near — express must still pick nearest
        near_expensive = make_package("NearExpensive", 1.0, 0.0)
        near_expensive.access_cost = 9999.0
        far_cheap = make_package("FarCheap", 100.0, 0.0)
        far_cheap.access_cost = 0.0

        result = strategy.calculate_route(RouteInput(packages=[far_cheap, near_expensive], vehicle=vehicle, origin=origin))
        assert result.stops[0].packages[0].recipient_name == "NearExpensive"

    def test_total_cost_is_zero(self, strategy, origin, vehicle):
        pkg = make_package("Alice", 3.0, 4.0)
        result = strategy.calculate_route(RouteInput(packages=[pkg], vehicle=vehicle, origin=origin))
        assert result.total_cost == 0.0

    def test_each_stop_has_exactly_one_package(self, strategy, origin, vehicle):
        packages = [make_package(f"P{i}", float(i), float(i)) for i in range(1, 5)]
        result = strategy.calculate_route(RouteInput(packages=packages, vehicle=vehicle, origin=origin))
        assert all(len(s.packages) == 1 for s in result.stops)

    def test_all_packages_delivered(self, strategy, origin, vehicle):
        packages = [make_package(f"P{i}", float(i * 10), 0.0) for i in range(1, 6)]
        result = strategy.calculate_route(RouteInput(packages=packages, vehicle=vehicle, origin=origin))
        delivered_ids = {s.packages[0].id for s in result.stops}
        assert delivered_ids == {p.id for p in packages}

    def test_non_origin_hub_has_no_effect(self, strategy, vehicle):
        """Strategy always departs from origin, extra hubs are ignored."""
        custom_origin = Hub(name="Custom", x=5.0, y=5.0, is_main=True)
        pkg = make_package("Alice", 5.0, 5.0)   # same point as origin → dist = 0
        result = strategy.calculate_route(RouteInput(packages=[pkg], vehicle=vehicle, origin=custom_origin))
        assert result.total_distance == pytest.approx(0.0)
