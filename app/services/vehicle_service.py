from uuid import UUID
from app.models.vehicle import Vehicle
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


class PlateAlreadyExistsError(Exception):
    pass


class VehicleService:
    def __init__(self, repository: VehicleRepository):
        self._repo = repository

    def list_vehicles(self) -> list[Vehicle]:
        return self._repo.get_all()

    def get_vehicle(self, vehicle_id: UUID) -> Vehicle | None:
        return self._repo.get_by_id(vehicle_id)

    def create_vehicle(self, data: VehicleCreate) -> Vehicle:
        if self._repo.get_by_plate(data.plate):
            raise PlateAlreadyExistsError(data.plate)
        return self._repo.create(Vehicle(**data.model_dump()))

    def update_vehicle(self, vehicle_id: UUID, data: VehicleUpdate) -> Vehicle | None:
        vehicle = self._repo.get_by_id(vehicle_id)
        if not vehicle:
            return None
        if data.plate and data.plate != vehicle.plate and self._repo.get_by_plate(data.plate):
            raise PlateAlreadyExistsError(data.plate)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(vehicle, field, value)
        return self._repo.update(vehicle)

    def delete_vehicle(self, vehicle_id: UUID) -> bool:
        return self._repo.delete(vehicle_id)
