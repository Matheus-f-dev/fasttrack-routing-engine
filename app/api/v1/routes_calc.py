from fastapi import APIRouter, HTTPException, Query, status
from app.algorithms.base import VehicleCapacityExceededError
from app.algorithms.registry import RouteStrategyRegistry, StrategyNotFoundError
from app.repositories.hub_repository import HubRepository
from app.repositories.package_repository import PackageRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.algorithms.models import RouteInput
from app.schemas.route import DeliveryStop, RouteRequest, RouteResponse, VisitedHubResponse

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
        "- **economic** — weighted nearest-neighbor, minimizes distance + access_cost per step; may travel further to avoid expensive stops\n"
        "- **strategic_hub** — routes through the nearest secondary hub to collect an extra regional package; respects vehicle max_weight"
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

    try:
        result = route_strategy.calculate_route(route_input)
    except VehicleCapacityExceededError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

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
        total_cost=result.total_cost,
        delivery_order=delivery_order,
        extra_package_collected=result.extra_package_collected,
        visited_hub=VisitedHubResponse(
            id=result.visited_hub.id,
            name=result.visited_hub.name,
            x=result.visited_hub.x,
            y=result.visited_hub.y,
        ) if result.visited_hub else None,
    )
