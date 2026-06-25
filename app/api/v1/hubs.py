from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.repositories.hub_repository import HubRepository
from app.services.hub_service import HubService, HubNameAlreadyExistsError, MainHubProtectedError
from app.schemas.hub import HubCreate, HubUpdate, HubResponse

router = APIRouter(prefix="/hubs", tags=["hubs"])

_repository = HubRepository()


def get_service() -> HubService:
    return HubService(_repository)


@router.get(
    "/",
    response_model=list[HubResponse],
    summary="List all hubs",
    description="Returns all registered hubs, including the main hub at (0, 0).",
)
def list_hubs(service: HubService = Depends(get_service)):
    return service.list_hubs()


@router.get(
    "/main",
    response_model=HubResponse,
    summary="Get main hub",
    description="Returns the main dispatch hub, always located at coordinates (0, 0).",
)
def get_main_hub(service: HubService = Depends(get_service)):
    return service.get_main_hub()


@router.get(
    "/{hub_id}",
    response_model=HubResponse,
    summary="Get hub by ID",
    description="Returns a single hub by its unique identifier.",
)
def get_hub(hub_id: UUID, service: HubService = Depends(get_service)):
    hub = service.get_hub(hub_id)
    if not hub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")
    return hub


@router.post(
    "/",
    response_model=HubResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a secondary hub",
    description="Creates a new secondary hub. The hub name must be unique across all hubs.",
)
def create_hub(data: HubCreate, service: HubService = Depends(get_service)):
    try:
        return service.create_hub(data)
    except HubNameAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Hub name '{e}' already registered")


@router.patch(
    "/{hub_id}",
    response_model=HubResponse,
    summary="Partially update a hub",
    description="Updates one or more fields of a secondary hub. The main hub cannot be modified.",
)
def update_hub(hub_id: UUID, data: HubUpdate, service: HubService = Depends(get_service)):
    try:
        hub = service.update_hub(hub_id, data)
    except MainHubProtectedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Main hub cannot be modified")
    except HubNameAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Hub name '{e}' already registered")
    if not hub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")
    return hub


@router.delete(
    "/{hub_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a hub",
    description="Deletes a secondary hub by ID. The main hub cannot be deleted.",
)
def delete_hub(hub_id: UUID, service: HubService = Depends(get_service)):
    try:
        if not service.delete_hub(hub_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")
    except MainHubProtectedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Main hub cannot be deleted")
