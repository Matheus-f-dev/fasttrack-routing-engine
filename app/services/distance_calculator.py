import math
from dataclasses import dataclass
from typing import Protocol


class Locatable(Protocol):
    @property
    def x(self) -> float: ...
    @property
    def y(self) -> float: ...


@dataclass(frozen=True)
class Point:
    """Lightweight Locatable for ad-hoc coordinates or Package adaptation."""
    x: float
    y: float


class DistanceCalculator:
    @staticmethod
    def calculate_distance(a: Locatable, b: Locatable) -> float:
        """Euclidean distance between two points: sqrt((x2-x1)^2 + (y2-y1)^2)."""
        return math.sqrt((b.x - a.x) ** 2 + (b.y - a.y) ** 2)

    @staticmethod
    def calculate_total_route_distance(stops: list[Locatable]) -> float:
        """Sum of distances between consecutive stops in the given order."""
        if len(stops) < 2:
            return 0.0
        return sum(
            DistanceCalculator.calculate_distance(stops[i], stops[i + 1])
            for i in range(len(stops) - 1)
        )
