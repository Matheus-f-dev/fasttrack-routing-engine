import math
import pytest
from app.models.hub import Hub
from app.models.package import Package
from app.services.distance_calculator import DistanceCalculator, Point


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def origin() -> Point:
    return Point(x=0.0, y=0.0)


@pytest.fixture
def hub_a() -> Hub:
    return Hub(name="A", x=0.0, y=0.0)


@pytest.fixture
def hub_b() -> Hub:
    return Hub(name="B", x=3.0, y=4.0)


@pytest.fixture
def package_at(request) -> Package:
    x, y = request.param
    return Package(recipient_name="Test", destination_x=x, destination_y=y, weight=1.0, access_cost=0.0)


# ---------------------------------------------------------------------------
# calculate_distance
# ---------------------------------------------------------------------------

class TestCalculateDistance:
    def test_known_triangle_3_4_5(self, hub_a, hub_b):
        assert DistanceCalculator.calculate_distance(hub_a, hub_b) == pytest.approx(5.0)

    def test_same_point_returns_zero(self, hub_a):
        assert DistanceCalculator.calculate_distance(hub_a, hub_a) == 0.0

    def test_symmetry(self, hub_a, hub_b):
        d_ab = DistanceCalculator.calculate_distance(hub_a, hub_b)
        d_ba = DistanceCalculator.calculate_distance(hub_b, hub_a)
        assert d_ab == pytest.approx(d_ba)

    def test_negative_coordinates(self):
        a = Point(x=-3.0, y=-4.0)
        b = Point(x=0.0, y=0.0)
        assert DistanceCalculator.calculate_distance(a, b) == pytest.approx(5.0)

    def test_horizontal_segment(self):
        a, b = Point(x=0.0, y=2.0), Point(x=5.0, y=2.0)
        assert DistanceCalculator.calculate_distance(a, b) == pytest.approx(5.0)

    def test_vertical_segment(self):
        a, b = Point(x=1.0, y=0.0), Point(x=1.0, y=7.0)
        assert DistanceCalculator.calculate_distance(a, b) == pytest.approx(7.0)

    def test_float_precision(self):
        a, b = Point(x=0.0, y=0.0), Point(x=1.0, y=1.0)
        assert DistanceCalculator.calculate_distance(a, b) == pytest.approx(math.sqrt(2))

    def test_accepts_hub(self, hub_a, hub_b):
        """Hub satisfies Locatable via structural subtyping."""
        result = DistanceCalculator.calculate_distance(hub_a, hub_b)
        assert result == pytest.approx(5.0)

    def test_accepts_point(self):
        """Point satisfies Locatable directly."""
        a, b = Point(0.0, 0.0), Point(1.0, 0.0)
        assert DistanceCalculator.calculate_distance(a, b) == pytest.approx(1.0)

    def test_accepts_mixed_locatables(self, hub_a):
        """Hub and Point can be mixed as long as both are Locatable."""
        b = Point(x=3.0, y=4.0)
        assert DistanceCalculator.calculate_distance(hub_a, b) == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# calculate_total_route_distance
# ---------------------------------------------------------------------------

class TestCalculateTotalRouteDistance:
    def test_empty_list_returns_zero(self):
        assert DistanceCalculator.calculate_total_route_distance([]) == 0.0

    def test_single_stop_returns_zero(self, hub_a):
        assert DistanceCalculator.calculate_total_route_distance([hub_a]) == 0.0

    def test_two_stops(self, hub_a, hub_b):
        assert DistanceCalculator.calculate_total_route_distance([hub_a, hub_b]) == pytest.approx(5.0)

    def test_three_collinear_stops(self):
        stops = [Point(0.0, 0.0), Point(3.0, 0.0), Point(7.0, 0.0)]
        assert DistanceCalculator.calculate_total_route_distance(stops) == pytest.approx(7.0)

    def test_closed_triangle_route(self):
        # 3-4-5 triangle: A→B→C→A = 5 + 5 + ... let's use an equilateral
        stops = [Point(0.0, 0.0), Point(3.0, 4.0), Point(6.0, 0.0), Point(0.0, 0.0)]
        expected = (
            DistanceCalculator.calculate_distance(stops[0], stops[1])
            + DistanceCalculator.calculate_distance(stops[1], stops[2])
            + DistanceCalculator.calculate_distance(stops[2], stops[3])
        )
        assert DistanceCalculator.calculate_total_route_distance(stops) == pytest.approx(expected)

    def test_order_affects_total(self):
        a, b, c = Point(0.0, 0.0), Point(10.0, 0.0), Point(10.0, 10.0)
        direct = DistanceCalculator.calculate_total_route_distance([a, b, c])
        reversed_ = DistanceCalculator.calculate_total_route_distance([c, b, a])
        assert direct == pytest.approx(reversed_)  # same total, different direction

    def test_accepts_hub_list(self):
        hubs = [Hub(name="X", x=0.0, y=0.0), Hub(name="Y", x=0.0, y=5.0)]
        assert DistanceCalculator.calculate_total_route_distance(hubs) == pytest.approx(5.0)

    def test_large_route_accumulates_correctly(self):
        # 10 stops along x-axis, 1 unit apart → total = 9.0
        stops = [Point(float(i), 0.0) for i in range(10)]
        assert DistanceCalculator.calculate_total_route_distance(stops) == pytest.approx(9.0)
