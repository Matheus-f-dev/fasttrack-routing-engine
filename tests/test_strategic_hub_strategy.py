import pytest
from app.algorithms.strategic_hub import StrategicHubRouteStrategy
from app.algorithms.models import RouteInput
from app.models.hub import Hub
from app.models.package import Package
from app.models.vehicle import Vehicle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_hub(name: str, x: float, y: float) -> Hub:
    return Hub(name=name, x=x, y=y, is_main=False)


def make_package(name: str, x: float, y: float, weight: float = 1.0, access_cost: float = 0.0) -> Package:
    return Package(recipient_name=name, destination_x=x, destination_y=y, weight=weight, access_cost=access_cost)


def make_input(packages, vehicle, origin=None, secondary_hubs=None) -> RouteInput:
    origin = origin or Hub(name="Main", x=0.0, y=0.0, is_main=True)
    hubs = [origin] + (secondary_hubs or [])
    return RouteInput(packages=packages, vehicle=vehicle, origin=origin, available_hubs=hubs)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def strategy() -> StrategicHubRouteStrategy:
    return StrategicHubRouteStrategy()


@pytest.fixture
def vehicle() -> Vehicle:
    return Vehicle(plate="HUB-001", max_weight=100.0)


@pytest.fixture
def north_hub() -> Hub:
    return make_hub("North", x=0.0, y=10.0)


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

class TestStrategicHubMetadata:
    def test_name(self, strategy):
        assert strategy.name == "strategic_hub"


# ---------------------------------------------------------------------------
# Hub detour behavior
# ---------------------------------------------------------------------------

class TestStrategicHubDetour:
    def test_visits_secondary_hub_when_regional_packages_exist(self, strategy, vehicle, north_hub):
        # Package near north_hub (within radius=10)
        pkg = make_package("Near", x=0.0, y=12.0)
        result = strategy.calculate_route(make_input([pkg], vehicle, secondary_hubs=[north_hub]))

        assert result.visited_hub is not None
        assert result.visited_hub.name == "North"

    def test_extra_package_collected_true_when_hub_used(self, strategy, vehicle, north_hub):
        pkg = make_package("Near", x=0.0, y=12.0)
        result = strategy.calculate_route(make_input([pkg], vehicle, secondary_hubs=[north_hub]))

        assert result.extra_package_collected is True

    def test_distance_includes_hub_detour_leg(self, strategy, vehicle, north_hub):
        # origin=(0,0) → hub=(0,10) → pkg=(0,12)
        # expected: 10 + 2 = 12
        pkg = make_package("Near", x=0.0, y=12.0)
        result = strategy.calculate_route(make_input([pkg], vehicle, secondary_hubs=[north_hub]))

        assert result.total_distance == pytest.approx(12.0)

    def test_regional_packages_delivered_before_non_regional(self, strategy, vehicle, north_hub):
        regional     = make_package("Regional",    x=0.0,  y=11.0)
        non_regional = make_package("NonRegional", x=50.0, y=50.0)

        result = strategy.calculate_route(make_input([non_regional, regional], vehicle, secondary_hubs=[north_hub]))

        names = [s.packages[0].recipient_name for s in result.stops]
        assert names.index("Regional") < names.index("NonRegional")

    def test_selects_hub_closest_to_package_centroid(self, strategy, vehicle):
        south_hub = make_hub("South", x=0.0, y=-10.0)
        north_hub = make_hub("North", x=0.0, y=10.0)
        # All packages are near north → centroid near north
        packages = [make_package(f"P{i}", x=float(i), y=10.0) for i in range(3)]

        result = strategy.calculate_route(make_input(packages, vehicle, secondary_hubs=[south_hub, north_hub]))

        assert result.visited_hub is not None
        assert result.visited_hub.name == "North"

    def test_strategy_name_in_result(self, strategy, vehicle, north_hub):
        pkg = make_package("A", x=0.0, y=9.0)
        result = strategy.calculate_route(make_input([pkg], vehicle, secondary_hubs=[north_hub]))
        assert result.strategy_name == "strategic_hub"

    def test_total_cost_is_sum_of_all_access_costs(self, strategy, vehicle, north_hub):
        packages = [
            make_package("A", x=0.0, y=9.0,  access_cost=5.0),
            make_package("B", x=50.0, y=0.0, access_cost=10.0),
        ]
        result = strategy.calculate_route(make_input(packages, vehicle, secondary_hubs=[north_hub]))
        assert result.total_cost == pytest.approx(15.0)


