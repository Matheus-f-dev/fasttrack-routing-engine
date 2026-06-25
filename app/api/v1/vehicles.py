from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.repositories.vehicle_repository import VehicleRepository
from app.services.vehicle_service import VehicleService, PlateAlreadyExistsError
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleResponse

router = APIRouter(prefix="/vehicles", tags=["vehicles"])

_repository = VehicleRepository()


def get_service() -> VehicleService:
    return VehicleService(_repository)


@router.get("/", response_model=list[VehicleResponse], summary="List all vehicles")
def list_vehicles(service: VehicleService = Depends(get_service)):
    return service.list_vehicles()


@router.get("/{vehicle_id}", response_model=VehicleResponse, summary="Get vehicle by ID")
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
)
def create_vehicle(data: VehicleCreate, service: VehicleService = Depends(get_service)):
    try:
        return service.create_vehicle(data)
    except PlateAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Plate '{e}' already registered")


@router.patch("/{vehicle_id}", response_model=VehicleResponse, summary="Partially update a vehicle")
def update_vehicle(vehicle_id: UUID, data: VehicleUpdate, service: VehicleService = Depends(get_service)):
    try:
        vehicle = service.update_vehicle(vehicle_id, data)
    except PlateAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Plate '{e}' already registered")
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove a vehicle")
def delete_vehicle(vehicle_id: UUID, service: VehicleService = Depends(get_service)):
    if not service.delete_vehicle(vehicle_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
