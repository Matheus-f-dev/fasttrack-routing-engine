import asyncio
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.algorithms.base import RouteStrategy, VehicleCapacityExceededError
from app.algorithms.models import RouteInput, RouteResult
from app.algorithms.registry import RouteStrategyRegistry, StrategyNotFoundError
from app.models.package import Package
from app.models.vehicle import Vehicle
from app.repositories.hub_repository import HubRepository
from app.repositories.package_repository import PackageRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.route import (
    AllRoutesResponse,
    DeliveryStop,
    RouteRequest,
    RouteResponse,
    VisitedHubResponse,
)
from app.services.route_comparison import RouteComparisonService

router = APIRouter(prefix="/routes", tags=["routes"])

_hub_repo = HubRepository()
_package_repo = PackageRepository()
_vehicle_repo = VehicleRepository()
_registry = RouteStrategyRegistry()
_executor = ThreadPoolExecutor()
_comparison_service = RouteComparisonService()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_vehicle(vehicle_id: UUID) -> Vehicle:
    vehicle = _vehicle_repo.get_by_id(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle


def _resolve_packages(package_ids: list[UUID]) -> list[Package]:
    packages = []
    for pid in package_ids:
        pkg = _package_repo.get_by_id(pid)
        if not pkg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Package {pid} not found")
        packages.append(pkg)
    return packages


def _build_route_input(vehicle: Vehicle, packages: list[Package]) -> RouteInput:
    return RouteInput(
        packages=packages,
        vehicle=vehicle,
        origin=_hub_repo.get_main(),
        available_hubs=_hub_repo.get_all(),
    )


def _build_response(result: RouteResult) -> RouteResponse:
    return RouteResponse(
        route_type=result.strategy_name,
        total_distance=result.total_distance,
        total_cost=result.total_cost,
        delivery_order=[
            DeliveryStop(
                sequence=stop.sequence,
                package_id=stop.packages[0].id,
                recipient_name=stop.packages[0].recipient_name,
                destination_x=stop.packages[0].destination_x,
                destination_y=stop.packages[0].destination_y,
            )
            for stop in result.stops
        ],
        extra_package_collected=result.extra_package_collected,
        visited_hub=VisitedHubResponse(
            id=result.visited_hub.id,
            name=result.visited_hub.name,
            x=result.visited_hub.x,
            y=result.visited_hub.y,
        ) if result.visited_hub else None,
    )


def _run_strategy(strategy: RouteStrategy, route_input: RouteInput) -> RouteResult:
    return strategy.calculate_route(route_input)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/calculate",
    response_model=RouteResponse,
    summary="Calculate a route with a single strategy",
    description=(
        "Calculates a delivery route using the strategy selected via the `strategy` query parameter.\n\n"
        "Available strategies:\n\n"
        "- **express** — nearest-neighbor greedy; minimizes total distance, ignores `access_cost`\n"
        "- **economic** — weighted nearest-neighbor; minimizes `distance + access_cost` per step\n"
        "- **strategic_hub** — hub-cluster; detours through the nearest secondary hub to group "
        "regional packages; respects `max_weight`\n\n"
        "Returns `400` if total package weight exceeds vehicle capacity.\n\n"
        "Returns `404` if vehicle or any package is not found.\n\n"
        "Returns `422` if the strategy name is not recognised."
    ),
)
def calculate_route(
    body: RouteRequest,
    strategy: str = Query(
        default="express",
        description="Routing strategy name. One of: `express`, `economic`, `strategic_hub`.",
        examples=["express"],
    ),
) -> RouteResponse:
    vehicle = _resolve_vehicle(body.vehicle_id)
    packages = _resolve_packages(body.package_ids)

    try:
        route_strategy = _registry.get(strategy)
    except StrategyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    try:
        result = route_strategy.calculate_route(_build_route_input(vehicle, packages))
    except VehicleCapacityExceededError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _build_response(result)


@router.post(
    "/calculate/all",
    response_model=AllRoutesResponse,
    summary="Calculate routes with all strategies simultaneously",
    description=(
        "Runs **all three routing strategies in parallel** for the same vehicle and package list, "
        "returning one route per strategy in a single response.\n\n"
        "This allows the caller to compare strategies and pick the most suitable route.\n\n"
        "| Field | Strategy | Optimises for |\n"
        "|---|---|---|\n"
        "| `express_route` | ExpressRouteStrategy | Minimum total distance |\n"
        "| `economic_route` | EconomicRouteStrategy | Minimum distance + access cost |\n"
        "| `strategic_route` | StrategicHubRouteStrategy | Regional hub consolidation |\n\n"
        "Returns `400` if total package weight exceeds vehicle `max_weight`.\n\n"
        "Returns `404` if the vehicle or any package ID is not found."
    ),
    responses={
        400: {"description": "Total package weight exceeds vehicle capacity"},
        404: {"description": "Vehicle or package not found"},
    },
)
async def calculate_all_routes(body: RouteRequest) -> AllRoutesResponse:
    vehicle = _resolve_vehicle(body.vehicle_id)
    packages = _resolve_packages(body.package_ids)
    route_input = _build_route_input(vehicle, packages)

    loop = asyncio.get_event_loop()
    strategies = {
        "express":       _registry.get("express"),
        "economic":      _registry.get("economic"),
        "strategic_hub": _registry.get("strategic_hub"),
    }

    try:
        express_result, economic_result, strategic_result = await asyncio.gather(
            loop.run_in_executor(_executor, _run_strategy, strategies["express"],       route_input),
            loop.run_in_executor(_executor, _run_strategy, strategies["economic"],      route_input),
            loop.run_in_executor(_executor, _run_strategy, strategies["strategic_hub"], route_input),
        )
    except VehicleCapacityExceededError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return AllRoutesResponse(
        express_route=_build_response(express_result),
        economic_route=_build_response(economic_result),
        strategic_route=_build_response(strategic_result),
        comparison=_comparison_service.compare(
            express=_build_response(express_result),
            economic=_build_response(economic_result),
            strategic=_build_response(strategic_result),
        ),
    )
