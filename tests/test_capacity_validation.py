import pytest
from app.algorithms.base import VehicleCapacityExceededError
from app.algorithms.express import ExpressRouteStrategy
from app.algorithms.economic import EconomicRouteStrategy
from app.algorithms.strategic_hub import StrategicHubRouteStrategy
from app.algorithms.models import RouteInput
from app.models.hub import Hub
from app.models.package import Package
from app.models.vehicle import Vehicle


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_package(name: str, weight: float) -> Package:
    return Package(recipient_name=name, destination_x=1.0, destination_y=1.0, weight=weight, access_cost=0.0)


def make_input(packages: list[Package], max_weight: float) -> RouteInput:
    origin = Hub(name="Main", x=0.0, y=0.0, is_main=True)
    vehicle = Vehicle(plate="TST-0001", max_weight=max_weight)
    return RouteInput(packages=packages, vehicle=vehicle, origin=origin, available_hubs=[origin])


STRATEGIES = [
    ExpressRouteStrategy(),
    EconomicRouteStrategy(),
    StrategicHubRouteStrategy(),
]


# ---------------------------------------------------------------------------
# VehicleCapacityExceededError
# ---------------------------------------------------------------------------

class TestVehicleCapacityExceededError:
    def test_message_contains_total_weight(self):
        err = VehicleCapacityExceededError(total_weight=15.0, max_weight=10.0)
        assert "15.00 kg" in str(err)

    def test_message_contains_max_weight(self):
        err = VehicleCapacityExceededError(total_weight=15.0, max_weight=10.0)
        assert "10.00 kg" in str(err)

    def test_message_contains_overload_delta(self):
        err = VehicleCapacityExceededError(total_weight=15.0, max_weight=10.0)
        assert "5.00 kg" in str(err)

    def test_stores_total_and_max_as_attributes(self):
        err = VehicleCapacityExceededError(total_weight=7.5, max_weight=5.0)
        assert err.total_weight == 7.5
        assert err.max_weight == 5.0


# ---------------------------------------------------------------------------
# Capacity validation — all strategies
# ---------------------------------------------------------------------------

class TestCapacityValidationAllStrategies:
    @pytest.mark.parametrize("strategy", STRATEGIES, ids=lambda s: s.name)
    def test_raises_when_weight_exceeds_capacity(self, strategy):
        packages = [make_package("P1", weight=6.0), make_package("P2", weight=6.0)]
        route_input = make_input(packages, max_weight=10.0)

        with pytest.raises(VehicleCapacityExceededError):
            strategy.calculate_route(route_input)

    @pytest.mark.parametrize("strategy", STRATEGIES, ids=lambda s: s.name)
    def test_succeeds_when_weight_equals_capacity(self, strategy):
        packages = [make_package("P1", weight=5.0), make_package("P2", weight=5.0)]
        route_input = make_input(packages, max_weight=10.0)

        result = strategy.calculate_route(route_input)
        assert len(result.stops) == 2

    @pytest.mark.parametrize("strategy", STRATEGIES, ids=lambda s: s.name)
    def test_succeeds_when_weight_is_under_capacity(self, strategy):
        packages = [make_package("P1", weight=3.0), make_package("P2", weight=3.0)]
        route_input = make_input(packages, max_weight=10.0)

        result = strategy.calculate_route(route_input)
        assert len(result.stops) == 2

    @pytest.mark.parametrize("strategy", STRATEGIES, ids=lambda s: s.name)
    def test_error_reports_correct_weights(self, strategy):
        packages = [make_package("P1", weight=8.0), make_package("P2", weight=8.0)]
        route_input = make_input(packages, max_weight=10.0)

        with pytest.raises(VehicleCapacityExceededError) as exc_info:
            strategy.calculate_route(route_input)

        assert exc_info.value.total_weight == pytest.approx(16.0)
        assert exc_info.value.max_weight == pytest.approx(10.0)

    @pytest.mark.parametrize("strategy", STRATEGIES, ids=lambda s: s.name)
    def test_raises_on_single_package_over_limit(self, strategy):
        packages = [make_package("Heavy", weight=999.0)]
        route_input = make_input(packages, max_weight=100.0)

        with pytest.raises(VehicleCapacityExceededError):
            strategy.calculate_route(route_input)
