from uuid import UUID
from app.models.hub import Hub


class HubRepository:
    def __init__(self):
        self._store: dict[UUID, Hub] = {}
        self._seed_main_hub()

    def _seed_main_hub(self) -> None:
        main = Hub(name="Main Hub", x=0.0, y=0.0, is_main=True)
        self._store[main.id] = main

    def get_all(self) -> list[Hub]:
        return list(self._store.values())

    def get_by_id(self, hub_id: UUID) -> Hub | None:
        return self._store.get(hub_id)

    def get_main(self) -> Hub:
        return next(h for h in self._store.values() if h.is_main)

    def get_by_name(self, name: str) -> Hub | None:
        return next((h for h in self._store.values() if h.name == name), None)

    def create(self, hub: Hub) -> Hub:
        self._store[hub.id] = hub
        return hub

    def update(self, hub: Hub) -> Hub:
        self._store[hub.id] = hub
        return hub

    def delete(self, hub_id: UUID) -> bool:
        if hub_id not in self._store:
            return False
        del self._store[hub_id]
        return True
