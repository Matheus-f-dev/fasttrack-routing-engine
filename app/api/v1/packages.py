from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.repositories.package_repository import PackageRepository
from app.services.package_service import PackageService
from app.schemas.package import PackageCreate, PackageUpdate, PackageResponse

router = APIRouter(prefix="/packages", tags=["packages"])

_repository = PackageRepository()


def get_service() -> PackageService:
    return PackageService(_repository)


@router.get("/", response_model=list[PackageResponse])
def list_packages(service: PackageService = Depends(get_service)):
    return service.list_packages()


@router.get("/{package_id}", response_model=PackageResponse)
def get_package(package_id: UUID, service: PackageService = Depends(get_service)):
    package = service.get_package(package_id)
    if not package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    return package


@router.post("/", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
def create_package(data: PackageCreate, service: PackageService = Depends(get_service)):
    return service.create_package(data)


@router.patch("/{package_id}", response_model=PackageResponse)
def update_package(package_id: UUID, data: PackageUpdate, service: PackageService = Depends(get_service)):
    package = service.update_package(package_id, data)
    if not package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    return package


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(package_id: UUID, service: PackageService = Depends(get_service)):
    if not service.delete_package(package_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
