from abc import ABC, abstractmethod
from typing import Any


class RoutingStrategy(ABC):
    @abstractmethod
    def execute(self, payload: Any) -> Any:
        raise NotImplementedError
