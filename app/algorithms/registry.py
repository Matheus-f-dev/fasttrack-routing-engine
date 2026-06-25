from app.algorithms.base import RouteStrategy
from app.algorithms.express import ExpressRouteStrategy
from app.algorithms.economic import EconomicRouteStrategy
from app.algorithms.strategic_hub import StrategicHubRouteStrategy


class StrategyNotFoundError(Exception):
    pass


class RouteStrategyRegistry:
    def __init__(self):
        self._strategies: dict[str, RouteStrategy] = {}
        for strategy in (ExpressRouteStrategy(), EconomicRouteStrategy(), StrategicHubRouteStrategy()):
            self.register(strategy)

    def register(self, strategy: RouteStrategy) -> None:
        self._strategies[strategy.name] = strategy

    def get(self, name: str) -> RouteStrategy:
        strategy = self._strategies.get(name)
        if not strategy:
            raise StrategyNotFoundError(f"Strategy '{name}' not registered. Available: {self.available()}")
        return strategy

    def available(self) -> list[str]:
        return list(self._strategies.keys())
