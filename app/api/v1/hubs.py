from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.repositories.hub_repository import HubRepository
from app.services.hub_service import HubService, HubNameAlreadyExistsError, MainHubProtectedError
from app.schemas.hub import HubCreate, HubUpdate, HubResponse

router = APIRouter(prefix="/hubs", tags=["hubs"])

_repository = HubRepository()

_403 = {"description": "Operation not allowed on the main hub"}
_404 = {"description": "Hub not found"}
_409 = {"description": "Hub name already registered"}


def get_service() -> HubService:
    return HubService(_repository)


@router.get(
    "/",
    response_model=list[HubResponse],
    summary="List all hubs",
    description=(
        "Returns all registered hubs, including the main hub at (0, 0).\n\n"
        "The main hub (`is_main: true`) is always present and serves as the departure "
        "point for all routing strategies."
    ),
    responses={200: {"description": "List of hubs (always contains at least the main hub)"}},
)
def list_hubs(service: HubService = Depends(get_service)):
    return service.list_hubs()


@router.get(
    "/main",
    response_model=HubResponse,
    summary="Get the main hub",
    description=(
        "Returns the main dispatch hub, always located at coordinates (0, 0).\n\n"
        "This is the origin point for all routing calculations. "
        "It always exists and cannot be deleted or modified."
    ),
    responses={200: {"description": "Main hub details"}},
)
def get_main_hub(service: HubService = Depends(get_service)):
    return service.get_main_hub()


@router.get(
    "/{hub_id}",
    response_model=HubResponse,
    summary="Get hub by ID",
    description="Returns a single hub by its UUID. Returns `404` if the ID does not exist.",
    responses={
        200: {"description": "Hub found"},
        404: _404,
    },
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
    description=(
        "Creates a new secondary hub at the given coordinates.\n\n"
        "- `name` must be **unique** across all hubs — returns `409` if already taken\n"
        "- Secondary hubs activate the `strategic_hub` routing strategy, which clusters "
        "nearby packages and routes the vehicle through the hub\n\n"
        "The new hub is immediately available for routing."
    ),
    responses={
        201: {"description": "Hub created successfully"},
        409: _409,
        422: {"description": "Validation error — invalid field values"},
    },
)
def create_hub(data: HubCreate, service: HubService = Depends(get_service)):
    try:
        return service.create_hub(data)
    except HubNameAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Hub name '{e}' already registered")


@router.patch(
    "/{hub_id}",
    response_model=HubResponse,
    summary="Partially update a secondary hub",
    description=(
        "Updates one or more fields of a secondary hub. "
        "Only the fields present in the request body are modified.\n\n"
        "- The **main hub cannot be modified** — returns `403`\n"
        "- Changing `name` to one already in use returns `409`\n"
        "- Returns `404` if the hub does not exist"
    ),
    responses={
        200: {"description": "Hub updated successfully"},
        403: _403,
        404: _404,
        409: _409,
    },
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
    summary="Delete a secondary hub",
    description=(
        "Permanently removes a secondary hub by its UUID.\n\n"
        "- The **main hub cannot be deleted** — returns `403`\n"
        "- Returns `204 No Content` on success\n"
        "- Returns `404` if the hub does not exist"
    ),
    responses={
        204: {"description": "Hub deleted successfully"},
        403: _403,
        404: _404,
    },
)
def delete_hub(hub_id: UUID, service: HubService = Depends(get_service)):
    try:
        if not service.delete_hub(hub_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hub not found")
    except MainHubProtectedError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Main hub cannot be deleted")
