from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.repositories.package_repository import PackageRepository
from app.services.package_service import PackageService
from app.schemas.package import PackageCreate, PackageUpdate, PackageResponse

router = APIRouter(prefix="/packages", tags=["packages"])

_repository = PackageRepository()

_404 = {"description": "Package not found"}


def get_service() -> PackageService:
    return PackageService(_repository)


@router.get(
    "/",
    response_model=list[PackageResponse],
    summary="List all packages",
    description=(
        "Returns the complete list of registered packages.\n\n"
        "Each package includes its destination coordinates, weight and access cost. "
        "An empty array is returned when no packages have been registered yet."
    ),
    responses={200: {"description": "List of packages (may be empty)"}},
)
def list_packages(service: PackageService = Depends(get_service)):
    return service.list_packages()


@router.get(
    "/{package_id}",
    response_model=PackageResponse,
    summary="Get package by ID",
    description="Returns a single package by its UUID. Returns `404` if the ID does not exist.",
    responses={
        200: {"description": "Package found"},
        404: _404,
    },
)
def get_package(package_id: UUID, service: PackageService = Depends(get_service)):
    package = service.get_package(package_id)
    if not package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    return package


@router.post(
    "/",
    response_model=PackageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new package",
    description=(
        "Creates a new package and returns it with the generated `id`.\n\n"
        "- `weight` must be **> 0**\n"
        "- `access_cost` must be **≥ 0**\n"
        "- `destination_x` / `destination_y` define the point on the routing map\n\n"
        "The package becomes immediately available for route calculation."
    ),
    responses={
        201: {"description": "Package created successfully"},
        422: {"description": "Validation error — invalid field values"},
    },
)
def create_package(data: PackageCreate, service: PackageService = Depends(get_service)):
    return service.create_package(data)


@router.patch(
    "/{package_id}",
    response_model=PackageResponse,
    summary="Partially update a package",
    description=(
        "Updates one or more fields of an existing package. "
        "Only the fields present in the request body are modified — "
        "omitted fields retain their current values.\n\n"
        "Returns `404` if the package does not exist."
    ),
    responses={
        200: {"description": "Package updated successfully"},
        404: _404,
        422: {"description": "Validation error — invalid field values"},
    },
)
def update_package(package_id: UUID, data: PackageUpdate, service: PackageService = Depends(get_service)):
    package = service.update_package(package_id, data)
    if not package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    return package


@router.delete(
    "/{package_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a package",
    description=(
        "Permanently removes a package by its UUID.\n\n"
        "Returns `204 No Content` on success. "
        "Returns `404` if the package does not exist."
    ),
    responses={
        204: {"description": "Package deleted successfully"},
        404: _404,
    },
)
def delete_package(package_id: UUID, service: PackageService = Depends(get_service)):
    if not service.delete_package(package_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
