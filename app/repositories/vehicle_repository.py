from uuid import UUID
from app.models.vehicle import Vehicle


class VehicleRepository:
    def __init__(self):
        self._store: dict[UUID, Vehicle] = {}

    def get_all(self) -> list[Vehicle]:
        return list(self._store.values())

    def get_by_id(self, vehicle_id: UUID) -> Vehicle | None:
        return self._store.get(vehicle_id)

    def get_by_plate(self, plate: str) -> Vehicle | None:
        return next((v for v in self._store.values() if v.plate == plate), None)

    def create(self, vehicle: Vehicle) -> Vehicle:
        self._store[vehicle.id] = vehicle
        return vehicle

    def update(self, vehicle: Vehicle) -> Vehicle:
        self._store[vehicle.id] = vehicle
        return vehicle

    def delete(self, vehicle_id: UUID) -> bool:
        if vehicle_id not in self._store:
            return False
        del self._store[vehicle_id]
        return True
