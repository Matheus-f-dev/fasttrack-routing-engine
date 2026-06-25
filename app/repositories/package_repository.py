from uuid import UUID
from app.models.package import Package


class PackageRepository:
    def __init__(self):
        self._store: dict[UUID, Package] = {}

    def get_all(self) -> list[Package]:
        return list(self._store.values())

    def get_by_id(self, package_id: UUID) -> Package | None:
        return self._store.get(package_id)

    def create(self, package: Package) -> Package:
        self._store[package.id] = package
        return package

    def update(self, package: Package) -> Package:
        self._store[package.id] = package
        return package

    def delete(self, package_id: UUID) -> bool:
        if package_id not in self._store:
            return False
        del self._store[package_id]
        return True