# ---------------------------------------------------------------------------
# Weight limit
# ---------------------------------------------------------------------------

class TestStrategicHubWeightLimit:
    def test_respects_vehicle_max_weight(self, strategy, north_hub):
        light_vehicle = Vehicle(plate="LGT-001", max_weight=5.0)
        # Two regional packages each weight=4, cluster=8 > max_weight=5
        # Algorithm must drop the heaviest until cluster fits → at most 1 regional delivered via hub
        p1 = make_package("Heavy1", x=0.0, y=11.0, weight=4.0)
        p2 = make_package("Heavy2", x=0.0, y=12.0, weight=4.0)
        far = make_package("Far",   x=50.0, y=0.0, weight=1.0)

        result = strategy.calculate_route(
            make_input([p1, p2, far], light_vehicle, secondary_hubs=[north_hub])
        )
        regional_stops = [s for s in result.stops if s.hub is not None]
        regional_weight = sum(s.packages[0].weight for s in regional_stops)
        assert regional_weight <= light_vehicle.max_weight

    def test_all_packages_always_delivered_despite_weight_redistribution(self, strategy, north_hub):
        light_vehicle = Vehicle(plate="LGT-002", max_weight=6.0)
        packages = [make_package(f"P{i}", x=float(i), y=10.0, weight=2.0) for i in range(4)]

        result = strategy.calculate_route(
            make_input(packages, light_vehicle, secondary_hubs=[north_hub])
        )
        delivered_ids = {s.packages[0].id for s in result.stops}
        assert delivered_ids == {p.id for p in packages}


# ---------------------------------------------------------------------------
# Fallback (no secondary hubs)
# ---------------------------------------------------------------------------

class TestStrategicHubFallback:
    def test_no_secondary_hubs_returns_result(self, strategy, vehicle):
        pkg = make_package("A", x=3.0, y=4.0)
        result = strategy.calculate_route(make_input([pkg], vehicle, secondary_hubs=[]))

        assert result.strategy_name == "strategic_hub"
        assert len(result.stops) == 1

    def test_no_secondary_hubs_extra_package_false(self, strategy, vehicle):
        pkg = make_package("A", x=1.0, y=0.0)
        result = strategy.calculate_route(make_input([pkg], vehicle, secondary_hubs=[]))

        assert result.extra_package_collected is False
        assert result.visited_hub is None

    def test_no_secondary_hubs_all_packages_delivered(self, strategy, vehicle):
        packages = [make_package(f"P{i}", float(i * 5), 0.0) for i in range(1, 5)]
        result = strategy.calculate_route(make_input(packages, vehicle, secondary_hubs=[]))

        delivered_ids = {s.packages[0].id for s in result.stops}
        assert delivered_ids == {p.id for p in packages}


# ---------------------------------------------------------------------------
# Sequence and completeness
# ---------------------------------------------------------------------------

class TestStrategicHubSequence:
    def test_sequence_numbers_are_1_based_and_contiguous(self, strategy, vehicle, north_hub):
        packages = [make_package(f"P{i}", float(i), 10.0) for i in range(1, 5)]
        result = strategy.calculate_route(make_input(packages, vehicle, secondary_hubs=[north_hub]))

        sequences = [s.sequence for s in result.stops]
        assert sequences == list(range(1, len(packages) + 1))

    def test_all_packages_delivered(self, strategy, vehicle, north_hub):
        packages = [make_package(f"P{i}", float(i * 3), float(i * 3)) for i in range(1, 6)]
        result = strategy.calculate_route(make_input(packages, vehicle, secondary_hubs=[north_hub]))

        delivered_ids = {s.packages[0].id for s in result.stops}
        assert delivered_ids == {p.id for p in packages}

    def test_each_stop_has_exactly_one_package(self, strategy, vehicle, north_hub):
        packages = [make_package(f"P{i}", float(i), 9.0) for i in range(1, 4)]
        result = strategy.calculate_route(make_input(packages, vehicle, secondary_hubs=[north_hub]))

        assert all(len(s.packages) == 1 for s in result.stops)
