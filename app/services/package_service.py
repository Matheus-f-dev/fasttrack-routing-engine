from uuid import UUID
from app.models.package import Package
from app.repositories.package_repository import PackageRepository
from app.schemas.package import PackageCreate, PackageUpdate


class PackageService:
    def __init__(self, repository: PackageRepository):
        self._repo = repository

    def list_packages(self) -> list[Package]:
        return self._repo.get_all()

    def get_package(self, package_id: UUID) -> Package | None:
        return self._repo.get_by_id(package_id)

    def create_package(self, data: PackageCreate) -> Package:
        package = Package(**data.model_dump())
        return self._repo.create(package)

    def update_package(self, package_id: UUID, data: PackageUpdate) -> Package | None:
        package = self._repo.get_by_id(package_id)
        if not package:
            return None
        updates = data.model_dump(exclude_none=True)
        for field, value in updates.items():
            setattr(package, field, value)
        return self._repo.update(package)

    def delete_package(self, package_id: UUID) -> bool:
        return self._repo.delete(package_id)
