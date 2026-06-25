from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.repositories.vehicle_repository import VehicleRepository
from app.services.vehicle_service import VehicleService, PlateAlreadyExistsError
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

_repository = VehicleRepository()

_404 = {"description": "Vehicle not found"}
_409 = {"description": "License plate already registered"}


def get_service() -> VehicleService:
    return VehicleService(_repository)


@router.get(
    "/",
    response_model=list[VehicleResponse],
    summary="List all vehicles",
    description=(
        "Returns the complete list of registered vehicles.\n\n"
        "Each vehicle includes its license plate and maximum load capacity. "
        "An empty array is returned when no vehicles have been registered yet."
    ),
    responses={200: {"description": "List of vehicles (may be empty)"}},
)
def list_vehicles(service: VehicleService = Depends(get_service)):
    return service.list_vehicles()


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Get vehicle by ID",
    description="Returns a single vehicle by its UUID. Returns `404` if the ID does not exist.",
    responses={
        200: {"description": "Vehicle found"},
        404: _404,
    },
)
def get_vehicle(vehicle_id: UUID, service: VehicleService = Depends(get_service)):
    vehicle = service.get_vehicle(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle


@router.post(
    "/",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new vehicle",
    description=(
        "Registers a new vehicle in the fleet and returns it with the generated `id`.\n\n"
        "- `plate` must be **unique** — returns `409` if already taken\n"
        "- `max_weight` must be **> 0** and is enforced by all routing strategies\n\n"
        "The vehicle becomes immediately available for route assignment."
    ),
    responses={
        201: {"description": "Vehicle registered successfully"},
        409: _409,
        422: {"description": "Validation error — invalid field values"},
    },
)
def create_vehicle(data: VehicleCreate, service: VehicleService = Depends(get_service)):
    try:
        return service.create_vehicle(data)
    except PlateAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Plate '{e}' already registered")


@router.patch(
    "/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Partially update a vehicle",
    description=(
        "Updates one or more fields of an existing vehicle. "
        "Only the fields present in the request body are modified.\n\n"
        "- Changing `plate` to one already in use returns `409`\n"
        "- Returns `404` if the vehicle does not exist"
    ),
    responses={
        200: {"description": "Vehicle updated successfully"},
        404: _404,
        409: _409,
        422: {"description": "Validation error — invalid field values"},
    },
)
def update_vehicle(vehicle_id: UUID, data: VehicleUpdate, service: VehicleService = Depends(get_service)):
    try:
        vehicle = service.update_vehicle(vehicle_id, data)
    except PlateAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Plate '{e}' already registered")
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle


@router.delete(
    "/{vehicle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a vehicle",
    description=(
        "Permanently removes a vehicle from the fleet by its UUID.\n\n"
        "Returns `204 No Content` on success. "
        "Returns `404` if the vehicle does not exist."
    ),
    responses={
        204: {"description": "Vehicle deleted successfully"},
        404: _404,
    },
)
def delete_vehicle(vehicle_id: UUID, service: VehicleService = Depends(get_service)):
    if not service.delete_vehicle(vehicle_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
