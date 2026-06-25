from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.algorithms.registry import RouteStrategyRegistry, StrategyNotFoundError
from app.repositories.hub_repository import HubRepository
from app.repositories.package_repository import PackageRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.algorithms.models import RouteInput
from app.schemas.route import DeliveryStop, RouteRequest, RouteResponse

router = APIRouter(prefix="/routes", tags=["routes"])

_hub_repo = HubRepository()
_package_repo = PackageRepository()
_vehicle_repo = VehicleRepository()
_registry = RouteStrategyRegistry()


@router.post(
    "/calculate",
    response_model=RouteResponse,
    summary="Calculate a delivery route",
    description=(
        "Calculates an optimized delivery route for the given packages and vehicle. "
        "Use the `strategy` query parameter to select the routing algorithm:\n\n"
        "- **express** — nearest-neighbor greedy, minimizes total distance, ignores access cost\n"
        "- **economic** — *(not yet implemented)*\n"
        "- **strategic_hub** — *(not yet implemented)*"
    ),
)
def calculate_route(
    body: RouteRequest,
    strategy: str = Query(default="express", description="Routing strategy", examples=["express"]),
) -> RouteResponse:
    vehicle = _vehicle_repo.get_by_id(body.vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    packages = []
    for pid in body.package_ids:
        pkg = _package_repo.get_by_id(pid)
        if not pkg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Package {pid} not found")
        packages.append(pkg)

    try:
        route_strategy = _registry.get(strategy)
    except StrategyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    route_input = RouteInput(
        packages=packages,
        vehicle=vehicle,
        origin=_hub_repo.get_main(),
        available_hubs=_hub_repo.get_all(),
    )

    result = route_strategy.calculate_route(route_input)

    delivery_order = [
        DeliveryStop(
            sequence=stop.sequence,
            package_id=stop.packages[0].id,
            recipient_name=stop.packages[0].recipient_name,
            destination_x=stop.packages[0].destination_x,
            destination_y=stop.packages[0].destination_y,
        )
        for stop in result.stops
    ]

    return RouteResponse(
        route_type=result.strategy_name,
        total_distance=result.total_distance,
        delivery_order=delivery_order,
    )
