from uuid import UUID
from app.models.hub import Hub
from app.repositories.hub_repository import HubRepository
from app.schemas.hub import HubCreate, HubUpdate


class HubNameAlreadyExistsError(Exception):
    pass


class MainHubProtectedError(Exception):
    pass


class HubService:
    def __init__(self, repository: HubRepository):
        self._repo = repository

    def list_hubs(self) -> list[Hub]:
        return self._repo.get_all()

    def get_hub(self, hub_id: UUID) -> Hub | None:
        return self._repo.get_by_id(hub_id)

    def get_main_hub(self) -> Hub:
        return self._repo.get_main()

    def create_hub(self, data: HubCreate) -> Hub:
        if self._repo.get_by_name(data.name):
            raise HubNameAlreadyExistsError(data.name)
        return self._repo.create(Hub(**data.model_dump()))

    def update_hub(self, hub_id: UUID, data: HubUpdate) -> Hub | None:
        hub = self._repo.get_by_id(hub_id)
        if not hub:
            return None
        if hub.is_main:
            raise MainHubProtectedError(hub_id)
        if data.name and data.name != hub.name and self._repo.get_by_name(data.name):
            raise HubNameAlreadyExistsError(data.name)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(hub, field, value)
        return self._repo.update(hub)

    def delete_hub(self, hub_id: UUID) -> bool:
        hub = self._repo.get_by_id(hub_id)
        if not hub:
            return False
        if hub.is_main:
            raise MainHubProtectedError(hub_id)
        return self._repo.delete(hub_id)
